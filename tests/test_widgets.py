from __future__ import annotations

from types import SimpleNamespace
from typing import Optional
from typing import Protocol

import pytest
from reaktiv import Signal

from solid_tk import Accessor
from solid_tk import Button
from solid_tk import Component
from solid_tk import Entry
from solid_tk import Label
from solid_tk import Provider
from solid_tk import VStack
from solid_tk import component
from solid_tk import create_context
from solid_tk import create_effect
from solid_tk import create_memo
from solid_tk import create_root
from solid_tk import on_cleanup
from solid_tk import on_mount
from solid_tk import use_context
from solid_tk import widgets


class FakeStringVar:
    def __init__(self, master=None):
        self.master = master
        self.value = ""
        self.traces = {}
        self.next_id = 0

    def get(self):
        return self.value

    def set(self, value):
        self.value = value
        for callback in list(self.traces.values()):
            callback("name", "index", "write")

    def trace_add(self, mode, callback):
        self.next_id += 1
        trace_id = f"trace-{self.next_id}"
        self.traces[trace_id] = callback
        return trace_id

    def trace_remove(self, mode, trace_id):
        self.traces.pop(trace_id, None)


class FakeWidget:
    def __init__(self, parent: Optional[FakeWidget] = None, **props):
        self.parent = parent
        self.props = dict(props)
        self.children = []
        self.destroyed = False
        if parent is not None:
            parent.children.append(self)

    def configure(self, **props):
        self.props.update(props)

    def pack(self, **kwargs):
        self.pack_kwargs = kwargs

    def grid(self, **kwargs):
        self.grid_kwargs = kwargs

    def place(self, **kwargs):
        self.place_kwargs = kwargs

    def pack_forget(self):
        pass

    def destroy(self):
        self.destroyed = True

    def title(self, value):
        self.props["title"] = value

    def quit(self):
        self.quit_called = True


class FakeTk(FakeWidget):
    def __init__(self, **props):
        super().__init__(None, **props)


@pytest.fixture(autouse=True)
def fake_tk(monkeypatch):
    monkeypatch.setattr(
        widgets,
        "tk",
        SimpleNamespace(
            Button=FakeWidget,
            Checkbutton=FakeWidget,
            Entry=FakeWidget,
            Frame=FakeWidget,
            Label=FakeWidget,
            StringVar=FakeStringVar,
            Tk=FakeTk,
        ),
    )


def test_entry_value_tracks_signal_changes_when_created_inside_root():
    value = Signal("hello")

    mount = create_root(lambda: VStack(Entry(value=value)), title="Demo")
    entry = mount.widget.children[0].children[0]
    variable = entry.props["textvariable"]

    assert variable.get() == "hello"

    value.set("world")

    assert variable.get() == "world"


def test_entry_value_writes_user_changes_back_to_signal():
    value = Signal("hello")

    mount = create_root(lambda: VStack(Entry(value=value)), title="Demo")
    entry = mount.widget.children[0].children[0]
    variable = entry.props["textvariable"]

    variable.set("typed")

    assert value() == "typed"


def test_entry_value_conflicts_with_textvariable():
    value = Signal("hello")

    with pytest.raises(ValueError, match="value and textvariable"):
        create_root(
            lambda: Entry(value=value, textvariable=FakeStringVar()),
            title="Demo",
        )


def test_create_root_disposes_mounted_app_node():
    mount = create_root(lambda: VStack(Entry(value=Signal("hello"))), title="Demo")
    app_frame = mount.widget.children[0]

    mount.dispose()

    assert app_frame.destroyed


def test_function_component_keeps_local_reactive_state_alive():
    @component
    def Counter(props):
        count = Signal(0)
        return VStack(
            Label(text=lambda: f"{props.title()}: {count()}"),
            Button(text="Increment", command=lambda: count.set(count() + 1)),
        )

    mount = create_root(lambda: Counter(title="Count"), title="Demo")
    frame = mount.widget.children[0]
    label = frame.children[0]
    button = frame.children[1]

    assert label.props["text"] == "Count: 0"

    button.props["command"]()

    assert label.props["text"] == "Count: 1"


