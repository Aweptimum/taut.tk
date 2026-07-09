from __future__ import annotations

from collections.abc import Callable
from collections.abc import Mapping
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
ValueCommand: TypeAlias = Callable[[Any], Any]
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
GridWeights: TypeAlias = tuple[int, ...] | list[int] | Mapping[int, int]


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


class RadiobuttonProps(CheckbuttonProps, total=False):
    tristatevalue: Reactive[Any]
    value: Reactive[Any]


class ScaleProps(BaseWidgetProps, total=False):
    activebackground: Reactive[str]
    bigincrement: Reactive[float]
    command: ValueCommand
    digits: Reactive[int]
    font: Reactive[str | tuple[Any, ...]]
    from_: Reactive[float]
    label: Reactive[str]
    length: Reactive[int]
    orient: Reactive[Literal["horizontal", "vertical"]]
    repeatdelay: Reactive[int]
    repeatinterval: Reactive[int]
    resolution: Reactive[float]
    showvalue: Reactive[bool]
    sliderlength: Reactive[int]
    sliderrelief: Reactive[Relief]
    state: Reactive[State]
    tickinterval: Reactive[float]
    to: Reactive[float]
    troughcolor: Reactive[str]
    value: Reactive[float]
    variable: Reactive[Any]
    on_input: Mutator[float]


class CanvasProps(BaseWidgetProps, total=False):
    closeenough: Reactive[float]
    confine: Reactive[bool]
    insertbackground: Reactive[str]
    insertborderwidth: Reactive[int]
    insertofftime: Reactive[int]
    insertontime: Reactive[int]
    insertwidth: Reactive[int]
    offset: Reactive[str]
    scrollregion: Reactive[tuple[int, int, int, int] | str]
    selectbackground: Reactive[str]
    selectborderwidth: Reactive[int]
    selectforeground: Reactive[str]
    state: Reactive[State]
    xscrollcommand: Command
    xscrollincrement: Reactive[int]
    yscrollcommand: Command
    yscrollincrement: Reactive[int]


class LabelFrameProps(FrameProps, total=False):
    font: Reactive[str | tuple[Any, ...]]
    foreground: Reactive[str]
    fg: Reactive[str]
    labelanchor: Reactive[Anchor]
    labelwidget: Reactive[Any]
    text: Reactive[str]


class ListboxProps(BaseWidgetProps, total=False):
    activestyle: Reactive[Literal["dotbox", "none", "underline"]]
    disabledforeground: Reactive[str]
    exportselection: Reactive[bool]
    font: Reactive[str | tuple[Any, ...]]
    listvariable: Reactive[Any]
    selectbackground: Reactive[str]
    selectborderwidth: Reactive[int]
    selectforeground: Reactive[str]
    selectmode: Reactive[Literal["single", "browse", "multiple", "extended"]]
    setgrid: Reactive[bool]
    state: Reactive[State]
    xscrollcommand: Callable[..., Any]
    yscrollcommand: Callable[..., Any]


class MenuProps(TypedDict, total=False):
    activebackground: Reactive[str]
    activeborderwidth: Reactive[int]
    activeforeground: Reactive[str]
    background: Reactive[str]
    bg: Reactive[str]
    borderwidth: Reactive[int]
    bd: Reactive[int]
    cursor: Reactive[str]
    disabledforeground: Reactive[str]
    font: Reactive[str | tuple[Any, ...]]
    foreground: Reactive[str]
    fg: Reactive[str]
    postcommand: Command
    relief: Reactive[Relief]
    selectcolor: Reactive[str]
    takefocus: Reactive[bool | str]
    tearoff: Reactive[bool]
    tearoffcommand: Callable[..., Any]
    title: Reactive[str]
    type: Reactive[Literal["menubar", "tearoff", "normal"]]


class MenubuttonProps(ButtonProps, total=False):
    direction: Reactive[Literal["above", "below", "left", "right", "flush"]]
    indicatoron: Reactive[bool]
    menu: Reactive[Any]


class MessageProps(TextWidgetProps, total=False):
    aspect: Reactive[int]


class OptionMenuProps(BaseWidgetProps, total=False):
    variable: Any
    value: Any
    values: tuple[Any, ...] | list[Any]
    command: Callable[[Any], Any]


class PanedWindowProps(BaseWidgetProps, total=False):
    handlepad: Reactive[int]
    handlesize: Reactive[int]
    opaqueresize: Reactive[bool]
    orient: Reactive[Literal["horizontal", "vertical"]]
    proxybackground: Reactive[str]
    proxyborderwidth: Reactive[int]
    proxyrelief: Reactive[Relief]
    sashcursor: Reactive[str]
    sashpad: Reactive[int]
    sashrelief: Reactive[Relief]
    sashwidth: Reactive[int]
    showhandle: Reactive[bool]


