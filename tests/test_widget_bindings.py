from __future__ import annotations

import pytest
from fakes import FakeStringVar

from taut import component
from taut import control
from taut import layout
from taut import reactive
from taut import runtime
from taut import style
from taut import tk


def test_entry_value_tracks_signal_changes_when_created_inside_root():
    value, set_value = reactive.create_signal("hello")

    mount = runtime.create_root(lambda: layout.VStack(tk.Entry(value=value)), title="Demo")
    entry = mount.widget.children[0].children[0]
    variable = entry.props["textvariable"]

    assert variable.get() == "hello"

    set_value("world")

    assert variable.get() == "world"


def test_entry_value_writes_user_changes_back_to_signal():
    value, set_value = reactive.create_signal("hello")

    mount = runtime.create_root(
        lambda: layout.VStack(tk.Entry(value=value, on_input=set_value)),
        title="Demo",
    )
    entry = mount.widget.children[0].children[0]
    variable = entry.props["textvariable"]

    variable.set("typed")

    assert value() == "typed"


def test_scale_on_input_can_use_owner_scoped_scheduler():
    rendered = []
    value, set_value = reactive.create_signal(0.0)

    def handle_input(next_value):
        set_value(next_value)
        runtime.after(80, lambda: rendered.append(next_value))

    mount = runtime.create_root(
        lambda: tk.Scale(
            value=value,
            on_input=handle_input,  # pyright: ignore[reportArgumentType]
        ),
        title="Demo",
    )
    scale = mount.widget.children[0]
    variable = scale.props["variable"]

    variable.set(12.0)
    scale.run_next_after()

    assert value() == 12.0
    assert rendered == [12.0]


def test_entry_value_conflicts_with_textvariable():
    value, _set_value = reactive.create_signal("hello")

    with pytest.raises(ValueError, match="value and textvariable"):
        runtime.create_root(
            lambda: tk.Entry(value=value, textvariable=FakeStringVar()),
            title="Demo",
        )


def test_tk_command_options_are_owned_callbacks_not_reactive_bindings():
    events = []

    def handle_scroll(first, last):
        runtime.after(10, lambda: events.append((first, last)))

    mount = runtime.create_root(
        lambda: tk.Entry(xscrollcommand=handle_scroll),
        title="Demo",
    )
    entry = mount.widget.children[0]

    assert events == []

    entry.props["xscrollcommand"]("0.0", "1.0")
    entry.run_next_after()

    assert events == [("0.0", "1.0")]


def test_create_root_disposes_mounted_app_node():
    value, _set_value = reactive.create_signal("hello")
    mount = runtime.create_root(lambda: layout.VStack(tk.Entry(value=value)), title="Demo")
    app_frame = mount.widget.children[0]

    mount.dispose()

    assert app_frame.destroyed


def test_mount_dispose_is_idempotent():
    events = []

    @component
    def App(props):
        runtime.on_cleanup(lambda: events.append("cleanup"))
        return tk.Label(text="App")

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
        return tk.Label(text="App")

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
        return tk.Label(text=props.text)

    mount = runtime.create_root(
        lambda: ForwardedLabel(text=lambda: f"Count: {count()}"),
        title="Demo",
    )
    label = mount.widget.children[0]

    assert label.props["text"] == "Count: 0"

    set_count(1)

    assert label.props["text"] == "Count: 1"


def test_button_on_click_uses_native_command_activation():
    events = []

    mount = runtime.create_root(
        lambda: tk.Button(text="Save", on_click=lambda: events.append("clicked")),
        title="Demo",
    )
    button = mount.widget.children[0]

    assert "command" in button.props
    assert button.bindings == {}

    button.props["command"]()

    assert events == ["clicked"]


def test_button_on_click_can_use_owner_scoped_scheduler():
    events = []

    mount = runtime.create_root(
        lambda: tk.Button(
            text="Save",
            on_click=lambda: runtime.after(10, lambda: events.append("saved")),
        ),
        title="Demo",
    )
    button = mount.widget.children[0]

    button.props["command"]()
    button.run_next_after()

    assert events == ["saved"]


def test_widget_on_click_binds_mouse_event():
    events = []
    event = object()

    mount = runtime.create_root(
        lambda: tk.Frame(on_click=lambda tk_event: events.append(tk_event)),
        title="Demo",
    )
    frame = mount.widget.children[0]

    bind_id = next(bind_id for sequence, bind_id in frame.bindings if sequence == "<Button-1>")
    frame.run_binding("<Button-1>", bind_id, event)

    assert events == [event]


