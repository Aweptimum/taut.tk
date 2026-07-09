from __future__ import annotations

from tkinter import ttk
from typing import Any
from typing import Unpack

from . import style as style_api
from .tk_props import TtkButtonProps
from .tk_props import TtkCheckbuttonProps
from .tk_props import TtkComboboxProps
from .tk_props import TtkEntryProps
from .tk_props import TtkFrameProps
from .tk_props import TtkLabelProps
from .tk_props import TtkProgressbarProps
from .tk_props import TtkSeparatorProps
from .widgets import ValueWidgetNode
from .widgets import WidgetNode
from .widgets import consume_layout

LAYOUT_KEYS = {"pack", "grid", "place"}
TTK_STYLE_NAMES: dict[str, str] = {
    "Button": "TButton",
    "Checkbutton": "TCheckbutton",
    "Combobox": "TCombobox",
    "Entry": "TEntry",
    "Frame": "TFrame",
    "Label": "TLabel",
    "Progressbar": "Horizontal.TProgressbar",
    "Separator": "TSeparator",
}
TTK_STYLE_ALIASES = {
    "bg": "background",
    "bd": "borderwidth",
    "fg": "foreground",
}
_configured_styles: set[tuple[str, tuple[tuple[str, Any], ...]]] = set()


def Frame(*children: Any, **props: Unpack[TtkFrameProps]) -> WidgetNode:
    apply_style(props, widget="Frame")
    layout = consume_layout(props)
    return WidgetNode(ttk.Frame, children=children, layout=layout, **props)


def Label(*children: Any, **props: Unpack[TtkLabelProps]) -> WidgetNode:
    apply_style(props, widget="Label")
    layout = consume_layout(props)
    return WidgetNode(ttk.Label, children=children, layout=layout, **props)


def Button(*children: Any, **props: Unpack[TtkButtonProps]) -> WidgetNode:
    apply_style(props, widget="Button")
    layout = consume_layout(props)
    return WidgetNode(ttk.Button, children=children, layout=layout, **props)


def Entry(*children: Any, **props: Unpack[TtkEntryProps]) -> WidgetNode:
    apply_style(props, widget="Entry")
    layout = consume_layout(props)
    return ValueWidgetNode(ttk.Entry, children=children, layout=layout, **props)


def Checkbutton(*children: Any, **props: Unpack[TtkCheckbuttonProps]) -> WidgetNode:
    apply_style(props, widget="Checkbutton")
    layout = consume_layout(props)
    return WidgetNode(ttk.Checkbutton, children=children, layout=layout, **props)


def Combobox(*children: Any, **props: Unpack[TtkComboboxProps]) -> WidgetNode:
    apply_style(props, widget="Combobox")
    layout = consume_layout(props)
    return ValueWidgetNode(ttk.Combobox, children=children, layout=layout, **props)


def Separator(*children: Any, **props: Unpack[TtkSeparatorProps]) -> WidgetNode:
    apply_style(props, widget="Separator")
    layout = consume_layout(props)
    return WidgetNode(ttk.Separator, children=children, layout=layout, **props)


def Progressbar(*children: Any, **props: Unpack[TtkProgressbarProps]) -> WidgetNode:
    apply_style(props, widget="Progressbar")
    layout = consume_layout(props)
    return WidgetNode(ttk.Progressbar, children=children, layout=layout, **props)


def apply_style(props: Any, *, widget: str) -> None:
    styled = props.pop("style", None)
    if styled is None:
        return
    if isinstance(styled, str):
        props["style"] = styled
        return

    style = style_api.merged_style(styled)
    style_props = style.props()
    layout_props = {key: style_props.pop(key) for key in LAYOUT_KEYS if key in style_props}
    for key, value in layout_props.items():
        props.setdefault(key, value)

    if style.name is None:
        props.update({key: value for key, value in style_props.items() if key not in props})
        return

    style_name = f"{style.name}.{TTK_STYLE_NAMES[widget]}"
    configure_style(style_name, style_props)
    props["style"] = style_name


def configure_style(name: str, props: dict[str, Any]) -> None:
    config = ttk_style_config(props)
    key = (name, tuple(sorted(config.items())))
    if key in _configured_styles:
        return
    ttk.Style().configure(name, **config)
    _configured_styles.add(key)


def ttk_style_config(props: dict[str, Any]) -> dict[str, Any]:
    config: dict[str, Any] = {}
    padding: list[Any | None] = [None, None]
    for key, value in props.items():
        if key == "padx":
            padding[0] = value
        elif key == "pady":
            padding[1] = value
        else:
            config[TTK_STYLE_ALIASES.get(key, key)] = value
    if padding != [None, None] and "padding" not in config:
        x, y = padding
        config["padding"] = x if y is None else (x if x is not None else 0, y)
    return config


__all__ = [
    "Button",
    "Checkbutton",
    "Combobox",
    "Entry",
    "Frame",
    "Label",
    "Progressbar",
    "Separator",
]
