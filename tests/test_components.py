from __future__ import annotations

import json
import os
from pathlib import Path
from textwrap import dedent
from typing import Protocol
from typing import cast

import pyright

from solid_tk import Component
from solid_tk import component
from solid_tk import reactive
from solid_tk import runtime
from solid_tk import widgets


def test_function_component_keeps_local_reactive_state_alive():
    @component
    def Counter(props):
        count, set_count = reactive.create_signal(0)
        return widgets.VStack(
            widgets.Label(text=lambda: f"{props.title()}: {count()}"),
            widgets.Button(
                text="Increment", command=lambda: set_count(lambda n: n + 1)
            ),
        )

    mount = runtime.create_root(lambda: Counter(title="Count"), title="Demo")
    frame = mount.widget.children[0]
    label = frame.children[0]
    button = frame.children[1]

    assert label.props["text"] == "Count: 0"

    button.props["command"]()

    assert label.props["text"] == "Count: 1"


def test_create_memo_derives_reactive_values():
    count, set_count = reactive.create_signal(1)

    @component
    def Counter(props):
        doubled = reactive.create_memo(lambda: count() * 2)
        return widgets.Label(text=lambda: f"Double: {doubled()}")

    mount = runtime.create_root(Counter, title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "Double: 2"

    set_count(3)

    assert label.props["text"] == "Double: 6"


def test_function_component_lifecycle_helpers_are_owned():
    value, set_value = reactive.create_signal("hello")
    events = []

    @component
    def Tracker(props):
        runtime.create_effect(lambda: events.append(f"effect:{props.value()}"))
        runtime.on_mount(lambda: events.append("mount"))
        runtime.on_cleanup(lambda: events.append("cleanup"))
        return widgets.Label(text=props.value)

    mount = runtime.create_root(lambda: Tracker(value=value), title="Demo")

    assert events == ["effect:hello", "mount"]

    set_value("world")

    assert events == ["effect:hello", "mount", "effect:world"]

    mount.dispose()
    set_value("again")

    assert events == ["effect:hello", "mount", "effect:world", "cleanup"]


def test_function_component_props_can_be_typed_with_protocol():
    class CounterProps(Protocol):
        title: reactive.Accessor[str]
        initial: reactive.Accessor[int]

    @component
    def Counter(props: CounterProps):
        count, _set_count = reactive.create_signal(props.initial())
        return widgets.Label(text=lambda: f"{props.title()}: {count()}")

    mount = runtime.create_root(lambda: Counter(title="Count", initial=2), title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "Count: 2"


def test_function_component_receives_signal_mutator_prop_directly():
    class CounterProps(Protocol):
        count: reactive.Accessor[int]
        set_count: reactive.Mutator[int]

    @component
    def Counter(props: CounterProps):
        return widgets.Button(
            text=lambda: f"Count: {props.count()}",
            command=lambda: props.set_count(lambda n: n + 1),
        )

    count, set_count = reactive.create_signal(0)
    mount = runtime.create_root(
        lambda: Counter(count=count, set_count=set_count),
        title="Demo",
    )
    button = mount.widget.children[0]

    assert button.props["text"] == "Count: 0"

    button.props["command"]()

    assert count() == 1
    assert button.props["text"] == "Count: 1"


def test_class_component_can_initialize_state_with_init():
    class Counter(Component):
        def __init__(self) -> None:
            self.count, self.set_count = reactive.create_signal(1)

        def render(self):
            return widgets.Label(text=lambda: f"{self.props.title()}: {self.count()}")

    mount = runtime.create_root(lambda: Counter(title="Count"), title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "Count: 1"


def test_class_component_init_can_receive_typed_props():
    class CounterProps(Protocol):
        title: reactive.Accessor[str]
        initial: reactive.Accessor[int]

    class Counter(Component):
        def __init__(self, props: CounterProps) -> None:
            self.title = props.title
            self.count, self.set_count = reactive.create_signal(props.initial())

        def render(self):
            return widgets.Label(text=lambda: f"{self.title()}: {self.count()}")

    mount = runtime.create_root(lambda: Counter(title="Count", initial=3), title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "Count: 3"


def test_class_component_generic_types_self_props(tmp_path: Path):
    sample = tmp_path / "component_generic.py"
    sample.write_text(
        dedent(
            """
            from __future__ import annotations

            from typing import Protocol

            from solid_tk import Component
            from solid_tk import reactive
            from solid_tk import widgets


            class CounterProps(Protocol):
                title: reactive.Accessor[str]
                initial: reactive.Accessor[int]


            class Counter(Component[CounterProps]):
                def render(self):
                    reveal_type(self.props.title)
                    self.props.missing
                    return widgets.Label(text=lambda: self.props.title())
            """
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}

    result = pyright.run(
        "--outputjson",
        str(sample),
        check=False,
        cwd=Path.cwd(),
        env=env,
        text=True,
        capture_output=True,
    )

    stdout = cast(str, result.stdout)
    stderr = cast(str, result.stderr)

    assert result.returncode == 1, stdout + stderr
    output = json.loads(stdout)
    messages = [diagnostic["message"] for diagnostic in output["generalDiagnostics"]]

    assert any(
        'Type of "self.props.title" is "Accessor[str]"' in msg for msg in messages
    )
    assert any(
        'Cannot access attribute "missing" for class "CounterProps"' in msg
        for msg in messages
    )
