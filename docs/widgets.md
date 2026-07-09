# Widgets

Widgets are thin node wrappers around Tk and ttk widgets. They accept positional
children, Tk-style keyword props, reactive prop values, and layout props.

Import from:

```python
from solid_tk import tk
from solid_tk import layout
from solid_tk import ttk
```

## Classic Tk Namespace

`solid_tk.tk` exports:

```python
tk.Tk
tk.Frame
tk.Label
tk.Button
tk.Entry
tk.Checkbutton
tk.Scale
tk.Canvas
tk.LabelFrame
tk.Listbox
tk.Menu
tk.Menubutton
tk.Message
tk.OptionMenu
tk.PanedWindow
tk.PhotoImage
tk.Radiobutton
tk.Scrollbar
tk.Spinbox
tk.Text
tk.Portal
tk.Fragment
```

`solid_tk.layout` exports the layout helper components:

```python
layout.Grid
layout.GridItem
layout.VStack
layout.HStack
layout.Item
```

`tk.Tk` is normally created for you by `create_root()`:

```python
mount = create_root(lambda: App(), title="Solid TK")
mount.widget.mainloop()
```

## Themed ttk Namespace

`solid_tk.ttk` exports:

```python
ttk.Frame
ttk.Label
ttk.Button
ttk.Entry
ttk.Checkbutton
ttk.Scale
ttk.Combobox
ttk.LabelFrame
ttk.Labelframe
ttk.LabeledScale
ttk.Menubutton
ttk.Notebook
ttk.OptionMenu
ttk.PanedWindow
ttk.Panedwindow
ttk.Separator
ttk.Progressbar
ttk.Radiobutton
ttk.Scrollbar
ttk.Sizegrip
ttk.Spinbox
ttk.Treeview
```

ttk widgets support ttk styling through `style=...`; see [Styles](style.md).

## Children

Children are passed positionally:

```python
layout.VStack(
    tk.Label(text="Name"),
    tk.Entry(value=name, on_input=set_name),
)
```

Primitive children are rendered with the widget layer's text-child factory,
which currently creates `tk.Label(text=str(child))`:

```python
layout.VStack("Hello", 42)
```

Use `Fragment(...)` to return multiple children without a wrapper widget:

```python
from solid_tk import Fragment

@component
def Actions(props):
    return Fragment(
        tk.Button(text="Save"),
        tk.Button(text="Cancel"),
    )
```

Components can also return transparent control-flow nodes such as `For(...)`.
The parent widget owns layout in both cases.

## Reactive Props

Widget props can be plain values, accessors, or callables:

```python
tk.Label(text="Snapshot")
tk.Label(text=name)
tk.Label(text=lambda: f"Hello {name()}")
```

Non-event callable props are treated as reactive expressions. When the
expression changes, the widget is configured with the new value.

Event props are passed as callbacks:

```python
tk.Button(text="Increment", on_click=lambda: set_count(lambda n: n + 1))
tk.Button(text="Save", command=save)
```

`on_click` is an alias for Tk's `command`.

## Writable Inputs

`tk.Entry` and `ttk.Entry` support `value` and `on_input`:

```python
text, set_text = create_signal("")

tk.Entry(value=text, on_input=set_text)
```

`value` is synced into a Tk `StringVar`. User edits call `on_input` with the new
string value.

Do not pass both `value` and `textvariable` to the same entry. `value` owns the
generated variable.

`tk.Scale` and `ttk.Scale` also support `value` and `on_input` for numeric
values. Their `value` prop owns a generated Tk variable, so do not pass both
`value` and `variable` to the same scale.

## Images and Canvas

Use `tk.PhotoImage(...)` to create a Tkinter `PhotoImage`, then pass it to
widget `image=` props or Canvas item methods. Keep a Python reference to the
image for as long as Tk needs to display it.

`tk.Canvas` is exposed as a regular widget node. It accepts Canvas
configuration props and can contain child widgets, but drawing items are still
created through Tk's Canvas methods on the mounted widget.

Menu entries, notebook tabs, paned-window panes, tree rows, and other
widget-specific child/item APIs are exposed through the mounted Tk widget's
standard methods. The namespace wrappers create and configure the widgets; they
do not replace those Tk item APIs with declarative child helpers yet.

## Layout Props

Every widget can receive one layout prop:

