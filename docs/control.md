# Control Flow

Control-flow nodes are transparent to layout. They produce child nodes, and the
parent widget decides how those children are packed, gridded, placed, or stacked.

```python
from taut import layout

layout.VStack(
    tk.Label(text="Before"),
    For(items, lambda item: tk.Label(text=item), key=lambda item: item),
    tk.Label(text="After"),
)
```

The labels produced by `For` appear between `Before` and `After`; `For` does
not create a wrapper frame.

## API

Import control helpers from `taut.control`:

```python
from taut.control import Dynamic
from taut.control import ErrorBoundary
from taut.control import For
from taut.control import Index
from taut.control import Match
from taut.control import Show
from taut.control import Switch
```

## `Show`

`Show(when, children, fallback=None)` renders one child when `when` is truthy
and optionally renders a fallback when it is falsey.

```python
Show(
    lambda: count() % 2 == 0,
    lambda: tk.Label(text="Even"),
    fallback=lambda: tk.Label(text="Odd"),
)
```

`when` can be a plain value, an accessor, or a callable. The child and fallback
can be nodes or callables that return nodes.

## `For`

`For(each, render, key=None)` renders a keyed list.

```python
For(
    todos,
    lambda todo: tk.Label(text=todo["title"]),
    key=lambda todo: todo["id"],
)
```

Use a stable `key` when items can be inserted, removed, or reordered. If no key
is provided, object identity is used.

`For` returns children only. Put it inside a parent layout helper to control
geometry:

```python
layout.VStack(
    For(items, lambda item: tk.Label(text=item), key=lambda item: item),
    gap=4,
)
```

## `Index`

`Index(each, render)` keeps child nodes stable by index and gives the render
function an item accessor plus the numeric index.

```python
Index(
    items,
    lambda item, index: tk.Label(text=lambda: f"{index}: {item()}"),
)
```

Use `Index` when positions are stable and item values change. Use `For` when
item identity matters more than position.

## `Switch` And `Match`

`Switch(*cases, fallback=None)` renders the first matching `Match`.

```python
Switch(
    Match(lambda: status() == "ready", lambda: tk.Label(text="Ready")),
    Match(lambda: status() == "busy", lambda: tk.Label(text="Working")),
    fallback=lambda: tk.Label(text="Idle"),
)
```

Each `Match(when, children)` uses the same value/callable semantics as `Show`.

## `Dynamic`

`Dynamic(component, **props)` renders a selected component or node.

```python
selected, set_selected = create_signal(UserCard)

Dynamic(selected, user=user)
```

If `component` is a signal/accessor, changing it swaps the active component.
Additional keyword props are forwarded to callable components.

## `ErrorBoundary`

`ErrorBoundary(children, fallback=None)` catches render and reactive update
errors in its child subtree.

```python
ErrorBoundary(
    lambda: RiskyPanel(),
    fallback=lambda error, reset: layout.VStack(
        tk.Label(text=f"Problem: {error}"),
        tk.Button(text="Retry", on_click=reset),
    ),
)
```

Fallbacks can accept `(error, reset)` or no arguments. If no fallback is
provided, the boundary renders a label with the error text.

Deferred callbacks scheduled with `after`, `defer`, `interval`, or event
handlers are not caught as render errors. They run later on the Tk event loop.

## Components Returning Control Flow

Components can return transparent control-flow nodes directly:

```python
@component
def Rows(props):
    return For(props.items, lambda item: tk.Label(text=item), key=lambda item: item)

layout.VStack(
    tk.Label(text="Before"),
    Rows(items=items),
    tk.Label(text="After"),
)
```

The parent `VStack` still owns layout for the rows.

## Example

See `examples/control_demo` for `Show`, `Switch`, `For`, `Index`, and
`Dynamic` together:

```sh
python -m examples.control_demo
```

See `examples/error_boundary_demo` for error recovery:

```sh
python -m examples.error_boundary_demo
```