class ScrollbarProps(BaseWidgetProps, total=False):
    activebackground: Reactive[str]
    activerelief: Reactive[Relief]
    command: Callable[..., Any]
    elementborderwidth: Reactive[int]
    jump: Reactive[bool]
    orient: Reactive[Literal["horizontal", "vertical"]]
    repeatdelay: Reactive[int]
    repeatinterval: Reactive[int]
    troughcolor: Reactive[str]


class SpinboxProps(EntryProps, total=False):
    buttonbackground: Reactive[str]
    buttoncursor: Reactive[str]
    buttondownrelief: Reactive[Relief]
    buttonuprelief: Reactive[Relief]
    command: Command
    disabledbackground: Reactive[str]
    format: Reactive[str]
    from_: Reactive[float]
    increment: Reactive[float]
    readonlybackground: Reactive[str]
    to: Reactive[float]
    values: Reactive[tuple[Any, ...] | list[Any]]
    wrap: Reactive[bool]


class TextProps(BaseWidgetProps, total=False):
    autoseparators: Reactive[bool]
    blockcursor: Reactive[bool]
    endline: Reactive[int]
    exportselection: Reactive[bool]
    font: Reactive[str | tuple[Any, ...]]
    inactiveselectbackground: Reactive[str]
    insertbackground: Reactive[str]
    insertborderwidth: Reactive[int]
    insertofftime: Reactive[int]
    insertontime: Reactive[int]
    insertunfocussed: Reactive[str]
    insertwidth: Reactive[int]
    maxundo: Reactive[int]
    padx: Reactive[int]
    pady: Reactive[int]
    selectbackground: Reactive[str]
    selectborderwidth: Reactive[int]
    selectforeground: Reactive[str]
    setgrid: Reactive[bool]
    spacing1: Reactive[int]
    spacing2: Reactive[int]
    spacing3: Reactive[int]
    startline: Reactive[int]
    state: Reactive[State]
    tabs: Reactive[Any]
    tabstyle: Reactive[Literal["tabular", "wordprocessor"]]
    undo: Reactive[bool]
    wrap: Reactive[Literal["char", "none", "word"]]
    xscrollcommand: Callable[..., Any]
    yscrollcommand: Callable[..., Any]


class PhotoImageProps(TypedDict, total=False):
    data: Any
    file: str
    format: str
    gamma: float
    height: int
    master: Any
    name: str
    palette: Any
    width: int


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


class TtkRadiobuttonProps(TtkCheckbuttonProps, total=False):
    value: Reactive[Any]


class TtkScaleProps(TtkBaseProps, total=False):
    command: ValueCommand
    from_: Reactive[float]
    length: Reactive[int]
    orient: Reactive[Literal["horizontal", "vertical"]]
    state: Reactive[State | Literal["readonly"]]
    to: Reactive[float]
    value: Reactive[float]
    variable: Reactive[Any]
    on_input: Mutator[float]


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


class TtkLabelFrameProps(TtkFrameProps, total=False):
    labelanchor: Reactive[Anchor]
    labelwidget: Reactive[Any]
    text: Reactive[str]
    underline: Reactive[int]


class TtkLabeledScaleProps(TtkFrameProps, total=False):
    compound: Reactive[str]
    from_: Reactive[float]
    to: Reactive[float]
    variable: Reactive[Any]


class TtkMenubuttonProps(TtkTextProps, total=False):
    direction: Reactive[Literal["above", "below", "left", "right", "flush"]]
    menu: Reactive[Any]
    state: Reactive[State]


class TtkNotebookProps(TtkBaseProps, total=False):
    height: Reactive[int]
    padding: Reactive[int | tuple[int, ...] | str]
    width: Reactive[int]


class TtkOptionMenuProps(TtkBaseProps, total=False):
    variable: Any
    default: Any
    values: tuple[Any, ...] | list[Any]
    command: Callable[[Any], Any]
    direction: Reactive[Literal["above", "below", "left", "right", "flush"]]


class TtkPanedWindowProps(TtkBaseProps, total=False):
    height: Reactive[int]
    orient: Reactive[Literal["horizontal", "vertical"]]
    width: Reactive[int]


class TtkScrollbarProps(TtkBaseProps, total=False):
    command: Callable[..., Any]
    orient: Reactive[Literal["horizontal", "vertical"]]


