from __future__ import annotations

from typing import Any
from typing import cast

from solid_tk import component
from solid_tk import control
from solid_tk import reactive
from solid_tk import runtime
from solid_tk import widgets


def test_switch_renders_first_matching_case_and_fallback():
    mode, set_mode = reactive.create_signal("a")

    mount = runtime.create_root(
        lambda: control.Switch(
            control.Match(lambda: mode() == "a", lambda: widgets.Label(text="A")),
            control.Match(lambda: mode() == "b", lambda: widgets.Label(text="B")),
            fallback=lambda: widgets.Label(text="fallback"),
        ),
        title="Demo",
    )
    switch = mount.node.children[0]

    assert switch.active.widget.props["text"] == "A"

    set_mode("b")

    assert switch.active.widget.props["text"] == "B"

    set_mode("c")

    assert switch.active.widget.props["text"] == "fallback"


def test_switch_renders_initial_fallback_when_no_case_matches():
    mode, _set_mode = reactive.create_signal("idle")

    mount = runtime.create_root(
        lambda: control.Switch(
            control.Match(lambda: mode() == "ready", lambda: widgets.Label(text="Ready")),
            fallback=lambda: widgets.Label(text="Idle"),
        ),
        title="Demo",
    )
    switch = mount.node.children[0]

    assert switch.active.widget.props["text"] == "Idle"


def test_index_reuses_nodes_by_index_and_updates_item_accessors():
    items, set_items = reactive.create_signal(["a", "b"])

    mount = runtime.create_root(
        lambda: control.Index(
            items,
            lambda item, index: widgets.Label(text=lambda: f"{index}:{item()}"),
        ),
        title="Demo",
    )
    index_node = mount.node.children[0]
    first = index_node.instances[0]

    assert first.widget.props["text"] == "0:a"
    assert index_node.instances[1].widget.props["text"] == "1:b"

    set_items(["x", "y", "z"])

    assert index_node.instances[0] is first
    assert first.widget.props["text"] == "0:x"
    assert index_node.instances[1].widget.props["text"] == "1:y"
    assert index_node.instances[2].widget.props["text"] == "2:z"

    stale = index_node.instances[2]
    set_items(["q"])

    assert index_node.instances == [first]
    assert first.widget.props["text"] == "0:q"
    assert stale.widget is None


def test_dynamic_switches_component_factories():
    selected, set_selected = reactive.create_signal(cast(Any, None))

    @component
    def Red(props):
        return widgets.Label(text="red")

    @component
    def Blue(props):
        return widgets.Label(text="blue")

    set_selected(lambda _: Red)
    mount = runtime.create_root(lambda: control.Dynamic(selected), title="Demo")
    dynamic = mount.node.children[0]

    assert dynamic.active.widget.props["text"] == "red"

    set_selected(lambda _: Blue)

    assert dynamic.active.widget.props["text"] == "blue"


def test_dynamic_forwards_reactive_props_to_selected_component():
    selected, set_selected = reactive.create_signal(cast(Any, None))
    item, set_item = reactive.create_signal("first")
    selected_item = reactive.create_memo(lambda: item())

    @component
    def Detail(props):
        return widgets.Label(text=lambda: f"Detail: {props.item()}")

    set_selected(lambda _: Detail)
    mount = runtime.create_root(lambda: control.Dynamic(selected, item=selected_item), title="Demo")
    dynamic = mount.node.children[0]

    assert dynamic.active.widget.props["text"] == "Detail: first"

    set_item("second")

    assert dynamic.active.widget.props["text"] == "Detail: second"
