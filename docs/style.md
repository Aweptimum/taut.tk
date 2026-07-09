# Styles

Styles are small, typed prop dictionaries. They are useful when a group of widget
or layout props is reused, but they are not a CSS cascade and they are not a
replacement for extracting a component.

```python
from solid_tk import style

styles = {
    "panel": style.define(bg="#f8fafc", padding=10, gap=8),
    "title": style.define(font=("TkDefaultFont", 13, "bold")),
}
```

Because a `Style` is a mapping, a single style can be passed directly with
Python's normal kwargs unpacking:

```python
VStack(
    Label(text="Settings", **styles["title"]),
    **styles["panel"],
)
```

Use `style.merge()` when you need to compose styles or add conditional props.
Later values win.

```python
Label(
    text="Status",
    **style.merge(
        styles["title"],
        is_error and {"fg": "red"},
        fg="blue",
    ),
)
```

For repeated styled widgets, use `style.component()` to create a small factory.
Call-site props still override the factory's styles and defaults.

```python
Panel = style.component(VStack, styles["panel"])
PanelTitle = style.component(Label, styles["title"])

Panel(
    PanelTitle(text="Settings"),
    Label(text="Ready"),
)
```

This works for stack helpers and `Item` as well:

```python
GrowItem = style.component(Item, style.define(grow=True, fill="both"))

HStack(
    Label(text="fixed"),
    GrowItem(Frame()),
)
```

Prefer a normal Python helper or component when a pattern has structure, state,
or domain meaning. `style.component()` is best for repeated prop bundles; once
the body itself matters, a named function usually reads better.
