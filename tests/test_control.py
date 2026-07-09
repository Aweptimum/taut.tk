from __future__ import annotations

from typing import Any
from typing import cast

import pytest

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
    switch = cast(Any, mount.node).children[0]

    assert switch.active.widget.props["text"] == "A"

    set_mode("b")

    assert switch.active.widget.props["text"] == "B"

    set_mode("c")

    assert switch.active.widget.props["text"] == "fallback"


def test_switch_renders_initial_fallback_when_no_case_matches():
    mode, _set_mode = reactive.create_signal("idle")

    mount = runtime.create_root(
        lambda: control.Switch(
            control.Match(
                lambda: mode() == "ready", lambda: widgets.Label(text="Ready")
            ),
            fallback=lambda: widgets.Label(text="Idle"),
        ),
        title="Demo",
    )
    switch = cast(Any, mount.node).children[0]

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
    index_node = cast(Any, mount.node).children[0]
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
    dynamic = cast(Any, mount.node).children[0]

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
    mount = runtime.create_root(
        lambda: control.Dynamic(selected, item=selected_item), title="Demo"
    )
    dynamic = cast(Any, mount.node).children[0]

    assert dynamic.active.widget.props["text"] == "Detail: first"

    set_item("second")

    assert dynamic.active.widget.props["text"] == "Detail: second"


def test_error_boundary_renders_fallback_when_child_render_raises():
    def Broken():
        raise ValueError("boom")

    mount = runtime.create_root(
        lambda: control.ErrorBoundary(
            Broken,
            fallback=lambda error, reset: widgets.Label(text=f"Caught: {error}"),
        ),
        title="Demo",
    )
    boundary = cast(Any, mount.node).children[0]

    assert boundary.active_kind == "fallback"
    assert boundary.active.widget.props["text"] == "Caught: boom"


def test_error_boundary_catches_child_reactive_update_errors():
    value, set_value = reactive.create_signal("ok")

    def text():
        if value() == "bad":
            raise ValueError("bad value")
        return value()

    mount = runtime.create_root(
        lambda: control.ErrorBoundary(
            lambda: widgets.Label(text=text),
            fallback=lambda error, reset: widgets.Label(text=f"Caught: {error}"),
        ),
        title="Demo",
    )
    boundary = cast(Any, mount.node).children[0]
    child_widget = boundary.active.widget

    assert boundary.active_kind == "child"
    assert child_widget.props["text"] == "ok"

    set_value("bad")

    assert child_widget.destroyed
    assert boundary.active_kind == "fallback"
    assert boundary.active.widget.props["text"] == "Caught: bad value"


def test_error_boundary_can_replace_show_after_reactive_child_error():
    value, set_value = reactive.create_signal("ok")

    @component
    def Risky(props):
        def text():
            if props.value() == "bad":
                raise ValueError("bad value")
            return props.value()

        return widgets.Label(text=text)

    mount = runtime.create_root(
        lambda: control.ErrorBoundary(
            lambda: control.Show(True, lambda: Risky(value=value)),
            fallback=lambda error, reset: widgets.Label(text=f"Caught: {error}"),
        ),
        title="Demo",
    )
    boundary = cast(Any, mount.node).children[0]
    show = boundary.active
    show_widget = show.widget

    set_value("bad")

    assert show_widget.destroyed
    assert boundary.active_kind == "fallback"
    assert boundary.active.widget.props["text"] == "Caught: bad value"


def test_error_boundary_reset_retries_child_rendering():
    value, set_value = reactive.create_signal("ok")

    def text():
        if value() == "bad":
            raise ValueError("bad value")
        return value()

    def fallback(error, reset):
        return widgets.Button(
            text=f"Reset from {error}",
            command=lambda: (set_value("ok"), reset()),
        )

    mount = runtime.create_root(
        lambda: control.ErrorBoundary(
            lambda: widgets.Label(text=text), fallback=fallback
        ),
        title="Demo",
    )
    boundary = cast(Any, mount.node).children[0]

    set_value("bad")
    assert boundary.active_kind == "fallback"

    boundary.active.widget.props["command"]()

    assert boundary.active_kind == "child"
    assert boundary.active.widget.props["text"] == "ok"


def test_error_boundary_fallback_errors_bubble_to_parent_boundary():
    def Broken():
        raise ValueError("child failed")

    def BrokenFallback(error, reset):
        raise RuntimeError("fallback failed")

    mount = runtime.create_root(
        lambda: control.ErrorBoundary(
            lambda: control.ErrorBoundary(Broken, fallback=BrokenFallback),
            fallback=lambda error, reset: widgets.Label(text=f"Outer: {error}"),
        ),
        title="Demo",
    )
    boundary = cast(Any, mount.node).children[0]

    assert boundary.active_kind == "fallback"
    assert boundary.active.widget.props["text"] == "Outer: fallback failed"


def test_error_boundary_does_not_catch_deferred_callback_errors():
    def boom():
        raise RuntimeError("event failed")

    @component
    def App(props):
        runtime.defer(boom)
        return widgets.Label(text="Ready")

    mount = runtime.create_root(
        lambda: control.ErrorBoundary(
            lambda: App(),
            fallback=lambda error, reset: widgets.Label(text=f"Caught: {error}"),
        ),
        title="Demo",
    )
    boundary = cast(Any, mount.node).children[0]

    with pytest.raises(RuntimeError, match="event failed"):
        mount.widget.run_next_after()

    assert boundary.active_kind == "child"
    assert boundary.active.widget.props["text"] == "Ready"
