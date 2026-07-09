from __future__ import annotations

from dataclasses import dataclass

from reaktiv import Signal

from solid_tk import Accessor
from solid_tk import Button
from solid_tk import HStack
from solid_tk import Label
from solid_tk import Provider
from solid_tk import Setter
from solid_tk import SignalLike
from solid_tk import VStack
from solid_tk import component
from solid_tk import create_context
from solid_tk import use_context

"""
Inspired by this:
https://gist.github.com/JLarky/a46055f673a2cb021db1a34449e3be07
"""


@dataclass(frozen=True)
class DarkContextValue:
    is_dark: SignalLike[bool]
    set_is_dark: Setter[bool]


dark_context = create_context(DarkContextValue)


def use_provider_value() -> DarkContextValue:
    is_dark = Signal(False)
    return DarkContextValue(is_dark=is_dark, set_is_dark=is_dark.set)


@component
def DarkProvider(props):
    value = use_provider_value()
    return Provider(dark_context, value, props.children)


def use_dark() -> DarkContextValue:
    context = use_context(dark_context)
    if context is None:
        raise RuntimeError("use_dark must be used within a DarkProvider")
    return context


def use_is_dark() -> Accessor[bool]:
    return use_dark().is_dark


def use_set_dark() -> Setter[bool]:
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
    is_dark = use_is_dark()
    set_dark = use_set_dark()
    return HStack(
        Button(text="Light", on_click=lambda: set_dark(False)),
        Button(text="Dark", on_click=lambda: set_dark(True)),
        Button(text="Toggle", on_click=lambda: set_dark(not is_dark())),
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
    return DarkProvider(children=lambda: DarkConsumer())
