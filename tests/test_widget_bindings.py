from __future__ import annotations

import pytest
from fakes import FakeStringVar

from solid_tk import component
from solid_tk import control
from solid_tk import reactive
from solid_tk import runtime
from solid_tk import style
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


def test_mount_dispose_is_idempotent():
    events = []

    @component
    def App(props):
        runtime.on_cleanup(lambda: events.append("cleanup"))
        return widgets.Label(text="App")

    mount = runtime.create_root(App, title="Demo")
    app_label = mount.widget.children[0]

    mount.dispose()
    mount.dispose()

    assert app_label.destroy_count == 1
    assert mount.widget.destroy_count == 1
    assert events == ["cleanup"]


def test_root_window_close_disposes_mounted_app_node():
    events = []

    @component
    def App(props):
        runtime.on_cleanup(lambda: events.append("cleanup"))
        return widgets.Label(text="App")

    mount = runtime.create_root(App, title="Demo")
    app_label = mount.widget.children[0]

    mount.widget.protocols["WM_DELETE_WINDOW"]()

    assert app_label.destroyed
    assert mount.widget.destroyed
    assert events == ["cleanup"]


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


def test_create_root_expands_default_app_layout():
    mount = runtime.create_root(
        lambda: widgets.VStack(widgets.Label(text="Hello")),
        title="Demo",
    )
    app = mount.widget.children[0]

    assert app.pack_kwargs == {"fill": "both", "expand": True}


def test_primitive_children_render_with_registered_text_factory():
    mount = runtime.create_root(
        lambda: widgets.VStack("Hello", 42),
        title="Demo",
    )
    first, second = mount.widget.children[0].children

    assert first.props["text"] == "Hello"
    assert second.props["text"] == "42"


def test_create_root_preserves_explicit_app_layout():
    mount = runtime.create_root(
        lambda: widgets.VStack(widgets.Label(text="Hello"), pack={"side": "left"}),
        title="Demo",
    )
    app = mount.widget.children[0]

    assert app.pack_kwargs == {"side": "left"}


def test_vstack_defaults_match_existing_layout():
    mount = runtime.create_root(
        lambda: widgets.VStack(widgets.Label(text="One"), widgets.Label(text="Two")),
        title="Demo",
    )
    first, second = mount.widget.children[0].children

    assert first.pack_kwargs == {
        "side": "top",
        "anchor": "w",
        "expand": False,
        "fill": "x",
    }
    assert second.pack_kwargs == first.pack_kwargs


def test_stack_padding_gap_and_alignment_are_applied():
    mount = runtime.create_root(
        lambda: widgets.VStack(
            widgets.Label(text="One"),
            widgets.Label(text="Two"),
            padding=(8, 4),
            gap=6,
            align="center",
            fill="none",
        ),
        title="Demo",
    )
    stack = mount.widget.children[0]
    first, second = stack.children

    assert stack.props["padx"] == 8
    assert stack.props["pady"] == 4
    assert first.pack_kwargs == {
        "side": "top",
        "anchor": "center",
        "expand": False,
        "pady": (0, 6),
    }
    assert second.pack_kwargs == {
        "side": "top",
        "anchor": "center",
        "expand": False,
    }


def test_hstack_item_overrides_stack_child_layout():
    mount = runtime.create_root(
        lambda: widgets.HStack(
            widgets.Label(text="Fixed"),
            widgets.Item(widgets.Label(text="Growing"), grow=True, fill="both", align="stretch"),
            gap=3,
        ),
        title="Demo",
    )
    fixed, growing = mount.widget.children[0].children

    assert fixed.pack_kwargs == {
        "side": "left",
        "anchor": "center",
        "expand": False,
        "padx": (0, 3),
    }
    assert growing.pack_kwargs == {
        "side": "left",
        "anchor": "center",
        "expand": True,
        "fill": "both",
    }


def test_stack_preserves_explicit_grid_and_place_layouts():
    mount = runtime.create_root(
        lambda: widgets.VStack(
            widgets.Label(text="Grid", grid={"row": 0, "column": 1}),
            widgets.Label(text="Place", place={"x": 10, "y": 20}),
        ),
        title="Demo",
    )
    grid_child, place_child = mount.widget.children[0].children

    assert grid_child.grid_kwargs == {"row": 0, "column": 1}
    assert place_child.place_kwargs == {"x": 10, "y": 20}


def test_grid_tiles_for_children_by_visible_order():
    items, set_items = reactive.create_signal(["a", "b", "c", "d"])

    mount = runtime.create_root(
        lambda: widgets.Grid(
            control.For(items, lambda item: widgets.Label(text=item), key=lambda item: item),
            columns=2,
            gap=4,
            sticky="ew",
        ),
        title="Demo",
    )
    first, second, third, fourth = mount.widget.children[0].children

    assert first.grid_kwargs == {
        "row": 0,
        "column": 0,
        "sticky": "ew",
        "padx": 4,
        "pady": 4,
    }
    assert second.grid_kwargs["row"] == 0
    assert second.grid_kwargs["column"] == 1
    assert third.grid_kwargs["row"] == 1
    assert third.grid_kwargs["column"] == 0
    assert fourth.grid_kwargs["row"] == 1
    assert fourth.grid_kwargs["column"] == 1

    set_items(["b", "d"])

    assert first.destroyed
    assert third.destroyed
    assert second.grid_kwargs["row"] == 0
    assert second.grid_kwargs["column"] == 0
    assert fourth.grid_kwargs["row"] == 0
    assert fourth.grid_kwargs["column"] == 1


def test_grid_accepts_layout_from_style():
    grid_style = style.grid(columns=2, gap=3, sticky="nsew", padding=8)

    mount = runtime.create_root(
        lambda: widgets.Grid(
            widgets.Label(text="One"),
            widgets.Label(text="Two"),
            style=grid_style,
        ),
        title="Demo",
    )
    grid = mount.widget.children[0]
    first, second = grid.children

    assert grid.props["padx"] == 8
    assert grid.props["pady"] == 8
    assert first.grid_kwargs == {
        "row": 0,
        "column": 0,
        "sticky": "nsew",
        "padx": 3,
        "pady": 3,
    }
    assert second.grid_kwargs["column"] == 1
