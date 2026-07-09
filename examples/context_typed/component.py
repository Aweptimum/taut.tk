from __future__ import annotations

from dataclasses import dataclass

from solid_tk import component
from solid_tk.context import Provider
from solid_tk.context import create_context
from solid_tk.context import use_context
from solid_tk.layout import HStack
from solid_tk.layout import VStack
from solid_tk.reactive import Accessor
from solid_tk.reactive import Mutator
from solid_tk.reactive import create_signal
from solid_tk.tk import Button
from solid_tk.tk import Label

"""
Inspired by this:
https://gist.github.com/JLarky/a46055f673a2cb021db1a34449e3be07
"""


@dataclass(frozen=True)
class DarkContextValue:
    is_dark: Accessor[bool]
    set_is_dark: Mutator[bool]


dark_context = create_context(DarkContextValue)


def use_provider_value() -> DarkContextValue:
    is_dark, set_is_dark = create_signal(False)
    return DarkContextValue(is_dark=is_dark, set_is_dark=set_is_dark)


@component
def DarkProvider(props):
    value = use_provider_value()
    return Provider(dark_context, value, props.children)


def use_dark() -> DarkContextValue:
    value = use_context(dark_context)
    if value is None:
        raise RuntimeError("use_dark must be used within a DarkProvider")
    return value


def use_is_dark() -> Accessor[bool]:
    return use_dark().is_dark


def use_set_dark() -> Mutator[bool]:
    return use_dark().set_is_dark


@component
def DarkStatus(props):
    is_dark = use_is_dark()
    return Label(
        text=lambda: "Dark mode is on" if is_dark() else "Dark mode is off",
        bg=lambda: "#1f2933" if is_dark() else "#f8fafc",
        fg=lambda: "#f8fafc" if is_dark() else "#1f2933",
        padx=10,
        pady=6,
    )


@component
def DarkControls(props):
    set_dark = use_set_dark()
    return HStack(
        Button(text="Light", on_click=lambda: set_dark(False)),
        Button(text="Dark", on_click=lambda: set_dark(True)),
        Button(text="Toggle", on_click=lambda: set_dark(lambda dark: not dark)),
    )


@component
def DarkConsumer(props):
    return VStack(
        DarkStatus(),
        DarkControls(),
        padx=12,
        pady=12,
    )


@component
def dark_context_demo(props):
    return DarkProvider(lambda: DarkConsumer())
