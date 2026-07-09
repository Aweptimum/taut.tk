from __future__ import annotations

from collections.abc import Callable
from typing import Any
from typing import Generic
from typing import Protocol
from typing import TypeGuard
from typing import TypeVar
from typing import cast
from typing import overload

from reaktiv import Computed
from reaktiv import Signal

T = TypeVar("T")


class Accessor[T](Protocol):
    """Represents retrieving a signal's current value"""

    def __call__(self) -> T: ...


type Mutation[T] = T | Callable[[T], T]


class Mutator[T](Protocol):
    """Represents setting / updating a signal value"""

    @overload
    def __call__(self, value: T, /) -> None: ...

    @overload
    def __call__(self, update_fn: Callable[[T], T], /) -> None: ...


class _SignalMutator(Generic[T]):
    def __init__(self, signal: Signal[T]) -> None:
        self._signal = signal

    def __call__(self, update: Mutation[T], /) -> None:
        if callable(update):
            self._signal.update(cast(Callable[[T], T], update))
            return
        self._signal.set(update)


def create_signal[T](initial: T) -> tuple[Accessor[T], Mutator[T]]:
    signal = Signal(initial)
    return signal, _SignalMutator(signal)


def create_memo[T](fn: Callable[[], T]) -> Accessor[T]:
    return Computed(fn)


def is_signal(value: object) -> TypeGuard[Accessor[Any]]:
    return callable(value) and hasattr(value, "get")


def is_accessor(value: object) -> TypeGuard[Accessor[Any]]:
    return callable(value)


def is_mutator(value: object) -> TypeGuard[Mutator[Any]]:
    return isinstance(value, _SignalMutator)


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
