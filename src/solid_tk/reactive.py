from __future__ import annotations

from collections.abc import Callable
from typing import Any
from typing import Generic
from typing import TypeGuard
from typing import TypeVar
from typing import cast
from typing import overload

from reaktiv import Computed
from reaktiv import Signal
from reaktiv import untracked

T = TypeVar("T")


class Accessor(Generic[T]):
    """Represents retrieving a signal's current value"""

    __slots__ = ("_source",)

    def __init__(self, source: Callable[[], T]) -> None:
        self._source = source

    def __call__(self) -> T:
        return self._source()


type Mutation[T] = T | Callable[[T], T]


class Mutator(Generic[T]):
    """Represents setting / updating a signal value"""

    __slots__ = ("_signal",)

    def __init__(self, signal: Signal[T]) -> None:
        self._signal = signal

    @overload
    def __call__(self, value: T, /) -> None: ...

    @overload
    def __call__(self, update_fn: Callable[[T], T], /) -> None: ...

    def __call__(self, update: Mutation[T], /) -> None:
        if callable(update):
            self._signal.update(cast(Callable[[T], T], update))
            return
        self._signal.set(update)


def create_signal[T](initial: T) -> tuple[Accessor[T], Mutator[T]]:
    signal = Signal(initial)
    return Accessor(signal), Mutator(signal)


def create_memo[T](fn: Callable[[], T]) -> Accessor[T]:
    computed = Computed(fn)
    return Accessor(computed)


def create_selector[T, U](
    source: Callable[[], T],
    equals: Callable[[U, T], bool] | None = None,
) -> Callable[[U], bool]:
    """Create a predicate that checks whether a key matches a source value."""

    compare = equals if equals is not None else lambda key, value: key == value
    current = create_memo(source)

    def selected(key: U) -> bool:
        return compare(key, current())

    return selected


def untrack[T](fn: Callable[[], T]) -> T:
    """Read reactive values inside ``fn`` without subscribing the current effect."""

    return cast(T, untracked(fn))


def on[T, U](
    source: Callable[[], T],
    fn: Callable[[T], U],
    *,
    defer: bool = False,
) -> Callable[[], U | None]:
    """Run ``fn`` when ``source`` changes, without tracking reads inside ``fn``."""

    initialized = False

    def effect() -> U | None:
        nonlocal initialized
        value = source()
        if defer and not initialized:
            initialized = True
            return None
        initialized = True
        return untrack(lambda: fn(value))

    return effect


def is_signal(value: object) -> TypeGuard[Accessor[Any]]:
    return isinstance(value, Accessor) or isinstance(value, Signal)


def is_accessor(value: object) -> TypeGuard[Accessor[Any]]:
    return isinstance(value, Accessor)


def is_mutator(value: object) -> TypeGuard[Mutator[Any]]:
    return isinstance(value, Mutator)


def to_accessor(value: Any) -> Accessor[Any]:
    if isinstance(value, Accessor):
        return value
    if isinstance(value, Signal):
        return Accessor(value)
    if callable(value):
        return create_memo(value)
    signal = Signal(value)
    return Accessor(signal)


def read(value: Any) -> Any:
    if isinstance(value, Accessor):
        return value()
    if isinstance(value, Signal):
        return value()
    return value() if callable(value) else value
