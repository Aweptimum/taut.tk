from __future__ import annotations

import argparse
import gc
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass

from bench_overhead import FakeTk
from bench_overhead import FakeWidget
from bench_overhead import patch_fake_tk
from reaktiv import batch

from solid_tk import reactive
from solid_tk import runtime
from solid_tk import widgets

Updater = Callable[[int], None]
Disposer = Callable[[], None]
Setup = Callable[[int], tuple[Updater, Disposer]]


@dataclass(frozen=True)
class Case:
    name: str
    setup: Setup
    affected_widgets: Callable[[int], int]
    baseline: str | None = None


def dispose_fake(root: FakeTk) -> None:
    root.dispose()


def raw_one_label(_count: int) -> tuple[Updater, Disposer]:
    root = FakeTk(title="Bench")
    label = FakeWidget(root, text="Value 0")
    label.pack()

    def update(value: int) -> None:
        label.configure(text=f"Value {value}")

    return update, lambda: dispose_fake(root)


def solid_one_label(_count: int) -> tuple[Updater, Disposer]:
    value, set_value = reactive.create_signal(0)
    mount = runtime.create_root(
        lambda: widgets.Label(text=lambda: f"Value {value()}"),
        title="Bench",
    )

    return set_value, mount.dispose


def raw_fanout(count: int) -> tuple[Updater, Disposer]:
    root = FakeTk(title="Bench")
    frame = FakeWidget(root)
    frame.pack()
    labels = [FakeWidget(frame, text=f"Value 0 {index}") for index in range(count)]
    for label in labels:
        label.pack()

    def update(value: int) -> None:
        for index, label in enumerate(labels):
            label.configure(text=f"Value {value} {index}")

    return update, lambda: dispose_fake(root)


def solid_fanout(count: int) -> tuple[Updater, Disposer]:
    value, set_value = reactive.create_signal(0)
    mount = runtime.create_root(
        lambda: widgets.VStack(
            *(
                widgets.Label(text=lambda index=index: f"Value {value()} {index}")
                for index in range(count)
            )
        ),
        title="Bench",
    )

    return set_value, mount.dispose


def raw_update_one_of_many(count: int) -> tuple[Updater, Disposer]:
    root = FakeTk(title="Bench")
    frame = FakeWidget(root)
    frame.pack()
    labels = [FakeWidget(frame, text=f"Value 0 {index}") for index in range(count)]
    for label in labels:
        label.pack()

    def update(value: int) -> None:
        index = value % count
        labels[index].configure(text=f"Value {value} {index}")

    return update, lambda: dispose_fake(root)


def solid_update_one_of_many(count: int) -> tuple[Updater, Disposer]:
    signals = [reactive.create_signal(0) for _ in range(count)]
    accessors = [accessor for accessor, _set_accessor in signals]
    mutators = [set_accessor for _accessor, set_accessor in signals]
    mount = runtime.create_root(
        lambda: widgets.VStack(
            *(
                widgets.Label(
                    text=lambda index=index: f"Value {accessors[index]()} {index}"
                )
                for index in range(count)
            )
        ),
        title="Bench",
    )

    def update(value: int) -> None:
        mutators[value % count](value)

    return update, mount.dispose


def raw_update_all(count: int) -> tuple[Updater, Disposer]:
    root = FakeTk(title="Bench")
    frame = FakeWidget(root)
    frame.pack()
    labels = [FakeWidget(frame, text=f"Value 0 {index}") for index in range(count)]
    for label in labels:
        label.pack()

    def update(value: int) -> None:
        for index, label in enumerate(labels):
            label.configure(text=f"Value {value} {index}")

    return update, lambda: dispose_fake(root)


def solid_update_all(count: int) -> tuple[Updater, Disposer]:
    signals = [reactive.create_signal(0) for _ in range(count)]
    accessors = [accessor for accessor, _set_accessor in signals]
    mutators = [set_accessor for _accessor, set_accessor in signals]
    mount = runtime.create_root(
        lambda: widgets.VStack(
            *(
                widgets.Label(
                    text=lambda index=index: f"Value {accessors[index]()} {index}"
                )
                for index in range(count)
            )
        ),
        title="Bench",
    )

    def update(value: int) -> None:
        for mutate in mutators:
            mutate(value)

    return update, mount.dispose


