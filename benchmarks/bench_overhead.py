from __future__ import annotations

import argparse
import gc
import statistics
import time
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

from solid_tk import component
from solid_tk import layout
from solid_tk import nodes
from solid_tk import reactive
from solid_tk import runtime
from solid_tk import tk


class FakeStringVar:
    def __init__(self, master: FakeWidget | None = None) -> None:
        self.master = master
        self.value = ""
        self.traces: dict[str, Callable[..., Any]] = {}
        self.next_id = 0

    def get(self) -> str:
        return self.value

    def set(self, value: str) -> None:
        self.value = value
        for callback in list(self.traces.values()):
            callback("name", "index", "write")

    def trace_add(self, mode: str, callback: Callable[..., Any]) -> str:
        self.next_id += 1
        trace_id = f"trace-{self.next_id}"
        self.traces[trace_id] = callback
        return trace_id

    def trace_remove(self, mode: str, trace_id: str) -> None:
        self.traces.pop(trace_id, None)


class FakeWidget:
    def __init__(self, parent: FakeWidget | None = None, **props: Any) -> None:
        self.parent = parent
        self.props = dict(props)
        self.children: list[FakeWidget] = []
        self.destroyed = False
        self.after_callbacks: dict[str, tuple[int, Callable[[], Any]]] = {}
        self.after_cancelled: list[str] = []
        self.next_after_id = 0
        if parent is not None:
            parent.children.append(self)

    def configure(self, **props: Any) -> None:
        self.props.update(props)

    def pack(self, **kwargs: Any) -> None:
        self.pack_kwargs = kwargs

    def grid(self, **kwargs: Any) -> None:
        self.grid_kwargs = kwargs

    def place(self, **kwargs: Any) -> None:
        self.place_kwargs = kwargs

    def destroy(self) -> None:
        for child in self.children:
            child.destroy()
        self.destroyed = True

    def title(self, value: str) -> None:
        self.props["title"] = value

    def quit(self) -> None:
        self.quit_called = True

    def after(self, ms: int, callback: Callable[[], Any]) -> str:
        self.next_after_id += 1
        after_id = f"after-{self.next_after_id}"
        self.after_callbacks[after_id] = (ms, callback)
        return after_id

    def after_cancel(self, after_id: str) -> None:
        self.after_cancelled.append(after_id)
        self.after_callbacks.pop(after_id, None)


class FakeTk(FakeWidget):
    def __init__(self, **props: Any) -> None:
        super().__init__(None, **props)

    def dispose(self) -> None:
        self.quit()
        self.destroy()


def patch_fake_tk() -> None:
    fake_tk = SimpleNamespace(
        Button=FakeWidget,
        Checkbutton=FakeWidget,
        Entry=FakeWidget,
        Frame=FakeWidget,
        Label=FakeWidget,
        StringVar=FakeStringVar,
        Tk=FakeTk,
    )
    tk.tk = fake_tk
    layout.tk = fake_tk
    nodes.tk = fake_tk


def raw_static(count: int) -> FakeTk:
    root = FakeTk(title="Bench")
    frame = FakeWidget(root, padx=12, pady=12)
    frame.pack()
    for index in range(count):
        label = FakeWidget(frame, text=f"Item {index}")
        label.pack(side="top", fill="x", anchor="w")
    return root


def solid_static(count: int) -> runtime.Mount:
    return runtime.create_root(
        lambda: layout.VStack(
            *(tk.Label(text=f"Item {index}") for index in range(count)),
            padx=12,
            pady=12,
        ),
        title="Bench",
    )


def solid_reactive(count: int) -> runtime.Mount:
    current, _set_current = reactive.create_signal("Item")
    return runtime.create_root(
        lambda: layout.VStack(
            *(
                tk.Label(text=lambda index=index: f"{current()} {index}")
                for index in range(count)
            ),
            padx=12,
            pady=12,
        ),
        title="Bench",
    )


@component
def LabelList(props: Any) -> tk.WidgetNode:
    return layout.VStack(
        *(tk.Label(text=f"{props.prefix()} {index}") for index in range(props.count())),
        padx=12,
        pady=12,
    )


def solid_component(count: int) -> runtime.Mount:
    return runtime.create_root(lambda: LabelList(prefix="Item", count=count), title="Bench")


def time_case(fn: Callable[[int], Any], count: int, iterations: int) -> float:
    started = time.perf_counter()
    for _ in range(iterations):
        mount = fn(count)
        if hasattr(mount, "dispose"):
            mount.dispose()
    return time.perf_counter() - started


def sample_case(
    fn: Callable[[int], Any],
    *,
    count: int,
    iterations: int,
    repeats: int,
    warmups: int,
) -> list[float]:
    for _ in range(warmups):
        time_case(fn, count, max(1, iterations // 10))

    was_enabled = gc.isenabled()
    gc.disable()
    try:
        return [time_case(fn, count, iterations) for _ in range(repeats)]
    finally:
        if was_enabled:
            gc.enable()


def format_us(seconds: float) -> str:
    return f"{seconds * 1_000_000:,.1f}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark solid-tk mounting overhead against raw Tk-style widget creation."
    )
    parser.add_argument("--widgets", type=int, default=100, help="labels per app mount")
    parser.add_argument("--iterations", type=int, default=100, help="app mounts per sample")
    parser.add_argument("--repeats", type=int, default=5, help="timed samples per scenario")
    parser.add_argument("--warmups", type=int, default=2, help="untimed warmup samples")
    args = parser.parse_args()

    patch_fake_tk()
    cases: list[tuple[str, Callable[[int], Any]]] = [
        ("raw static", raw_static),
        ("solid static", solid_static),
        ("solid reactive props", solid_reactive),
        ("solid component", solid_component),
    ]

    results: dict[str, float] = {}
    print(
        f"fake Tk backend: {args.widgets} labels, "
        f"{args.iterations} mounts/sample, {args.repeats} samples"
    )
    print()
    print(f"{'case':<22} {'median/sample':>15} {'per mount':>14} {'per widget':>14}")
    print("-" * 69)
    for name, fn in cases:
        samples = sample_case(
            fn,
            count=args.widgets,
            iterations=args.iterations,
            repeats=args.repeats,
            warmups=args.warmups,
        )
        median = statistics.median(samples)
        results[name] = median
        per_mount = median / args.iterations
        per_widget = per_mount / max(args.widgets, 1)
        print(
            f"{name:<22} {format_us(median):>15} "
            f"{format_us(per_mount):>14} {format_us(per_widget):>14}"
        )

    raw = results["raw static"]
    print()
    for name in ("solid static", "solid reactive props", "solid component"):
        extra = (results[name] - raw) / args.iterations / max(args.widgets, 1)
        ratio = results[name] / raw if raw else float("inf")
        print(f"{name} overhead: {ratio:.2f}x raw, +{format_us(extra)} us/widget")


if __name__ == "__main__":
    main()