```python
tk.Label(text="Packed", pack={"side": "left"})
tk.Label(text="Gridded", grid={"row": 0, "column": 1, "sticky": "ew"})
tk.Label(text="Placed", place={"x": 10, "y": 10})
```

If no layout prop is provided, classic widget helpers default to `pack={}`.
`create_root()` expands the app's default-packed root child with:

```python
{"fill": "both", "expand": True}
```

Explicit root-child layout is preserved.

Avoid mixing Tk geometry managers inside the same parent. If one child uses
`grid`, its siblings in that parent should use `grid` too.

## Stacks

`VStack` and `HStack` are convenience `Frame` nodes that assign pack options to
their visible children.

```python
layout.VStack(
    tk.Label(text="One"),
    tk.Label(text="Two"),
    padding=12,
    gap=6,
)
```

Stack props:

- `padding`: integer or `(padx, pady)` tuple applied to the frame
- `gap`: spacing between children
- `align`: `"start"`, `"center"`, `"end"`, or `"stretch"`
- `fill`: `"none"`, `"x"`, `"y"`, or `"both"`
- `grow`: whether children expand

Use `Item(child, ...)` for per-child stack overrides:

```python
layout.VStack(
    layout.Item(tk.Label(text="Title"), align="center"),
    layout.Item(tk.Button(text="Save"), fill="none"),
)
```

`Item` attaches stack layout metadata to a child node. It does not create a
wrapper widget.

Children with explicit `grid` or `place` layout are not rewritten by stack
layout.

## Grid

`Grid` is a convenience `Frame` node that assigns grid options to its visible
children. It works well with transparent control flow:

```python
layout.Grid(
    For(images, lambda image: ImageTile(image), key=lambda image: image["id"]),
    columns=2,
    column_weights=(1, 1),
    gap=6,
    row_weights={0: 1},
    sticky="nsew",
)
```

Grid props:

- `columns`: number of columns before wrapping to the next row
- `column_weights`: tuple/list by column index, or `{index: weight}` mapping
- `gap`: integer padding applied as `padx` and `pady` to each child
- `row_weights`: tuple/list by row index, or `{index: weight}` mapping
- `sticky`: Tk grid sticky value for each child, defaulting to `"nsew"`
- `padding`: integer or `(padx, pady)` tuple applied to the grid frame

Use `GridItem(child, ...)` for per-child grid overrides:

```python
layout.Grid(
    layout.GridItem(tk.Label(text="Title"), columnspan=2, sticky="ew"),
    tk.Label(text="Left"),
    tk.Label(text="Right"),
    columns=2,
)
```

Child widgets can still provide explicit `grid={...}` options. `GridItem` and
explicit `grid={...}` options override the row, column, sticky, or padding
computed by the parent grid. Children with explicit `place` layout are not
rewritten by grid layout.

## Transparent Layout

`Fragment`, `Show`, `For`, `Switch`, `Index`, `Dynamic`, and components that
return transparent nodes do not create wrapper frames. They expose their child
nodes to the parent:

```python
layout.VStack(
    tk.Label(text="Before"),
    For(items, lambda item: tk.Label(text=item), key=lambda item: item),
    tk.Label(text="After"),
)
```

The parent `VStack` lays out the repeated labels between the two surrounding
labels.

## Portal

`Portal(child, title=None, on_close=None)` mounts a child subtree into a
`tk.Toplevel`.

```python
tk.Portal(
    lambda: layout.VStack(tk.Label(text="Dialog")),
    title="Dialog",
    on_close=lambda: set_open(False),
)
```

The child is usually callable so it is created under the portal owner. The
portal owns its subtree and disposes it when closed.

## Styles

Pass `style=...` to classic Tk widgets, ttk widgets, and stack helpers:

```python
tk.Label(text="Classic", style=styles.title)
ttk.Label(text="Themed", style=styles.title)
layout.VStack(style=styles.panel)
```

Classic Tk widgets unpack style props directly. ttk widgets configure and use a
generated ttk style name. See [Styles](style.md).

## Example

See `examples/layout_demo` for stacks, spacing, padding, alignment, per-child
layout overrides, and styles:

```sh
python -m examples.layout_demo
```

See `examples/portal_demo` for `Portal`:

```sh
python -m examples.portal_demo
```