def test_widget_binding_unwraps_forwarded_callable_prop_value():
    count = Signal(0)

    @component
    def ForwardedLabel(props):
        return Label(text=props.text)

    mount = create_root(
        lambda: ForwardedLabel(text=lambda: f"Count: {count()}"),
        title="Demo",
    )
    label = mount.widget.children[0]

    assert label.props["text"] == "Count: 0"

    count.set(1)

    assert label.props["text"] == "Count: 1"


def test_create_memo_derives_reactive_values():
    count = Signal(1)

    @component
    def Counter(props):
        doubled = create_memo(lambda: count() * 2)
        return Label(text=lambda: f"Double: {doubled()}")

    mount = create_root(Counter, title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "Double: 2"

    count.set(3)

    assert label.props["text"] == "Double: 6"


def test_function_component_lifecycle_helpers_are_owned():
    value = Signal("hello")
    events = []

    @component
    def Tracker(props):
        create_effect(lambda: events.append(f"effect:{props.value()}"))
        on_mount(lambda: events.append("mount"))
        on_cleanup(lambda: events.append("cleanup"))
        return Label(text=props.value)

    mount = create_root(lambda: Tracker(value=value), title="Demo")

    assert events == ["effect:hello", "mount"]

    value.set("world")

    assert events == ["effect:hello", "mount", "effect:world"]

    mount.dispose()
    value.set("again")

    assert events == ["effect:hello", "mount", "effect:world", "cleanup"]


def test_root_callback_lifecycle_helpers_are_owned():
    events = []

    def App():
        on_mount(lambda: events.append("mount"))
        on_cleanup(lambda: events.append("cleanup"))
        return Label(text="Root")

    mount = create_root(App, title="Demo")

    assert events == ["mount"]

    mount.dispose()

    assert events == ["mount", "cleanup"]


def test_context_reads_default_value():
    theme = create_context("light")

    @component
    def ThemedLabel(props):
        return Label(text=use_context(theme))

    mount = create_root(lambda: ThemedLabel(), title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "light"


def test_provider_supplies_context_to_callable_child():
    theme = create_context("light")

    @component
    def ThemedLabel(props):
        return Label(text=use_context(theme))

    mount = create_root(
        lambda: Provider(theme, "dark", lambda: ThemedLabel()),
        title="Demo",
    )
    label = mount.widget.children[0]

    assert label.props["text"] == "dark"


def test_provider_accepts_forwarded_component_children():
    theme = create_context("light")

    @component
    def ThemeProvider(props):
        return Provider(theme, "dark", props.children)

    @component
    def ThemedLabel(props):
        return Label(text=use_context(theme))

    mount = create_root(
        lambda: ThemeProvider(children=lambda: ThemedLabel()),
        title="Demo",
    )
    label = mount.widget.children[0]

    assert label.props["text"] == "dark"


def test_nested_provider_uses_nearest_context_value():
    theme = create_context("light")

    @component
    def ThemedLabel(props):
        return Label(text=use_context(theme))

    mount = create_root(
        lambda: Provider(
            theme,
            "outer",
            lambda: Provider(theme, "inner", lambda: ThemedLabel()),
        ),
        title="Demo",
    )
    label = mount.widget.children[0]

    assert label.props["text"] == "inner"


def test_function_component_props_can_be_typed_with_protocol():
    class CounterProps(Protocol):
        title: Accessor[str]
        initial: Accessor[int]

    @component
    def Counter(props: CounterProps):
        count = Signal(props.initial())
        return Label(text=lambda: f"{props.title()}: {count()}")

    mount = create_root(lambda: Counter(title="Count", initial=2), title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "Count: 2"


def test_class_component_can_initialize_state_with_init():
    class Counter(Component):
        def __init__(self) -> None:
            self.count = Signal(1)

        def render(self):
            return Label(text=lambda: f"{self.props.title()}: {self.count()}")

    mount = create_root(lambda: Counter(title="Count"), title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "Count: 1"


def test_class_component_init_can_receive_typed_props():
    class CounterProps(Protocol):
        title: Accessor[str]
        initial: Accessor[int]

    class Counter(Component):
        def __init__(self, props: CounterProps) -> None:
            self.title = props.title
            self.count = Signal(props.initial())

        def render(self):
            return Label(text=lambda: f"{self.title()}: {self.count()}")

    mount = create_root(lambda: Counter(title="Count", initial=3), title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "Count: 3"
