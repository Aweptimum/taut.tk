from __future__ import annotations

from typing import Protocol

from solid_tk import Component
from solid_tk import component
from solid_tk.control import For
from solid_tk.control import Show
from solid_tk.reactive import Accessor
from solid_tk.reactive import Mutator
from solid_tk.reactive import create_signal
from solid_tk.widgets import Button
from solid_tk.widgets import HStack
from solid_tk.widgets import Label
from solid_tk.widgets import VStack


class CounterProps(Protocol):
    label: Accessor[str]
    count: Accessor[int]
    set_count: Mutator[int]


class Counter(Component[CounterProps]):
    def __init__(self, props: CounterProps) -> None:
        self.props = props
        self.count = props.count
        self.set_count = props.set_count
        self.todos, self.set_todos = create_signal(
            ["wire props", "own effects", "dispose cleanly"]
        )

    def render(self):
        return VStack(
            Label(text=lambda: f"{self.props.label()}: {self.count()}"),
            Button(text="Increment", on_click=lambda: self.set_count(self.count() + 1)),
            Show(
                lambda: self.count() % 2 == 0,
                lambda: Label(text="Even"),
                fallback=lambda: Label(text="Odd"),
            ),
            For(self.todos, lambda item: Label(text=item), key=lambda item: item),
            HStack(
                Button(
                    text="-",
                    on_click=lambda: self.set_todos(lambda todos: todos[:-1]),
                )
            ),
            padx=12,
            pady=12,
        )


@component
def counter(props: CounterProps):
    count = props.count
    set_count = props.set_count
    todos, set_todos = create_signal(["wire props", "own effects", "dispose cleanly"])

    return VStack(
        Label(text=lambda: f"{props.label()}: {count()}"),
        Button(text="Increment", on_click=lambda: set_count(count() + 1)),
        Show(
            lambda: count() % 2 == 0,
            lambda: Label(text="Even"),
            fallback=lambda: Label(text="Odd"),
        ),
        For(todos, lambda item: Label(text=item), key=lambda item: item),
        HStack(Button(text="-", on_click=lambda: set_todos(lambda todos: todos[:-1]))),
        padx=12,
        pady=12,
    )
