# solid-tk

A small SolidJS-inspired runtime for Tkinter using
[reaktiv](https://pypi.org/project/reaktiv/) for fine-grained signals.

This is currently a prototype that I hope makes Tkinter more fun

```python
from typing import Protocol

from solid_tk import component
from solid_tk.reactive import Accessor
from solid_tk.reactive import Mutator
from solid_tk.reactive import create_signal
from solid_tk.runtime import create_root
from solid_tk.control import For
from solid_tk.control import Show
from solid_tk.widgets import Button
from solid_tk.widgets import Label
from solid_tk.widgets import HStack
from solid_tk.widgets import VStack


class CounterProps(Protocol):
    label: Accessor[str]
    count: Accessor[int]
    set_count: Mutator[int]


@component
def counter(props: CounterProps):
    todos, set_todos = create_signal(["wire props", "own effects", "dispose cleanly"])

    return VStack(
        Label(text=lambda: f"{props.label()}: {props.count()}"),
        Button(text="Increment", on_click=lambda: props.set_count(lambda n: n + 1)),
        Show(
            lambda: props.count() % 2 == 0,
            lambda: Label(text="Even"),
            fallback=lambda: Label(text="Odd"),
        ),
        For(todos, lambda item: Label(text=item), key=lambda item: item),
        HStack(
            Button(text="-", on_click=lambda: set_todos(lambda items: items[:-1])),
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
it directly. Writable widgets such as `Entry(value=..., on_input=...)` receive
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
Label(text=f"{count()}")                  # snapshot now
Label(text=count)                         # reactive signal value
Label(text=lambda: f"{count()}")          # reactive derived expression
```

That means a component prop can be read inside a derived expression:

```python
Label(text=lambda: f"Hello {self.props.name()}")
```

or forwarded directly to a widget prop:

```python
Label(text=self.props.name)
```


## What's Here So Far

- Functional components using `@component` decorator
- `Component` with `__init__()/setup()` and `render()`
- `Props`, where every attribute is an accessor
- widgets: `Tk`, `Frame`, `Label`, `Button`, `Entry`, `Checkbutton`
- stack layout helpers: `VStack`, `HStack`, `Item`
- StyleX-ish style objects with `style.define()`, `style.merge()`, and
  `style.component()`
- some control flow: `Show`, `For`, `Switch` / `Match`, `Index`, `Dynamic`
- context: `create_context()`, `Provider`, `use_context()`
- resources: `create_resource()` with `loading`, `error`, `state`, `mutate`, `refetch`
- lifecycle helpers: `create_effect()`, `on_mount()`, `on_cleanup()`
- `create_root()` and explicit disposal through the returned `Mount`

```python
Switch(
    Match(lambda: status() == "ready", lambda: Label(text="Ready")),
    Match(lambda: status() == "busy", lambda: Label(text="Working")),
    fallback=lambda: Label(text="Idle"),
)

Index(items, lambda item, index: Label(text=lambda: f"{index}: {item()}"))
Dynamic(selected_component, title="Hello")
```

See `examples/layout_demo` for stack spacing, padding, alignment, per-child
layout overrides, and importable style definitions:

```sh
python -m examples.layout_demo
```

See `docs/style.md` for the style helper conventions.

See `examples/control_demo` for a runnable version:

```sh
python -m examples.control_demo
```

`ErrorBoundary` catches render and reactive update errors in its child subtree
and can retry from a fallback:

```sh
python -m examples.error_boundary_demo
```

- event-loop helpers: `after`, `interval`, `defer`, `to_ui`

```python
after(500, lambda: set_status("half a second later"))
interval(1000, lambda: set_count(lambda value: value + 1))
defer(lambda: print("runs on the next Tk event loop turn"))

dispatch = to_ui()
dispatch(lambda: set_status("called from another thread"))
```

Scheduled callbacks are owned and cancelled automatically when their component
or root is disposed. Keep interval callbacks small; Tk runs UI work on one event
loop, so slow callbacks still block the interface.

See `examples/scheduler_demo` for moving labels and a worker-thread callback:

```sh
python -m examples.scheduler_demo
```

Resources run blocking work on a worker thread and publish the result back to
Tk through the owner scheduler. If a newer request starts before an older one
finishes, the older result is ignored; the worker thread itself is not forcibly
cancelled.

```python
image, (mutate, refetch) = create_resource(fetch_image, None, image_url)

Label(text=lambda: "Loading..." if image.loading() else image.state())
Button(text="Retry", on_click=lambda: refetch("button"))
```

See `docs/resources.md` for the API reference and `examples/resource_demo` for
a runnable image-loading demo with progress updates.

This is not a full Tkinter framework yet; more goodies to implement!

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

## Why Tk?
I keep reaching for it every time I want a small UI at work and I keep getting bogged down in abstractions I think are loose but turn out to be more tightly-coupled than I realize. Imperatively updating state is also a chore and makes for widgets with lots of clunky helpers, and I find widget vars unwieldy. My most recent attempt I threw `reaktiv` at the problem and was surprised at how streamlined it made my widgets. I felt it could be more. So here we are.