def test_bound_widget_event_can_use_owner_scoped_scheduler():
    events = []

    mount = runtime.create_root(
        lambda: tk.Frame(
            on_click=lambda: runtime.after(10, lambda: events.append("clicked"))
        ),
        title="Demo",
    )
    frame = mount.widget.children[0]

    frame.run_binding("<Button-1>")
    frame.run_next_after()

    assert events == ["clicked"]


def test_widget_on_auxclick_binds_middle_mouse_event_and_unbinds_on_dispose():
    events = []

    mount = runtime.create_root(
        lambda: tk.Frame(on_auxclick=lambda: events.append("aux")),
        title="Demo",
    )
    frame = mount.widget.children[0]
    bind_id = next(bind_id for sequence, bind_id in frame.bindings if sequence == "<Button-2>")

    frame.run_binding("<Button-2>", bind_id, object())
    mount.dispose()

    assert events == ["aux"]
    assert ("<Button-2>", bind_id) in frame.unbound


def test_create_root_expands_default_app_layout():
    mount = runtime.create_root(
        lambda: layout.VStack(tk.Label(text="Hello")),
        title="Demo",
    )
    app = mount.widget.children[0]

    assert app.pack_kwargs == {"fill": "both", "expand": True}


def test_primitive_children_render_with_registered_text_factory():
    mount = runtime.create_root(
        lambda: layout.VStack("Hello", 42),
        title="Demo",
    )
    first, second = mount.widget.children[0].children

    assert first.props["text"] == "Hello"
    assert second.props["text"] == "42"


def test_create_root_preserves_explicit_app_layout():
    mount = runtime.create_root(
        lambda: layout.VStack(tk.Label(text="Hello"), pack={"side": "left"}),
        title="Demo",
    )
    app = mount.widget.children[0]

    assert app.pack_kwargs == {"side": "left"}


def test_vstack_defaults_match_existing_layout():
    mount = runtime.create_root(
        lambda: layout.VStack(tk.Label(text="One"), tk.Label(text="Two")),
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
        lambda: layout.VStack(
            tk.Label(text="One"),
            tk.Label(text="Two"),
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
        lambda: layout.HStack(
            tk.Label(text="Fixed"),
            layout.Item(tk.Label(text="Growing"), grow=True, fill="both", align="stretch"),
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
        lambda: layout.VStack(
            tk.Label(text="Grid", grid={"row": 0, "column": 1}),
            tk.Label(text="Place", place={"x": 10, "y": 20}),
        ),
        title="Demo",
    )
    grid_child, place_child = mount.widget.children[0].children

    assert grid_child.grid_kwargs == {"row": 0, "column": 1}
    assert place_child.place_kwargs == {"x": 10, "y": 20}


def test_grid_tiles_for_children_by_visible_order():
    items, set_items = reactive.create_signal(["a", "b", "c", "d"])

    mount = runtime.create_root(
        lambda: layout.Grid(
            control.For(items, lambda item: tk.Label(text=item), key=lambda item: item),
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
        lambda: layout.Grid(
            tk.Label(text="One"),
            tk.Label(text="Two"),
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


def test_grid_configures_row_and_column_weights():
    mount = runtime.create_root(
        lambda: layout.Grid(
            tk.Label(text="One"),
            tk.Label(text="Two"),
            columns=2,
            column_weights=(1, 2),
            row_weights={0: 1},
        ),
        title="Demo",
    )
    grid = mount.widget.children[0]

    assert grid.column_weights == {0: {"weight": 1}, 1: {"weight": 2}}
    assert grid.row_weights == {0: {"weight": 1}}


def test_grid_item_applies_per_child_grid_options():
    mount = runtime.create_root(
        lambda: layout.Grid(
            layout.GridItem(
                tk.Label(text="Wide"),
                columnspan=2,
                sticky="ew",
                padx=8,
            ),
            tk.Label(text="Next"),
            columns=2,
        ),
        title="Demo",
    )
    wide, next_child = mount.widget.children[0].children

    assert wide.grid_kwargs == {
        "row": 0,
        "column": 0,
        "sticky": "ew",
        "columnspan": 2,
        "padx": 8,
    }
    assert next_child.grid_kwargs == {"row": 0, "column": 1, "sticky": "nsew"}


def test_grid_item_accepts_style_props():
    item_style = style.grid_item(row=2, column=3, sticky="w")

    mount = runtime.create_root(
        lambda: layout.Grid(
            layout.GridItem(tk.Label(text="Styled"), style=item_style),
            columns=2,
        ),
        title="Demo",
    )
    child = mount.widget.children[0].children[0]

    assert child.grid_kwargs == {"row": 2, "column": 3, "sticky": "w"}
