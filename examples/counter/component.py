from __future__ import annotations

from typing import Protocol

from reaktiv import Signal

from solid_tk import Accessor
from solid_tk import Button
from solid_tk import Component
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


class Counter(Component[CounterProps]):
    def __init__(self, props: CounterProps) -> None:
        self.props = props
        self.count = props.initial
        self.todos = Signal(["wire props", "own effects", "dispose cleanly"])

    def render(self):
        return VStack(
            Label(text=lambda: f"{self.props.label()}: {self.count()}"),
            Button(
                text="Increment", on_click=lambda: self.count.update(lambda n: n + 1)
            ),
            Show(
                lambda: self.count() % 2 == 0,
                lambda: Label(text="Even"),
                fallback=lambda: Label(text="Odd"),
            ),
            For(self.todos, lambda item: Label(text=item), key=lambda item: item),
            HStack(
                Button(text="-", on_click=lambda: self.todos.set(self.todos()[:-1]))
            ),
            padx=12,
            pady=12,
        )


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
