from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import cast

import pytest

from taut import component
from taut import control
from taut import layout
from taut import reactive
from taut import runtime
from taut import tk


def test_switch_renders_first_matching_case_and_fallback():
    mode, set_mode = reactive.create_signal("a")

    mount = runtime.create_root(
        lambda: control.Switch(
            control.Match(lambda: mode() == "a", lambda: tk.Label(text="A")),
            control.Match(lambda: mode() == "b", lambda: tk.Label(text="B")),
            fallback=lambda: tk.Label(text="fallback"),
        ),
        title="Demo",
    )
    switch = cast(Any, mount.node).children[0]

    assert switch.widget is mount.widget
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
                lambda: mode() == "ready", lambda: tk.Label(text="Ready")
            ),
            fallback=lambda: tk.Label(text="Idle"),
        ),
        title="Demo",
    )
    switch = cast(Any, mount.node).children[0]

    assert switch.widget is mount.widget
    assert switch.active.widget.props["text"] == "Idle"


def test_show_mounts_active_child_as_fragment():
    mount = runtime.create_root(
        lambda: layout.VStack(
            tk.Label(text="Before"),
            control.Show(True, lambda: tk.Label(text="Shown")),
            tk.Label(text="After"),
        ),
        title="Demo",
    )
    stack = mount.widget.children[0]
    show = cast(Any, mount.node).children[0].children[1]

    assert show.widget is stack
    assert [child.props["text"] for child in stack.children] == [
        "Before",
        "Shown",
        "After",
    ]


