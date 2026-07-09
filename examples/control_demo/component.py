from __future__ import annotations

from taut import component
from taut.control import Dynamic
from taut.control import Index
from taut.control import Match
from taut.control import Switch
from taut.layout import HStack
from taut.layout import VStack
from taut.reactive import create_memo
from taut.reactive import create_signal
from taut.tk import Button
from taut.tk import Label

STATUSES = ("ready", "busy", "done")


@component
def compact_detail(props):
    return Label(
        text=lambda: f"Compact: {props.item()}",
        padx=8,
        pady=4,
    )


@component
def full_detail(props):
    return VStack(
        Label(text=lambda: f"Full detail for {props.item()}"),
        Label(text="Dynamic swaps this whole component when the mode changes."),
        padx=8,
        pady=4,
    )


@component
def control_demo(props):
    status, set_status = create_signal("ready")
    detail_component, set_detail_component = create_signal(compact_detail)
    items, set_items = create_signal(["Alpha", "Beta", "Gamma"])
    selected_item = create_memo(lambda: items()[0])

    def cycle_status() -> None:
        current = STATUSES.index(status())
        set_status(STATUSES[(current + 1) % len(STATUSES)])

    def rotate_items() -> None:
        current = items()
        set_items([*current[1:], current[0]])

    def rename_second() -> None:
        current = items()
        set_items([current[0], f"{current[1]}*", *current[2:]])

    def toggle_detail() -> None:
        next_detail = full_detail if detail_component() is compact_detail else compact_detail
        set_detail_component(
            lambda _: next_detail,
        )

    return VStack(
        Label(text="Control flow demo"),
        Switch(
            Match(lambda: status() == "ready", lambda: Label(text="Ready")),
            Match(lambda: status() == "busy", lambda: Label(text="Working")),
            Match(lambda: status() == "done", lambda: Label(text="Complete")),
            fallback=lambda: Label(text="Unknown"),
        ),
        HStack(
            Button(text="Cycle status", on_click=cycle_status),
            Button(text="Rotate list", on_click=rotate_items),
            Button(text="Rename second", on_click=rename_second),
            Button(text="Toggle detail", on_click=toggle_detail),
        ),
        Label(text="Index keeps row nodes stable while item accessors update."),
        Index(
            items,
            lambda item, index: HStack(
                Label(text=lambda: f"{index + 1}."),
                Label(text=item),
            ),
        ),
        Dynamic(detail_component, item=selected_item),
        padx=12,
        pady=12,
    )
