from __future__ import annotations

from typing import Any
from typing import Protocol
from typing import TypeGuard

from reaktiv import Computed
from reaktiv import ReadableSignal
from reaktiv import Signal


class Accessor(Protocol):
    def __call__(self) -> Any: ...


def is_signal(value: object) -> TypeGuard[ReadableSignal[Any]]:
    return callable(value) and hasattr(value, "get")


def is_accessor(value: object) -> TypeGuard[Accessor]:
    return callable(value)


def to_accessor(value: Any) -> Accessor:
    if is_signal(value):
        return value
    if callable(value):
        return Computed(value)
    signal = Signal(value)
    return signal


def read(value: Any) -> Any:
    if is_signal(value):
        return value()
    return value() if callable(value) else value
