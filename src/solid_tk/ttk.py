from __future__ import annotations

from tkinter import ttk
from typing import Any
from typing import Unpack

from . import style as style_api
from .nodes import NumericValueWidgetNode
from .nodes import ValueWidgetNode
from .nodes import WidgetNode
from .nodes import consume_layout
from .tk_props import TtkButtonProps
from .tk_props import TtkCheckbuttonProps
from .tk_props import TtkComboboxProps
from .tk_props import TtkEntryProps
from .tk_props import TtkFrameProps
from .tk_props import TtkLabeledScaleProps
from .tk_props import TtkLabelFrameProps
from .tk_props import TtkLabelProps
from .tk_props import TtkMenubuttonProps
from .tk_props import TtkNotebookProps
from .tk_props import TtkOptionMenuProps
from .tk_props import TtkPanedWindowProps
from .tk_props import TtkProgressbarProps
from .tk_props import TtkRadiobuttonProps
from .tk_props import TtkScaleProps
from .tk_props import TtkScrollbarProps
from .tk_props import TtkSeparatorProps
from .tk_props import TtkSizegripProps
from .tk_props import TtkSpinboxProps
from .tk_props import TtkTreeviewProps

LAYOUT_KEYS = {"pack", "grid", "place"}
TTK_STYLE_NAMES: dict[str, str] = {
    "Button": "TButton",
    "Checkbutton": "TCheckbutton",
    "Combobox": "TCombobox",
    "Entry": "TEntry",
    "Frame": "TFrame",
    "LabeledScale": "Horizontal.TScale",
    "LabelFrame": "TLabelframe",
    "Label": "TLabel",
    "Menubutton": "TMenubutton",
    "Notebook": "TNotebook",
    "OptionMenu": "TMenubutton",
    "PanedWindow": "TPanedwindow",
    "Progressbar": "Horizontal.TProgressbar",
    "Radiobutton": "TRadiobutton",
    "Scale": "Horizontal.TScale",
    "Scrollbar": "Vertical.TScrollbar",
    "Separator": "TSeparator",
    "Sizegrip": "TSizegrip",
    "Spinbox": "TSpinbox",
    "Treeview": "Treeview",
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


def Radiobutton(*children: Any, **props: Unpack[TtkRadiobuttonProps]) -> WidgetNode:
    apply_style(props, widget="Radiobutton")
    layout = consume_layout(props)
    return WidgetNode(ttk.Radiobutton, children=children, layout=layout, **props)


def Scale(*children: Any, **props: Unpack[TtkScaleProps]) -> WidgetNode:
    apply_style(props, widget="Scale")
    layout = consume_layout(props)
    return NumericValueWidgetNode(ttk.Scale, children=children, layout=layout, **props)


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


def LabelFrame(*children: Any, **props: Unpack[TtkLabelFrameProps]) -> WidgetNode:
    apply_style(props, widget="LabelFrame")
    layout = consume_layout(props)
    return WidgetNode(ttk.LabelFrame, children=children, layout=layout, **props)


Labelframe = LabelFrame


def LabeledScale(*children: Any, **props: Unpack[TtkLabeledScaleProps]) -> WidgetNode:
    apply_style(props, widget="LabeledScale")
    layout = consume_layout(props)
    return WidgetNode(ttk.LabeledScale, children=children, layout=layout, **props)


def Menubutton(*children: Any, **props: Unpack[TtkMenubuttonProps]) -> WidgetNode:
    apply_style(props, widget="Menubutton")
    layout = consume_layout(props)
    return WidgetNode(ttk.Menubutton, children=children, layout=layout, **props)


def Notebook(*children: Any, **props: Unpack[TtkNotebookProps]) -> WidgetNode:
    apply_style(props, widget="Notebook")
    layout = consume_layout(props)
    return WidgetNode(ttk.Notebook, children=children, layout=layout, **props)


def OptionMenu(*children: Any, **props: Unpack[TtkOptionMenuProps]) -> WidgetNode:
    apply_style(props, widget="OptionMenu")
    layout = consume_layout(props)
    return WidgetNode(
        option_menu_factory,
        children=children,
        layout=layout,
        **props,
    )


def PanedWindow(*children: Any, **props: Unpack[TtkPanedWindowProps]) -> WidgetNode:
    apply_style(props, widget="PanedWindow")
    layout = consume_layout(props)
    return WidgetNode(ttk.PanedWindow, children=children, layout=layout, **props)


Panedwindow = PanedWindow


def Scrollbar(*children: Any, **props: Unpack[TtkScrollbarProps]) -> WidgetNode:
    apply_style(props, widget="Scrollbar")
    layout = consume_layout(props)
    return WidgetNode(ttk.Scrollbar, children=children, layout=layout, **props)


def Sizegrip(*children: Any, **props: Unpack[TtkSizegripProps]) -> WidgetNode:
    apply_style(props, widget="Sizegrip")
    layout = consume_layout(props)
    return WidgetNode(ttk.Sizegrip, children=children, layout=layout, **props)


def Spinbox(*children: Any, **props: Unpack[TtkSpinboxProps]) -> WidgetNode:
    apply_style(props, widget="Spinbox")
    layout = consume_layout(props)
    return ValueWidgetNode(ttk.Spinbox, children=children, layout=layout, **props)


def Treeview(*children: Any, **props: Unpack[TtkTreeviewProps]) -> WidgetNode:
    apply_style(props, widget="Treeview")
    layout = consume_layout(props)
    return WidgetNode(ttk.Treeview, children=children, layout=layout, **props)


def option_menu_factory(parent: Any | None, **props: Any) -> Any:
    variable = props.pop("variable")
    values = list(props.pop("values", ()))
    default = props.pop("default", values[0] if values else None)
    return ttk.OptionMenu(parent, variable, default, *values, **props)


def apply_style(props: Any, *, widget: str) -> None:
    styled = props.pop("style", None)
    if styled is None:
        return
    if isinstance(styled, str):
        props["style"] = styled
        return

    style = style_api.merged_style(styled)
    style_props = style.props()
    style_api.reject_layout_props(style_props)

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
    "LabeledScale",
    "LabelFrame",
    "Labelframe",
    "Label",
    "Menubutton",
    "Notebook",
    "OptionMenu",
    "PanedWindow",
    "Panedwindow",
    "Progressbar",
    "Radiobutton",
    "Scale",
    "Scrollbar",
    "Separator",
    "Sizegrip",
    "Spinbox",
    "Treeview",
]
