from __future__ import annotations

from reaktiv import Signal

from solid_tk import Button
from solid_tk import Dynamic
from solid_tk import HStack
from solid_tk import Index
from solid_tk import Label
from solid_tk import Match
from solid_tk import Switch
from solid_tk import VStack
from solid_tk import component
from solid_tk import create_memo

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
    status = Signal("ready")
    detail_component = Signal(compact_detail)
    items = Signal(["Alpha", "Beta", "Gamma"])
    selected_item = create_memo(lambda: items()[0])

    def cycle_status() -> None:
        current = STATUSES.index(status())
        status.set(STATUSES[(current + 1) % len(STATUSES)])

    def rotate_items() -> None:
        current = items()
        items.set([*current[1:], current[0]])

    def rename_second() -> None:
        current = items()
        items.set([current[0], f"{current[1]}*", *current[2:]])

    def toggle_detail() -> None:
        detail_component.set(
            full_detail if detail_component() is compact_detail else compact_detail
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
