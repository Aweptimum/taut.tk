from __future__ import annotations

from collections.abc import Callable
from typing import Any
from typing import Literal
from typing import TypeAlias
from typing import TypedDict
from typing import TypeVar

from .reactive import Accessor
from .reactive import Mutator

T = TypeVar("T")

Reactive: TypeAlias = T | Accessor[T] | Callable[[], T]
Command: TypeAlias = Callable[[], Any]
Side: TypeAlias = Literal["left", "right", "top", "bottom"]
Anchor: TypeAlias = Literal[
    "n",
    "ne",
    "e",
    "se",
    "s",
    "sw",
    "w",
    "nw",
    "center",
]
Fill: TypeAlias = Literal["none", "x", "y", "both"]
Relief: TypeAlias = Literal["flat", "groove", "raised", "ridge", "solid", "sunken"]
Justify: TypeAlias = Literal["left", "center", "right"]
State: TypeAlias = Literal["normal", "active", "disabled"]
StackAlign: TypeAlias = Literal["start", "center", "end", "stretch"]
Padding: TypeAlias = int | tuple[int, int]


class PackOptions(TypedDict, total=False):
    after: Any
    anchor: Anchor
    before: Any
    expand: bool
    fill: Fill
    in_: Any
    ipadx: int
    ipady: int
    padx: int | tuple[int, int]
    pady: int | tuple[int, int]
    side: Side


class GridOptions(TypedDict, total=False):
    column: int
    columnspan: int
    in_: Any
    ipadx: int
    ipady: int
    padx: int | tuple[int, int]
    pady: int | tuple[int, int]
    row: int
    rowspan: int
    sticky: str


class PlaceOptions(TypedDict, total=False):
    anchor: Anchor
    bordermode: Literal["inside", "outside", "ignore"]
    height: int
    in_: Any
    relheight: float
    relwidth: float
    relx: float
    rely: float
    width: int
    x: int
    y: int


class LayoutProps(TypedDict, total=False):
    pack: PackOptions
    grid: GridOptions
    place: PlaceOptions


class BaseWidgetProps(LayoutProps, total=False):
    style: Any
    background: Reactive[str]
    bg: Reactive[str]
    borderwidth: Reactive[int]
    bd: Reactive[int]
    cursor: Reactive[str]
    foreground: Reactive[str]
    fg: Reactive[str]
    height: Reactive[int]
    highlightbackground: Reactive[str]
    highlightcolor: Reactive[str]
    highlightthickness: Reactive[int]
    padx: Reactive[int]
    pady: Reactive[int]
    relief: Reactive[Relief]
    takefocus: Reactive[bool | str]
    width: Reactive[int]


class TextWidgetProps(BaseWidgetProps, total=False):
    anchor: Reactive[Anchor]
    font: Reactive[str | tuple[Any, ...]]
    image: Reactive[Any]
    justify: Reactive[Justify]
    text: Reactive[str]
    textvariable: Reactive[Any]
    underline: Reactive[int]
    wraplength: Reactive[int]


class FrameProps(BaseWidgetProps, total=False):
    class_: Reactive[str]
    colormap: Reactive[str]
    container: Reactive[bool]
    visual: Reactive[str]


class LabelProps(TextWidgetProps, total=False):
    bitmap: Reactive[str]
    compound: Reactive[str]


class ButtonProps(TextWidgetProps, total=False):
    activebackground: Reactive[str]
    activeforeground: Reactive[str]
    command: Command
    compound: Reactive[str]
    default: Reactive[Literal["normal", "active", "disabled"]]
    disabledforeground: Reactive[str]
    on_click: Command
    overrelief: Reactive[Relief]
    repeatdelay: Reactive[int]
    repeatinterval: Reactive[int]
    state: Reactive[State]


class EntryProps(BaseWidgetProps, total=False):
    disabledbackground: Reactive[str]
    disabledforeground: Reactive[str]
    exportselection: Reactive[bool]
    font: Reactive[str | tuple[Any, ...]]
    insertbackground: Reactive[str]
    insertborderwidth: Reactive[int]
    insertofftime: Reactive[int]
    insertontime: Reactive[int]
    insertwidth: Reactive[int]
    invalidcommand: Command
    justify: Reactive[Justify]
    readonlybackground: Reactive[str]
    selectbackground: Reactive[str]
    selectborderwidth: Reactive[int]
    selectforeground: Reactive[str]
    show: Reactive[str]
    state: Reactive[State | Literal["readonly"]]
    textvariable: Reactive[Any]
    validate: Reactive[str]
    validatecommand: Command
    value: Reactive[str]
    on_input: Mutator[str]
    xscrollcommand: Command


class CheckbuttonProps(ButtonProps, total=False):
    indicatoron: Reactive[bool]
    offvalue: Reactive[Any]
    onvalue: Reactive[Any]
    selectcolor: Reactive[str]
    selectimage: Reactive[Any]
    variable: Reactive[Any]


class TtkBaseProps(LayoutProps, total=False):
    class_: Reactive[str]
    cursor: Reactive[str]
    style: Any
    takefocus: Reactive[bool | str]


