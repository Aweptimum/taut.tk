# solid-tk

A small SolidJS-inspired runtime for Tkinter using
[reaktiv](https://pypi.org/project/reaktiv/) for fine-grained signals.

This is currently a prototype that I hope makes Tkinter more fun

```python
from typing import Protocol

from solid_tk import component
from solid_tk import tk
from solid_tk.reactive import Accessor
from solid_tk.reactive import Mutator
from solid_tk.reactive import create_signal
from solid_tk.runtime import create_root
from solid_tk.control import For
from solid_tk.control import Show


class CounterProps(Protocol):
    label: Accessor[str]
    count: Accessor[int]
    set_count: Mutator[int]


@component
def counter(props: CounterProps):
    todos, set_todos = create_signal(["wire props", "own effects", "dispose cleanly"])

    return tk.VStack(
        tk.Label(text=lambda: f"{props.label()}: {props.count()}"),
        tk.Button(text="Increment", on_click=lambda: props.set_count(lambda n: n + 1)),
        Show(
            lambda: props.count() % 2 == 0,
            lambda: tk.Label(text="Even"),
            fallback=lambda: tk.Label(text="Odd"),
        ),
        For(todos, lambda item: tk.Label(text=item), key=lambda item: item),
        tk.HStack(
            tk.Button(text="-", on_click=lambda: set_todos(lambda items: items[:-1])),
            gap=6,
        ),
        padding=12,
        gap=6,
    )

count, set_count = create_signal(0)
mount = create_root(
    lambda: counter(label="Solid TK", count=count, set_count=set_count),
    title="Solid TK",
)
mount.widget.mainloop()
```

## Why Tk?
I keep reaching for it every time I want a small UI at work and I keep getting bogged down in abstractions I think are loose but turn out to be more tightly-coupled than I realize. Imperatively updating state is also a chore and makes for widgets with lots of clunky helpers, and I find widget vars unwieldy. My most recent attempt I threw `reaktiv` at the problem and was surprised at how streamlined it made my widgets. I felt it could be more. So here we are.

## What's Here So Far

- Functional components using `@component` decorator
- Class `Component` with `__init__()/setup()` and `render()`
- `Props`, where every attribute is an accessor
- first-class component children through `props.children`
- transparent `Fragment(...)` nodes for returning multiple children
- widget namespaces: `tk` for classic Tk widgets and `ttk` for themed widgets
- layout helpers: `VStack`, `HStack`, `Grid`, `Item`
- StyleX-ish style objects agnostic to tk/ttk widgets with `style.define()`, `style.merge()`, and `style.component()`.
- some control flow: `Show`, `For`, `Switch` / `Match`, `Index`, `Dynamic`
- context: `create_context()`, `Provider`, `use_context()`
- stores: `create_store()` for immutable updates and `create_mutable()` for
  Solid-style mutable object state
- resources: `create_resource()` with `loading`, `error`, `state`, `mutate`, `refetch`
- lifecycle helpers: `create_effect()`, `on_mount()`, `on_cleanup()`
- `create_root()` and explicit disposal through the returned `Mount`

## Doc Topics

- [Context](docs/context.md): providers, typed context helpers, and forwarded children.
- [Control](docs/control.md): conditional rendering.
- [Reactive primitives](docs/reactive.md): signals, memos, effects, and owner cleanup.
- [Resources](docs/resources.md): worker-thread loading, refreshes, mutation, and status.
- [Scheduling](docs/scheduling.md): queueing work
- [Stores](docs/stores.md): state management
- [Style](docs/style.md): StyleX-ish style objects, merging, and component styling.
- [Widgets](docs/widgets.md): Tkinter primitives

## Examples

The runnable examples live in [examples](../examples/). Start with the
[examples README](../examples/README.md) for a short path through them.

## Strong Typing
To follow Solid's model of named args collected into reactive props, there is some brittle trickery.

In JS/TS land, there's tons of tooling around jsx/tsx. Python doesn't have that.<br>What it *does* have are .pyi files. We can define parameter transformations that type checkers can't inspect and then give them the publc facing API with a wink and a smile. The problem is generating those .pyi files.

The beginning of solving that problem is the `@component` decorator. In addition to transforming functions into rendered nodes, is also a syntax marker that can be inspected. 

The next bit stub-genning; basically a build step. Files in the working directory are scanned for component declarations and a corresponding `.pyi` file is generated, unrolling the typed prop object into a function signature.

This process can be manual with `uv run solid-tk stubs .`, or you can run a watcher to do it live with `uv run solid-tk watch` (it might be brittle though).

This bit is honestly harder and more involved than the actual framework.

## Design Notes

`create_signal()` returns an accessor and a mutator:

```python
from solid_tk.reactive import create_signal
count, set_count = create_signal(0)
count()
set_count(lambda value: value + 1)
```

The accessor is still compatible with `reaktiv` signals, so widgets can bind to
it directly. Writable widgets such as `tk.Entry(value=..., on_input=...)` receive
the accessor and mutator separately.

`Component.__new__` returns a renderable node to keep the class API simple

```python
Counter(title="Solid TK")
```

Inside a component, `self.props.title()` reads a reaktiv signal. This is
intentionally accessor-oriented.

Existing signals are preserved, while plain values and callbacks are wrapped as
signal values. Tk widget props use one additional convention: callable non-event
props are treated as reactive bindings, and event props such as `on_click` /
`command` are passed through as callbacks.

```python
tk.Label(text=f"{count()}")                  # snapshot now
tk.Label(text=count)                         # reactive signal value
tk.Label(text=lambda: f"{count()}")          # reactive derived expression
```

That means a component prop can be read inside a derived expression:

```python
tk.Label(text=lambda: f"Hello {self.props.name()}")
```

or forwarded directly to a widget prop:

```python
tk.Label(text=self.props.name)
```

Component children are also collected into `props.children`, so container-like
components can feel like Solid components instead of manually passing a
`children=` prop:

```python
@component
def panel(props):
    return tk.VStack(
        tk.Label(text=props.title),
        props.children(),
        padding=8,
    )

panel(tk.Label(text="Nested"), title="Details")
```

Control-flow nodes and `Fragment(...)` are transparent to layout. They produce
children; the parent widget or layout helper decides where those children go:

```python
@component
def rows(props):
    return For(props.items, lambda item: tk.Label(text=item), key=lambda item: item)

tk.VStack(
    tk.Label(text="Before"),
    rows(items=todos),
    tk.Label(text="After"),
)
```

In that example, the repeated labels are laid out by `VStack` between
`Before` and `After`; `For` and the component do not create wrapper frames.

## Benchmarks

To estimate framework overhead without needing a display server, run the fake-Tk
benchmark:

```sh
uv run python benchmarks/bench_overhead.py
```

It compares raw Tk-style widget creation with solid-tk mounting for static
labels, reactive label props, and a component wrapper. The most useful line is
the reported extra microseconds per widget, because native Tk/Tcl startup and
platform display behavior are intentionally excluded.
