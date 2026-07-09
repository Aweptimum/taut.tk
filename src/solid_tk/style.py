from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Mapping
from types import SimpleNamespace
from typing import Any
from typing import Generic
from typing import ParamSpec
from typing import TypeAlias
from typing import TypeVar
from typing import Unpack

from .tk_props import ButtonProps
from .tk_props import CheckbuttonProps
from .tk_props import EntryProps
from .tk_props import FrameProps
from .tk_props import LabelProps
from .tk_props import StackItemProps
from .tk_props import StackProps
from .tk_props import StyleProps
from .tk_props import TkProps

TProps = TypeVar("TProps")
P = ParamSpec("P")
R = TypeVar("R")
StyleInput: TypeAlias = "Style[Any] | Mapping[str, Any] | None | bool"


class Style(Mapping[str, Any], Generic[TProps]):
    def __init__(self, props: Mapping[str, Any] | None = None, **overrides: Any) -> None:
        values: dict[str, Any] = {}
        if props is not None:
            values.update(props)
        values.update(overrides)
        self._props = values

    def __getitem__(self, key: str) -> Any:
        return self._props[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._props)

    def __len__(self) -> int:
        return len(self._props)

    def __repr__(self) -> str:
        return f"Style({self._props!r})"

    def props(self) -> dict[str, Any]:
        return dict(self._props)


def create(styles: Mapping[str, Mapping[str, Any]]) -> SimpleNamespace:
    return SimpleNamespace(
        **{
            name: value if isinstance(value, Style) else Style(value)
            for name, value in styles.items()
        }
    )


def raw(props: Mapping[str, Any] | None = None, **overrides: Any) -> Style[Any]:
    return Style(props, **overrides)


def define(**props: Unpack[StyleProps]) -> Style[StyleProps]:
    return Style(props)


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


def stack(**props: Unpack[StackProps]) -> Style[StackProps]:
    return Style(props)


def item(**props: Unpack[StackItemProps]) -> Style[StackItemProps]:
    return Style(props)


def merge(*styles: StyleInput, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for item in styles:
        if not item:
            continue
        if isinstance(item, bool):
            continue
        if isinstance(item, Style):
            merged.update(item.props())
        else:
            merged.update(item)
    merged.update(overrides)
    return merged


def component(
    factory: Callable[P, R],
    *styles: StyleInput,
    **defaults: Any,
) -> Callable[P, R]:
    def styled(*children: P.args, **props: P.kwargs) -> R:
        return factory(*children, **merge(*styles, defaults, props))

    return styled
