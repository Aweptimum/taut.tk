from __future__ import annotations

import pytest
from fakes import FakeStringVar

from solid_tk import component
from solid_tk import reactive
from solid_tk import runtime
from solid_tk import widgets


def test_entry_value_tracks_signal_changes_when_created_inside_root():
    value, set_value = reactive.create_signal("hello")

    mount = runtime.create_root(lambda: widgets.VStack(widgets.Entry(value=value)), title="Demo")
    entry = mount.widget.children[0].children[0]
    variable = entry.props["textvariable"]

    assert variable.get() == "hello"

    set_value("world")

    assert variable.get() == "world"


def test_entry_value_writes_user_changes_back_to_signal():
    value, set_value = reactive.create_signal("hello")

    mount = runtime.create_root(
        lambda: widgets.VStack(widgets.Entry(value=value, on_input=set_value)),
        title="Demo",
    )
    entry = mount.widget.children[0].children[0]
    variable = entry.props["textvariable"]

    variable.set("typed")

    assert value() == "typed"


def test_entry_value_conflicts_with_textvariable():
    value, _set_value = reactive.create_signal("hello")

    with pytest.raises(ValueError, match="value and textvariable"):
        runtime.create_root(
            lambda: widgets.Entry(value=value, textvariable=FakeStringVar()),
            title="Demo",
        )


def test_create_root_disposes_mounted_app_node():
    value, _set_value = reactive.create_signal("hello")
    mount = runtime.create_root(lambda: widgets.VStack(widgets.Entry(value=value)), title="Demo")
    app_frame = mount.widget.children[0]

    mount.dispose()

    assert app_frame.destroyed


def test_widget_binding_unwraps_forwarded_callable_prop_value():
    count, set_count = reactive.create_signal(0)

    @component
    def ForwardedLabel(props):
        return widgets.Label(text=props.text)

    mount = runtime.create_root(
        lambda: ForwardedLabel(text=lambda: f"Count: {count()}"),
        title="Demo",
    )
    label = mount.widget.children[0]

    assert label.props["text"] == "Count: 0"

    set_count(1)

    assert label.props["text"] == "Count: 1"
