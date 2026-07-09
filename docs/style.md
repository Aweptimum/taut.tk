# Styles

Styles are reusable prop dictionaries with optional generated names. They make
repeated widget and layout props easier to share without introducing a CSS
cascade.

Prefer defining styles as ordinary module variables:

```python
# styles.py
from taut import style

panel = style.define("panel", bg="#f8fafc", padding=10, gap=8)
title = style.define(
    "title",
    fg="#111827",
    font=("TkDefaultFont", 13, "bold"),
)
```

The first argument names the style. The name is used by themed `ttk` widgets,
and ordinary module variables keep `styles.panel` and `styles.title` visible to
static type checkers.

The same style can be passed to classic `tk` widgets, themed `ttk` widgets, and
stack helpers:

```python
from . import styles
from taut import layout
from taut import tk
from taut import ttk

tk.Label(text="Classic", style=styles.title)
ttk.Label(text="Themed", style=styles.title)
layout.VStack(tk.Label(text="Settings"), style=styles.panel)
```

Classic `tk` widgets unpack the style into direct widget options. In the example
above, `tk.Label(..., style=styles.title)` receives `fg` and `font`.

Themed `ttk` widgets configure and use a generated ttk style name. In the
example above, `ttk.Label(..., style=styles.title)` uses `Title.TLabel`, and the
style config maps friendly aliases such as `fg`, `bg`, and `bd` to ttk's
`foreground`, `background`, and `borderwidth` options.

Layout helpers can still consume their own configuration props from styles:

```python
content = style.define("content", padding=12, gap=8)

layout.VStack(
    tk.Label(text="One"),
    tk.Label(text="Two"),
    style=content,
)
```

Grid helpers can do the same:

```python
image_grid = style.define("image_grid", columns=2, gap=6, sticky="nsew")
wide_cell = style.grid_item(columnspan=2, sticky="ew")

layout.Grid(
    For(images, lambda image: ImageTile(image), key=lambda image: image["id"]),
    layout.GridItem(Footer(), style=wide_cell),
    style=image_grid,
)
```

Styles cannot define parent-owned Tk geometry manager props: `pack`, `grid`, or
`place`. Pass those directly at the call site so placement stays visible where
the widget is used.

Use `style.merge()` when composing styles or adding conditional props. Later
styles win, and the generated style name comes from the last named style.

```python
accent = style.define("accent", fg="blue", padx=8)
danger = style.define("danger", fg="red")

ttk.Label(
    text="Status",
    style=style.merge(accent, is_error and danger),
)
```

For repeated styled widgets, use `style.component()` to create a small factory.
Call-site props still override style props.

```python
Panel = style.component(layout.VStack, styles.panel)
PanelTitle = style.component(ttk.Label, styles.title)

Panel(
    PanelTitle(text="Settings"),
    ttk.Button(text="Save"),
)
```

Anonymous styles are still useful for one-off composition:

```python
compact = style.define(padx=4, pady=2)
```

A `Style` is a mapping, so `**style.merge(...)` remains available when you
explicitly need a plain kwargs-style spread. Prefer `style=...` for normal widget
use so classic Tk and ttk can interpret the style appropriately.

## Example
See `examples/layout_demo` for stack spacing, padding, alignment, per-child
layout overrides, and importable style definitions:

```sh
python -m examples.layout_demo
```