def test_index_reuses_nodes_by_index_and_updates_item_accessors():
    items, set_items = reactive.create_signal(["a", "b"])

    mount = runtime.create_root(
        lambda: control.Index(
            items,
            lambda item, index: tk.Label(text=lambda: f"{index}:{item()}"),
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


def test_for_mounts_repeated_children_as_fragment():
    items, _set_items = reactive.create_signal(["a", "b"])

    mount = runtime.create_root(
        lambda: layout.VStack(
            tk.Label(text="Before"),
            control.For(
                items,
                lambda item: tk.Label(text=item),
            ),
            tk.Label(text="After"),
        ),
        title="Demo",
    )
    stack = mount.widget.children[0]
    for_node = cast(Any, mount.node).children[0].children[1]

    assert for_node.widget is stack
    assert [child.props["text"] for child in stack.children] == [
        "Before",
        "a",
        "b",
        "After",
    ]


def test_for_reuses_object_items_and_updates_index_accessors_when_reordered():
    first = object()
    second = object()
    items, set_items = reactive.create_signal([first, second])
    rendered = {}

    def render(item, index):
        node = tk.Label(text=lambda: str(index()))
        rendered[item] = node
        return node

    mount = runtime.create_root(
        lambda: layout.VStack(control.For(items, render)), title="Demo"
    )
    first_node = rendered[first]
    second_node = rendered[second]

    assert first_node.widget.props["text"] == "0"
    assert second_node.widget.props["text"] == "1"

    set_items([second, first])

    assert rendered == {first: first_node, second: second_node}
    assert first_node.widget.props["text"] == "1"
    assert second_node.widget.props["text"] == "0"

    mount.dispose()


def test_for_reorders_retained_widgets_using_plain_pack_layout():
    first = object()
    second = object()
    items, set_items = reactive.create_signal([first, second])
    rendered = {}

    def render(item):
        node = tk.Label(text="row")
        rendered[item] = node
        return node

    mount = runtime.create_root(lambda: control.For(items, render), title="Demo")

    # Assert packed_children order
    first_widget = rendered[first].widget
    second_widget = rendered[second].widget

    assert mount.widget.packed_children == [first_widget, second_widget]

    # Update order, check again
    set_items([second, first])

    assert mount.widget.packed_children == [second_widget, first_widget]
    assert rendered[first].widget is first_widget
    assert rendered[second].widget is second_widget

    mount.dispose()


def test_for_recreates_equal_but_distinct_objects():
    @dataclass
    class Item:
        name: str

    first = Item("same")
    replacement = Item("same")
    items, set_items = reactive.create_signal([first])
    rendered = []

    def render(item):
        node = tk.Label(text=item.name)
        rendered.append(node)
        return node

    mount = runtime.create_root(lambda: control.For(items, render), title="Demo")
    first_node = rendered[0]

    assert first == replacement
    assert first is not replacement

    set_items([replacement])

    assert len(rendered) == 2
    assert rendered[1] is not first_node
    assert first_node.widget is None

    mount.dispose()


def test_for_reuses_equal_primitive_values():
    first = "".join(["same", " value"])
    replacement = "same value"
    items, set_items = reactive.create_signal([first])
    rendered = []

    def render(item):
        node = tk.Label(text=item)
        rendered.append(node)
        return node

    mount = runtime.create_root(lambda: control.For(items, render), title="Demo")
    first_node = rendered[0]

    assert first == replacement
    assert first is not replacement

    set_items([replacement])

    assert rendered == [first_node]
    assert first_node.widget is not None

    mount.dispose()


def test_for_does_not_match_boolean_and_numeric_values():
    items, set_items = reactive.create_signal(cast(list[Any], [True]))
    rendered = []

    def render(item):
        node = tk.Label(text=str(item))
        rendered.append(node)
        return node

    mount = runtime.create_root(lambda: control.For(items, render), title="Demo")
    boolean_node = rendered[0]

    set_items([1])

    assert len(rendered) == 2
    assert boolean_node.widget is None

    mount.dispose()


def test_for_supports_duplicate_item_occurrences():
    items, set_items = reactive.create_signal(["same", "same"])
    rendered = []

    def render(item):
        node = tk.Label(text=item)
        rendered.append(node)
        return node

    mount = runtime.create_root(
        lambda: layout.VStack(control.For(items, render)), title="Demo"
    )
    first_node, second_node = rendered

    set_items(["same"])

    assert first_node.widget is not None
    assert second_node.widget is None

    set_items(["same", "same"])

    assert len(rendered) == 3
    assert first_node.widget is not None
    assert rendered[2].widget is not None

    mount.dispose()


def test_for_disposes_only_the_removed_item_scope():
    first = object()
    second = object()
    items, set_items = reactive.create_signal([first, second])
    cleanups = []

    def render(item):
        runtime.on_cleanup(lambda: cleanups.append(item))
        return tk.Label(text="row")

    mount = runtime.create_root(lambda: control.For(items, render), title="Demo")

    set_items([second])

    assert cleanups == [first]

    mount.dispose()

    assert cleanups == [first, second]


@pytest.mark.parametrize("empty", [[], None, False])
def test_for_renders_fallback_for_empty_or_falsy_sources(empty):
    items, set_items = reactive.create_signal(cast(Any, ["row"]))
    cleanups = []

    def fallback():
        runtime.on_cleanup(lambda: cleanups.append("fallback"))
        return tk.Label(text="Empty")

    mount = runtime.create_root(
        lambda: control.For(items, lambda item: tk.Label(text=item), fallback=fallback),
        title="Demo",
    )
    for_node = cast(Any, mount.node).children[0]

    set_items(empty)

    fallback_node = for_node.active[0].rendered
    assert fallback_node.widget.props["text"] == "Empty"

    set_items(["next"])

    assert fallback_node.widget is None
    assert cleanups == ["fallback"]

    mount.dispose()


def test_for_runs_fallback_mount_and_cleanup_in_its_own_scope():
    items, set_items = reactive.create_signal(cast(Any, []))
    events = []

    def fallback():
        runtime.on_mount(lambda: events.append("mount"))
        runtime.on_cleanup(lambda: events.append("cleanup"))
        return tk.Label(text="Empty")

    mount = runtime.create_root(
        lambda: control.For(items, lambda item: tk.Label(text=item), fallback=fallback),
        title="Demo",
    )

    assert events == ["mount"]

    set_items(["row"])

    assert events == ["mount", "cleanup"]

    mount.dispose()


def test_for_does_not_track_reactive_reads_in_renderer():
    items = reactive.create_signal(["row"])[0]
    incidental, set_incidental = reactive.create_signal("first")
    renders = []

    def render(item):
        renders.append((item, incidental()))
        return tk.Label(text=item)

    mount = runtime.create_root(lambda: control.For(items, render), title="Demo")

    set_incidental("second")

    assert renders == [("row", "first")]

    mount.dispose()


def test_dynamic_switches_component_factories():
    selected, set_selected = reactive.create_signal(cast(Any, None))

    @component
    def Red(props):
        return tk.Label(text="red")

    @component
    def Blue(props):
        return tk.Label(text="blue")

    set_selected(lambda _: Red)
    mount = runtime.create_root(lambda: control.Dynamic(selected), title="Demo")
    dynamic = cast(Any, mount.node).children[0]

    assert dynamic.widget is mount.widget
    assert dynamic.active.widget.props["text"] == "red"

    set_selected(lambda _: Blue)

    assert dynamic.active.widget.props["text"] == "blue"


def test_dynamic_forwards_reactive_props_to_selected_component():
    selected, set_selected = reactive.create_signal(cast(Any, None))
    item, set_item = reactive.create_signal("first")
    selected_item = reactive.create_memo(lambda: item())

    @component
    def Detail(props):
        return tk.Label(text=lambda: f"Detail: {props.item()}")

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
            fallback=lambda error, reset: tk.Label(text=f"Caught: {error}"),
        ),
        title="Demo",
    )
    boundary = cast(Any, mount.node).children[0]

    assert boundary.widget is mount.widget
    assert boundary.active_kind == "fallback"
    assert boundary.active.widget.props["text"] == "Caught: boom"