class TtkSizegripProps(TtkBaseProps, total=False):
    pass


class TtkSpinboxProps(TtkEntryProps, total=False):
    command: Command
    format: Reactive[str]
    from_: Reactive[float]
    increment: Reactive[float]
    to: Reactive[float]
    values: Reactive[tuple[Any, ...] | list[Any]]
    wrap: Reactive[bool]


class TtkTreeviewProps(TtkBaseProps, total=False):
    columns: Reactive[tuple[Any, ...] | list[Any] | str]
    displaycolumns: Reactive[tuple[Any, ...] | list[Any] | str]
    height: Reactive[int]
    padding: Reactive[int | tuple[int, ...] | str]
    selectmode: Reactive[Literal["extended", "browse", "none"]]
    show: Reactive[tuple[str, ...] | list[str] | str]
    xscrollcommand: Callable[..., Any]
    yscrollcommand: Callable[..., Any]


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
    column_weights: GridWeights
    gap: int
    padding: Padding
    row_weights: GridWeights
    sticky: str


class StackItemProps(TypedDict, total=False):
    style: Any
    align: StackAlign
    fill: Fill
    grow: bool
    pack: PackOptions


class GridItemProps(GridOptions, total=False):
    style: Any


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
    value: Reactive[Any]
    on_input: Mutator[Any]
    xscrollcommand: Command
    indicatoron: Reactive[bool]
    offvalue: Reactive[Any]
    onvalue: Reactive[Any]
    selectcolor: Reactive[str]
    selectimage: Reactive[Any]
    variable: Reactive[Any]
    bigincrement: Reactive[float]
    digits: Reactive[int]
    from_: Reactive[float]
    label: Reactive[str]
    resolution: Reactive[float]
    showvalue: Reactive[bool]
    sliderlength: Reactive[int]
    sliderrelief: Reactive[Relief]
    tickinterval: Reactive[float]
    to: Reactive[float]
    troughcolor: Reactive[str]
    closeenough: Reactive[float]
    confine: Reactive[bool]
    offset: Reactive[str]
    scrollregion: Reactive[tuple[int, int, int, int] | str]
    xscrollincrement: Reactive[int]
    yscrollcommand: Command
    yscrollincrement: Reactive[int]
    length: Reactive[int]
    maximum: Reactive[float]
    mode: Reactive[Literal["determinate", "indeterminate"]]
    orient: Reactive[Literal["horizontal", "vertical"]]
    phase: Reactive[int]
    values: Reactive[tuple[Any, ...] | list[Any]]
    activestyle: Reactive[Literal["dotbox", "none", "underline"]]
    activerelief: Reactive[Relief]
    aspect: Reactive[int]
    autoseparators: Reactive[bool]
    blockcursor: Reactive[bool]
    buttonbackground: Reactive[str]
    buttoncursor: Reactive[str]
    buttondownrelief: Reactive[Relief]
    buttonuprelief: Reactive[Relief]
    direction: Reactive[Literal["above", "below", "left", "right", "flush"]]
    displaycolumns: Reactive[tuple[Any, ...] | list[Any] | str]
    elementborderwidth: Reactive[int]
    endline: Reactive[int]
    handlepad: Reactive[int]
    handlesize: Reactive[int]
    inactiveselectbackground: Reactive[str]
    increment: Reactive[float]
    insertunfocussed: Reactive[str]
    jump: Reactive[bool]
    labelanchor: Reactive[Anchor]
    labelwidget: Reactive[Any]
    listvariable: Reactive[Any]
    maxundo: Reactive[int]
    menu: Reactive[Any]
    opaqueresize: Reactive[bool]
    postcommand: Command
    proxybackground: Reactive[str]
    proxyborderwidth: Reactive[int]
    proxyrelief: Reactive[Relief]
    sashcursor: Reactive[str]
    sashpad: Reactive[int]
    sashrelief: Reactive[Relief]
    sashwidth: Reactive[int]
    selectmode: Reactive[str]
    setgrid: Reactive[bool]
    showhandle: Reactive[bool]
    spacing1: Reactive[int]
    spacing2: Reactive[int]
    spacing3: Reactive[int]
    startline: Reactive[int]
    tabs: Reactive[Any]
    tabstyle: Reactive[Literal["tabular", "wordprocessor"]]
    tearoff: Reactive[bool]
    title: Reactive[str]
    tristatevalue: Reactive[Any]
    type: Reactive[Literal["menubar", "tearoff", "normal"]]
    undo: Reactive[bool]
    wrap: Reactive[Any]
