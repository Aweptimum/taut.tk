from __future__ import annotations

from dataclasses import dataclass

from solid_tk import component
from solid_tk.context import Provider
from solid_tk.context import create_context
from solid_tk.context import use_context
from solid_tk.reactive import create_signal
from solid_tk.widgets import Button
from solid_tk.widgets import HStack
from solid_tk.widgets import Label
from solid_tk.widgets import VStack


@dataclass(frozen=True)
class Theme:
    name: str
    background: str
    foreground: str
    accent: str


LIGHT = Theme(
    name="Light",
    background="#f5f5f0",
    foreground="#1f2933",
    accent="#1d6f8f",
)
DARK = Theme(
    name="Dark",
    background="#202124",
    foreground="#f1f5f9",
    accent="#7dd3fc",
)
CONTRAST = Theme(
    name="Contrast",
    background="#101010",
    foreground="#ffffff",
    accent="#ffd400",
)

theme_context = create_context(lambda: LIGHT)


@component
def themed_label(props):
    theme = use_context(theme_context)
    return Label(
        text=props.text,
        bg=lambda: theme().background,
        fg=lambda: theme().foreground,
        padx=8,
        pady=4,
    )


@component
def themed_button(props):
    theme = use_context(theme_context)
    return Button(
        text=props.text,
        on_click=props.on_click,
        bg=lambda: theme().accent,
        fg=lambda: theme().foreground,
        padx=8,
        pady=4,
    )


@component
def panel(props):
    theme = use_context(theme_context)
    return VStack(
        themed_label(text=lambda: f"Current theme: {theme().name}"),
        themed_label(text="Children read this without receiving it as a prop."),
        props.children(),
        bg=lambda: theme().background,
        padx=12,
        pady=12,
    )


@component
def preview(props):
    return Provider(
        theme_context,
        lambda: CONTRAST,
        lambda: panel(
            children=themed_label(
                text="This nested Provider shadows the app theme.",
            ),
        ),
    )


@component
def context_demo(props):
    selected, set_selected = create_signal(LIGHT)

    return Provider(
        theme_context,
        selected,
        lambda: panel(
            children=VStack(
                HStack(
                    themed_button(text="Light", on_click=lambda: set_selected(LIGHT)),
                    themed_button(text="Dark", on_click=lambda: set_selected(DARK)),
                    themed_button(
                        text="Contrast",
                        on_click=lambda: set_selected(CONTRAST),
                    ),
                ),
                preview(),
            ),
        ),
    )