class TtkFrameProps(TtkBaseProps, total=False):
    borderwidth: Reactive[int]
    height: Reactive[int]
    padding: Reactive[int | tuple[int, ...] | str]
    relief: Reactive[Relief]
    width: Reactive[int]


class TtkTextProps(TtkBaseProps, total=False):
    compound: Reactive[str]
    image: Reactive[Any]
    text: Reactive[str]
    textvariable: Reactive[Any]
    underline: Reactive[int]
    width: Reactive[int]


class TtkLabelProps(TtkTextProps, total=False):
    anchor: Reactive[Anchor]
    background: Reactive[str]
    font: Reactive[str | tuple[Any, ...]]
    foreground: Reactive[str]
    justify: Reactive[Justify]
    padding: Reactive[int | tuple[int, ...] | str]
    relief: Reactive[Relief]
    wraplength: Reactive[int]


class TtkButtonProps(TtkTextProps, total=False):
    command: Command
    default: Reactive[Literal["normal", "active", "disabled"]]
    on_click: Command
    state: Reactive[State]


class TtkEntryProps(TtkBaseProps, total=False):
    exportselection: Reactive[bool]
    font: Reactive[str | tuple[Any, ...]]
    invalidcommand: Command
    justify: Reactive[Justify]
    show: Reactive[str]
    state: Reactive[State | Literal["readonly"]]
    textvariable: Reactive[Any]
    validate: Reactive[str]
    validatecommand: Command
    value: Reactive[str]
    on_input: Mutator[str]
    width: Reactive[int]
    xscrollcommand: Command


class TtkCheckbuttonProps(TtkButtonProps, total=False):
    offvalue: Reactive[Any]
    onvalue: Reactive[Any]
    variable: Reactive[Any]


class TtkComboboxProps(TtkEntryProps, total=False):
    exportselection: Reactive[bool]
    height: Reactive[int]
    postcommand: Command
    values: Reactive[tuple[Any, ...] | list[Any]]


class TtkSeparatorProps(TtkBaseProps, total=False):
    orient: Reactive[Literal["horizontal", "vertical"]]


class TtkProgressbarProps(TtkBaseProps, total=False):
    length: Reactive[int]
    maximum: Reactive[float]
    mode: Reactive[Literal["determinate", "indeterminate"]]
    orient: Reactive[Literal["horizontal", "vertical"]]
    phase: Reactive[int]
    value: Reactive[float]
    variable: Reactive[Any]


class TkProps(TypedDict, total=False):
    style: Any
    title: Reactive[str]


class PortalProps(TypedDict, total=False):
    title: Reactive[str]
    on_close: Command


class StackProps(FrameProps, total=False):
    align: StackAlign
    fill: Fill
    gap: int
    grow: bool
    padding: Padding


class GridProps(FrameProps, total=False):
    columns: int
    gap: int
    padding: Padding
    sticky: str


class StackItemProps(TypedDict, total=False):
    style: Any
    align: StackAlign
    fill: Fill
    grow: bool
    pack: PackOptions


class StyleProps(GridProps, StackProps, total=False):
    style: Reactive[str]
    title: Reactive[str]
    anchor: Reactive[Anchor]
    font: Reactive[str | tuple[Any, ...]]
    image: Reactive[Any]
    justify: Reactive[Justify]
    text: Reactive[str]
    textvariable: Reactive[Any]
    underline: Reactive[int]
    wraplength: Reactive[int]
    bitmap: Reactive[str]
    compound: Reactive[str]
    activebackground: Reactive[str]
    activeforeground: Reactive[str]
    command: Command
    default: Reactive[Literal["normal", "active", "disabled"]]
    disabledforeground: Reactive[str]
    on_click: Command
    overrelief: Reactive[Relief]
    repeatdelay: Reactive[int]
    repeatinterval: Reactive[int]
    state: Reactive[State | Literal["readonly"]]
    disabledbackground: Reactive[str]
    exportselection: Reactive[bool]
    insertbackground: Reactive[str]
    insertborderwidth: Reactive[int]
    insertofftime: Reactive[int]
    insertontime: Reactive[int]
    insertwidth: Reactive[int]
    invalidcommand: Command
    readonlybackground: Reactive[str]
    selectbackground: Reactive[str]
    selectborderwidth: Reactive[int]
    selectforeground: Reactive[str]
    show: Reactive[str]
    validate: Reactive[str]
    validatecommand: Command
    value: Reactive[str]
    on_input: Mutator[str]
    xscrollcommand: Command
    indicatoron: Reactive[bool]
    offvalue: Reactive[Any]
    onvalue: Reactive[Any]
    selectcolor: Reactive[str]
    selectimage: Reactive[Any]
    variable: Reactive[Any]
    length: Reactive[int]
    maximum: Reactive[float]
    mode: Reactive[Literal["determinate", "indeterminate"]]
    orient: Reactive[Literal["horizontal", "vertical"]]
    phase: Reactive[int]
    values: Reactive[tuple[Any, ...] | list[Any]]
