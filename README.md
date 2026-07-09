# solid-tk

A small SolidJS-inspired runtime for Tkinter using
[reaktiv](https://pypi.org/project/reaktiv/) for fine-grained signals.

This is currently a prototype that I hope makes Tkinter more fun

```python
from typing import Protocol

from reaktiv import Signal

from solid_tk import Accessor
from solid_tk import Button
from solid_tk import For
from solid_tk import HStack
from solid_tk import Label
from solid_tk import Show
from solid_tk import SignalLike
from solid_tk import VStack
from solid_tk import component


class CounterProps(Protocol):
    label: Accessor[str]
    initial: SignalLike[int]


@component
def counter(props: CounterProps):
    count = props.initial
    todos = Signal(["wire props", "own effects", "dispose cleanly"])

    return VStack(
        Label(text=lambda: f"{props.label()}: {count()}"),
        Button(text="Increment", on_click=lambda: count.update(lambda n: n + 1)),
        Show(
            lambda: count() % 2 == 0,
            lambda: Label(text="Even"),
            fallback=lambda: Label(text="Odd"),
        ),
        For(todos, lambda item: Label(text=item), key=lambda item: item),
        HStack(Button(text="-", on_click=lambda: todos.set(todos()[:-1]))),
        padx=12,
        pady=12,
    )

mount = create_root(lambda: counter(label="Solid TK", initial=Signal(0)),title="Solid TK")
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

I did not think that hard about using `Signals` as-is instead of wrapping them in hooks returning accessor/mutator pairs. Some helper methods could be put around them to make it more solid-like, but it seems fine.

`Component.__new__` returns a renderable node to keep the class API simple

```python
Counter(title="Solid TK")
```

Inside a component, `self.props.title()` reads a reaktiv signal. This is
intentionally accessor-oriented: unlike Solid's `props.name` property access,
`solid-tk` keeps component props consistent with `reaktiv` signals and computed
values, which are called to read.

Existing signals are preserved, while plain values and callbacks are wrapped as
signal values. Tk widget props use one additional convention: callable non-event
props are treated as reactive bindings, and event props such as `on_click` /
`command` are passed through as callbacks.

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
- `Props`, where every attribute is a `Signal`
- widgets: `Tk`, `Frame`, `Label`, `Button`, `Entry`, `Checkbutton`
- some layout helpers: `VStack`, `HStack`
- some control flow: `Show`, `For`, `Switch` / `Match`, `Index`, `Dynamic`
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

See `examples/control_demo` for a runnable version:

```sh
python -m examples.control_demo
```
```

This is not a full Tkinter framework yet; more goodies to implement!

## Why Tk?
I keep reaching for it every time I want a small UI at work and I keep getting bogged down in abstractions I think are loose but turn out to be more tightly-coupled than I realize. Imperatively updating state is also a chore and makes for widgets with lots of clunky helpers, and I find widget vars unwieldy. My most recent attempt I threw `reaktiv` at the problem and was surprised at how streamlined it made my widgets. I felt it could be more. So here we are.