def test_error_boundary_default_fallback_uses_primitive_child_factory():
    def Broken():
        raise ValueError("boom")

    mount = runtime.create_root(
        lambda: control.ErrorBoundary(Broken),
        title="Demo",
    )
    boundary = cast(Any, mount.node).children[0]

    assert boundary.active_kind == "fallback"
    assert boundary.active.widget.props["text"] == "boom"


def test_error_boundary_catches_child_reactive_update_errors():
    value, set_value = reactive.create_signal("ok")

    def text():
        if value() == "bad":
            raise ValueError("bad value")
        return value()

    mount = runtime.create_root(
        lambda: control.ErrorBoundary(
            lambda: tk.Label(text=text),
            fallback=lambda error, reset: tk.Label(text=f"Caught: {error}"),
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

        return tk.Label(text=text)

    mount = runtime.create_root(
        lambda: control.ErrorBoundary(
            lambda: control.Show(True, lambda: Risky(value=value)),
            fallback=lambda error, reset: tk.Label(text=f"Caught: {error}"),
        ),
        title="Demo",
    )
    boundary = cast(Any, mount.node).children[0]
    show = boundary.active
    risky_widget = show.active.widget

    set_value("bad")

    assert risky_widget.destroyed
    assert show.widget is None
    assert boundary.active_kind == "fallback"
    assert boundary.active.widget.props["text"] == "Caught: bad value"


def test_error_boundary_reset_retries_child_rendering():
    value, set_value = reactive.create_signal("ok")

    def text():
        if value() == "bad":
            raise ValueError("bad value")
        return value()

    def fallback(error, reset):
        return tk.Button(
            text=f"Reset from {error}",
            command=lambda: (set_value("ok"), reset()),
        )

    mount = runtime.create_root(
        lambda: control.ErrorBoundary(
            lambda: tk.Label(text=text), fallback=fallback
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
            fallback=lambda error, reset: tk.Label(text=f"Outer: {error}"),
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
        return tk.Label(text="Ready")

    mount = runtime.create_root(
        lambda: control.ErrorBoundary(
            lambda: App(),
            fallback=lambda error, reset: tk.Label(text=f"Caught: {error}"),
        ),
        title="Demo",
    )
    boundary = cast(Any, mount.node).children[0]

    with pytest.raises(RuntimeError, match="event failed"):
        mount.widget.run_next_after()

    assert boundary.active_kind == "child"
    assert boundary.active.widget.props["text"] == "Ready"