def solid_update_all_batched(count: int) -> tuple[Updater, Disposer]:
    update_all, dispose = solid_update_all(count)

    def update(value: int) -> None:
        with batch():
            update_all(value)

    return update, dispose


def time_updates(update: Updater, iterations: int) -> float:
    started = time.perf_counter()
    for value in range(1, iterations + 1):
        update(value)
    return time.perf_counter() - started


def sample_case(
    case: Case,
    *,
    widgets_per_app: int,
    iterations: int,
    repeats: int,
    warmups: int,
) -> list[float]:
    samples: list[float] = []
    for sample in range(repeats + warmups):
        update, dispose = case.setup(widgets_per_app)
        try:
            if sample < warmups:
                time_updates(update, max(1, iterations // 10))
                continue

            was_enabled = gc.isenabled()
            gc.disable()
            try:
                samples.append(time_updates(update, iterations))
            finally:
                if was_enabled:
                    gc.enable()
        finally:
            dispose()
    return samples


def format_us(seconds: float) -> str:
    return f"{seconds * 1_000_000:,.1f}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark solid-tk update propagation against raw Tk-style updates."
    )
    parser.add_argument("--widgets", type=int, default=100, help="labels in multi-widget cases")
    parser.add_argument("--iterations", type=int, default=1_000, help="state updates per sample")
    parser.add_argument("--repeats", type=int, default=7, help="timed samples per scenario")
    parser.add_argument("--warmups", type=int, default=2, help="untimed warmup samples")
    args = parser.parse_args()

    patch_fake_tk()
    cases = [
        Case("raw one label", raw_one_label, lambda _count: 1),
        Case("solid one label", solid_one_label, lambda _count: 1, "raw one label"),
        Case("raw fanout", raw_fanout, lambda count: count),
        Case("solid fanout", solid_fanout, lambda count: count, "raw fanout"),
        Case("raw one of many", raw_update_one_of_many, lambda _count: 1),
        Case(
            "solid one of many",
            solid_update_one_of_many,
            lambda _count: 1,
            "raw one of many",
        ),
        Case("raw all independent", raw_update_all, lambda count: count),
        Case(
            "solid all independent",
            solid_update_all,
            lambda count: count,
            "raw all independent",
        ),
        Case(
            "solid all batched",
            solid_update_all_batched,
            lambda count: count,
            "raw all independent",
        ),
    ]

    print(
        f"fake Tk backend: {args.widgets} labels, "
        f"{args.iterations} updates/sample, {args.repeats} samples"
    )
    print()
    print(
        f"{'case':<24} {'median/sample':>15} "
        f"{'per update':>14} {'per widget':>14}"
    )
    print("-" * 73)

    results: dict[str, float] = {}
    for case in cases:
        samples = sample_case(
            case,
            widgets_per_app=args.widgets,
            iterations=args.iterations,
            repeats=args.repeats,
            warmups=args.warmups,
        )
        median = statistics.median(samples)
        results[case.name] = median
        per_update = median / args.iterations
        affected = max(case.affected_widgets(args.widgets), 1)
        per_widget = per_update / affected
        print(
            f"{case.name:<24} {format_us(median):>15} "
            f"{format_us(per_update):>14} {format_us(per_widget):>14}"
        )

    print()
    for case in cases:
        if case.baseline is None:
            continue
        raw = results[case.baseline]
        solid = results[case.name]
        affected = max(case.affected_widgets(args.widgets), 1)
        extra = (solid - raw) / args.iterations / affected
        ratio = solid / raw if raw else float("inf")
        print(f"{case.name} overhead: {ratio:.2f}x raw, +{format_us(extra)} us/widget")


if __name__ == "__main__":
    main()
