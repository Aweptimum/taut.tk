from __future__ import annotations

from collections.abc import Callable
from typing import Any
from typing import Protocol
from typing import TypeGuard

from reaktiv import Computed
from reaktiv import Signal


class Accessor[T](Protocol):
    def __call__(self) -> T: ...


class Setter[T](Protocol):
    def __call__(self, value: T, /) -> None: ...


class Updater[T](Protocol):
    def __call__(self, update_fn: Callable[[T], T], /) -> None: ...


class WritableAccessor[T](Accessor[T], Protocol):
    set: Setter[T]
    update: Updater[T]


class SignalLike[T](WritableAccessor[T], Protocol):
    pass


def is_signal(value: object) -> TypeGuard[Accessor[Any]]:
    return callable(value) and hasattr(value, "get")


def is_accessor(value: object) -> TypeGuard[Accessor[Any]]:
    return callable(value)


def to_accessor(value: Any) -> Accessor[Any]:
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
