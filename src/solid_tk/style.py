from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Mapping
from typing import Any
from typing import Generic
from typing import ParamSpec
from typing import TypeAlias
from typing import TypeVar
from typing import Unpack
from typing import cast
from typing import overload

from .tk_props import ButtonProps
from .tk_props import CanvasProps
from .tk_props import CheckbuttonProps
from .tk_props import EntryProps
from .tk_props import FrameProps
from .tk_props import GridItemProps
from .tk_props import GridProps
from .tk_props import LabelFrameProps
from .tk_props import LabelProps
from .tk_props import ListboxProps
from .tk_props import MenubuttonProps
from .tk_props import MenuProps
from .tk_props import MessageProps
from .tk_props import OptionMenuProps
from .tk_props import PanedWindowProps
from .tk_props import RadiobuttonProps
from .tk_props import ScaleProps
from .tk_props import ScrollbarProps
from .tk_props import SpinboxProps
from .tk_props import StackItemProps
from .tk_props import StackProps
from .tk_props import StyleProps
from .tk_props import TextProps
from .tk_props import TkProps

TProps = TypeVar("TProps")
P = ParamSpec("P")
R = TypeVar("R")
StyleInput: TypeAlias = "Style[Any] | Mapping[str, Any] | None | bool"
LAYOUT_PROP_KEYS = {"pack", "grid", "place"}


class Style(Mapping[str, Any], Generic[TProps]):
    def __init__(
        self,
        props: Mapping[str, Any] | None = None,
        *,
        name: str | None = None,
        **overrides: Any,
    ) -> None:
        values: dict[str, Any] = {}
        if props is not None:
            values.update(props)
        values.update(overrides)
        self._props = values
        self.name = name

    def __getitem__(self, key: str) -> Any:
        return self._props[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._props)

    def __len__(self) -> int:
        return len(self._props)

    def __repr__(self) -> str:
        return f"Style({self._props!r}, name={self.name!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Style):
            return self.name == other.name and self._props == other._props
        if isinstance(other, Mapping):
            return self._props == dict(other)
        return NotImplemented

    def props(self) -> dict[str, Any]:
        return dict(self._props)


def named(name: str, style: StyleInput) -> Style[Any]:
    return Style(style_props(style), name=style_name(name))


def style_name(name: str) -> str:
    parts = [part.capitalize() for part in name.replace("-", "_").split("_") if part]
    return "".join(parts) or "Style"


def raw(props: Mapping[str, Any] | None = None, **overrides: Any) -> Style[Any]:
    return Style(props, **overrides)


@overload
def define(**props: Unpack[StyleProps]) -> Style[StyleProps]: ...


@overload
def define(name: str, **props: Unpack[StyleProps]) -> Style[StyleProps]: ...


def define(name: str | None = None, **props: Unpack[StyleProps]) -> Style[StyleProps]:
    return Style(props, name=style_name(name) if name is not None else None)


def tk(**props: Unpack[TkProps]) -> Style[TkProps]:
    return Style(props)


def frame(**props: Unpack[FrameProps]) -> Style[FrameProps]:
    return Style(props)


def label(**props: Unpack[LabelProps]) -> Style[LabelProps]:
    return Style(props)


def button(**props: Unpack[ButtonProps]) -> Style[ButtonProps]:
    return Style(props)


def entry(**props: Unpack[EntryProps]) -> Style[EntryProps]:
    return Style(props)


def checkbutton(**props: Unpack[CheckbuttonProps]) -> Style[CheckbuttonProps]:
    return Style(props)


def radiobutton(**props: Unpack[RadiobuttonProps]) -> Style[RadiobuttonProps]:
    return Style(props)


def scale(**props: Unpack[ScaleProps]) -> Style[ScaleProps]:
    return Style(props)


def canvas(**props: Unpack[CanvasProps]) -> Style[CanvasProps]:
    return Style(props)


def label_frame(**props: Unpack[LabelFrameProps]) -> Style[LabelFrameProps]:
    return Style(props)


def listbox(**props: Unpack[ListboxProps]) -> Style[ListboxProps]:
    return Style(props)


def menu(**props: Unpack[MenuProps]) -> Style[MenuProps]:
    return Style(props)


def menubutton(**props: Unpack[MenubuttonProps]) -> Style[MenubuttonProps]:
    return Style(props)


def message(**props: Unpack[MessageProps]) -> Style[MessageProps]:
    return Style(props)


def option_menu(**props: Unpack[OptionMenuProps]) -> Style[OptionMenuProps]:
    return Style(props)


def paned_window(**props: Unpack[PanedWindowProps]) -> Style[PanedWindowProps]:
    return Style(props)


def scrollbar(**props: Unpack[ScrollbarProps]) -> Style[ScrollbarProps]:
    return Style(props)


def spinbox(**props: Unpack[SpinboxProps]) -> Style[SpinboxProps]:
    return Style(props)


def text(**props: Unpack[TextProps]) -> Style[TextProps]:
    return Style(props)


def stack(**props: Unpack[StackProps]) -> Style[StackProps]:
    return Style(props)


def grid(**props: Unpack[GridProps]) -> Style[GridProps]:
    return Style(props)


def grid_item(**props: Unpack[GridItemProps]) -> Style[GridItemProps]:
    return Style(props)


def item(**props: Unpack[StackItemProps]) -> Style[StackItemProps]:
    return Style(props)


def merge(*styles: StyleInput, **overrides: Any) -> Style[Any]:
    return merged_style(*styles, overrides)


def merged_style(*styles: StyleInput) -> Style[Any]:
    merged: dict[str, Any] = {}
    name: str | None = None
    for item in styles:
        if not item:
            continue
        if isinstance(item, bool):
            continue
        if isinstance(item, Style):
            if item.name is not None:
                name = item.name
            merged.update(item.props())
        else:
            merged.update(item)
    return Style(merged, name=name)


def style_props(style: StyleInput) -> dict[str, Any]:
    if not style or isinstance(style, bool):
        return {}
    if isinstance(style, Style):
        return style.props()
    return dict(style)


def reject_layout_props(props: Mapping[str, Any]) -> None:
    keys = LAYOUT_PROP_KEYS & props.keys()
    if keys:
        joined = ", ".join(sorted(keys))
        raise ValueError(f"style cannot define parent layout props: {joined}")


def component(
    factory: Callable[P, R],
    *styles: StyleInput,
    **defaults: Any,
) -> Callable[P, R]:
    def styled(*children: P.args, **props: P.kwargs) -> R:
        styled_factory = cast(Any, factory)
        return styled_factory(*children, style=merged_style(*styles, defaults), **props)

    return styled
