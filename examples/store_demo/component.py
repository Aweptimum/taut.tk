from __future__ import annotations

from dataclasses import dataclass

from solid_tk import component
from solid_tk.reactive import create_memo
from solid_tk.stores import create_store
from solid_tk.stores import produce
from solid_tk.stores import reconcile
from solid_tk.stores import unwrap
from solid_tk.widgets import Button
from solid_tk.widgets import HStack
from solid_tk.widgets import Label
from solid_tk.widgets import VStack


@dataclass(frozen=True)
class User:
    name: str
    role: str


@dataclass(frozen=True)
class AppState:
    user: User
    todos: list[str]
    selected: int


INITIAL = AppState(
    user=User(name="Ada", role="Engineer"),
    todos=["wire props", "own effects"],
    selected=0,
)

PRESET = AppState(
    user=User(name="Grace", role="Compiler enjoyer"),
    todos=["ship stores", "write docs", "drink water"],
    selected=1,
)


@component
def store_demo(props):
    state, set_state = create_store(INITIAL)
    name = set_state.at("user", "name")
    selected = set_state.at("selected")
    selected_todo = create_memo(lambda: state().todos[state().selected])

    def cycle_name() -> None:
        name.update(lambda current: "Grace" if current == "Ada" else "Ada")

    def add_todo() -> None:
        next_index = len(state().todos) + 1
        set_state(
            produce(
                lambda draft: draft.todos.append(f"store task {next_index}"),
            )
        )

    def select_next() -> None:
        selected.update(lambda index: (index + 1) % len(state().todos))

    return VStack(
        Label(text=lambda: f"{state().user.name} - {state().user.role}"),
        Label(text=lambda: f"Selected: {selected_todo()}"),
        Label(text=lambda: f"Todos: {', '.join(state().todos)}"),
        HStack(
            Button(text="Name Lens", on_click=cycle_name),
            Button(text="Produce Todo", on_click=add_todo),
            Button(text="Next", on_click=select_next),
            Button(text="Reconcile", on_click=lambda: set_state(reconcile(PRESET))),
            Button(text="Reset", on_click=lambda: set_state(INITIAL)),
        ),
        Label(text=lambda: f"Unwrapped: {unwrap(state)}"),
        padx=12,
        pady=12,
    )
