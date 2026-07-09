from __future__ import annotations

from taut import component
from taut.control import Show
from taut.layout import HStack
from taut.layout import VStack
from taut.reactive import create_signal
from taut.tk import Button
from taut.tk import Label
from taut.tk import Portal


@component
def portal_demo(props):
    open_, set_open = create_signal(False)
    count, set_count = create_signal(0)

    def close() -> None:
        set_open(False)

    return VStack(
        Label(text="Portal demo"),
        Label(text=lambda: "Dialog is open" if open_() else "Dialog is closed"),
        HStack(
            Button(text="Open dialog", on_click=lambda: set_open(True)),
            Button(text="Increment title", on_click=lambda: set_count(lambda value: value + 1)),
        ),
        Show(
            open_,
            lambda: Portal(
                lambda: VStack(
                    Label(text="This content is mounted in a tk.Toplevel."),
                    Label(text=lambda: f"Counter: {count()}"),
                    HStack(
                        Button(
                            text="+",
                            on_click=lambda: set_count(lambda value: value + 1),
                        ),
                        Button(text="Close", on_click=close),
                    ),
                    padx=12,
                    pady=12,
                ),
                title=lambda: f"Portal Window {count()}",
                on_close=close,
            ),
        ),
        padx=12,
        pady=12,
    )
