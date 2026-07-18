from __future__ import annotations

from collections import defaultdict
from collections import deque
from collections.abc import Callable
from collections.abc import Iterable
from dataclasses import dataclass
from inspect import Parameter
from inspect import signature
from math import isnan
from typing import Any
from typing import Generic
from typing import Literal
from typing import TypeGuard
from typing import TypeVar
from typing import cast
from typing import overload

from reaktiv import Computed
from reaktiv import Signal
from reaktiv import untracked

T = TypeVar("T")
U = TypeVar("U")


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
    # Import lazily because runtime depends on stores, which depends on this
    # module. Memo evaluation happens after module initialization is complete.
    from .runtime import get_current_owner
    from .runtime import use_owner

    owner = get_current_owner()
    if owner is None:
        computed = Computed(fn)
    else:

        def run() -> T:
            with use_owner(owner):
                return fn()

        computed = Computed(run)
    return Accessor(computed)


class _ObjectIdentity:
    """Hashable identity token for non-primitive mapped items."""

    __slots__ = ("value",)

    def __init__(self, value: Any) -> None:
        self.value = value

    def __hash__(self) -> int:
        return id(self.value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _ObjectIdentity) and self.value is other.value


def _map_item_key(item: Any) -> Any:
    """Return a Python equivalent of JavaScript Map item identity."""

    item_type = type(item)
    if item is None:
        return ("none",)
    if item_type is bool:
        return ("bool", item)
    if item_type is int:
        return ("number", item)
    if item_type is float:
        return ("number-nan",) if isnan(item) else ("number", item)
    if item_type is str:
        return ("str", item)
    if item_type is bytes:
        return ("bytes", item)
    return _ObjectIdentity(item)


def _call_map_fn(map_fn: Callable[..., U], item: Any, index: Accessor[int]) -> U:
    """Pass the index accessor while allowing Python one-argument callbacks."""

    try:
        parameters = signature(map_fn).parameters.values()
    except (TypeError, ValueError):
        return map_fn(item, index)

    positional = [
        parameter
        for parameter in parameters
        if parameter.kind
        in (
            Parameter.POSITIONAL_ONLY,
            Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    has_varargs = any(
        parameter.kind == Parameter.VAR_POSITIONAL for parameter in parameters
    )
    return map_fn(item, index) if has_varargs or len(positional) >= 2 else map_fn(item)


@dataclass
class _MapEntry(Generic[T, U]):
    item: T
    key: Any
    value: U
    owner: Any
    index: Accessor[int]
    set_index: Mutator[int]


class _MappedArray(Generic[T, U]):
    def __init__(
        self,
        source: Callable[[], Iterable[T] | Literal[False] | None],
        map_fn: Callable[..., U],
        fallback: Callable[[], U] | None,
    ) -> None:
        from .runtime import get_current_owner

        self.source = source
        self.map_fn = map_fn
        self.fallback = fallback
        self.owner = get_current_owner()
        self.entries: list[_MapEntry[T, U]] = []
        self.fallback_entry: _MapEntry[Any, U] | None = None
        self.disposed = False
        if self.owner is not None:
            self.owner.cleanup(self.dispose)

    def __call__(self) -> list[U]:
        if self.disposed:
            return []
        source = self.source()
        items = [] if source is None or source is False else list(source)
        return untrack(lambda: self.reconcile(items))

    def reconcile(self, items: list[T]) -> list[U]:
        if not items:
            return self.show_fallback()

        self.dispose_fallback()
        available: defaultdict[Any, deque[_MapEntry[T, U]]] = defaultdict(deque)
        for entry in self.entries:
            available[entry.key].append(entry)

        next_entries: list[_MapEntry[T, U]] = []
        created: list[_MapEntry[T, U]] = []
        try:
            for position, item in enumerate(items):
                key = _map_item_key(item)
                matches = available[key]
                if matches:
                    entry = matches.popleft()
                    entry.set_index(position)
                else:
                    entry = self.create_entry(item, key, position)
                    created.append(entry)
                next_entries.append(entry)
        except Exception:
            for entry in reversed(created):
                entry.owner.dispose()
            raise

        for stale_entries in available.values():
            for entry in stale_entries:
                entry.owner.dispose()

        self.entries = next_entries
        return [entry.value for entry in self.entries]

    def create_entry(self, item: T, key: Any, position: int) -> _MapEntry[T, U]:
        from .runtime import Owner
        from .runtime import use_owner

        owner = Owner(parent=self.owner)
        index, set_index = create_signal(position)
        try:
            with use_owner(owner):
                value = _call_map_fn(self.map_fn, item, index)
        except Exception:
            owner.dispose()
            raise
        return _MapEntry(item, key, value, owner, index, set_index)

    def show_fallback(self) -> list[U]:
        for entry in reversed(self.entries):
            entry.owner.dispose()
        self.entries.clear()

        if self.fallback is None:
            return []
        if self.fallback_entry is None:
            from .runtime import Owner
            from .runtime import use_owner

            owner = Owner(parent=self.owner)
            try:
                with use_owner(owner):
                    value = self.fallback()
            except Exception:
                owner.dispose()
                raise
            index, set_index = create_signal(0)
            self.fallback_entry = _MapEntry(
                None, ("fallback",), value, owner, index, set_index
            )
        return [self.fallback_entry.value]

    def dispose_fallback(self) -> None:
        if self.fallback_entry is None:
            return
        self.fallback_entry.owner.dispose()
        self.fallback_entry = None

    def dispose(self) -> None:
        if self.disposed:
            return
        self.disposed = True
        for entry in reversed(self.entries):
            entry.owner.dispose()
        self.entries.clear()
        self.dispose_fallback()


def map_array[T, U](
    source: Callable[[], Iterable[T] | Literal[False] | None],
    map_fn: Callable[..., U],
    *,
    fallback: Callable[[], U] | None = None,
) -> Accessor[list[U]]:
    """Reactively map a list while retaining results by item identity.

    Objects are matched by reference identity and built-in primitives by value.
    The mapping callback receives the item and a reactive index accessor. Its
    reads are untracked, and each mapped value owns an independently disposable
    lifecycle scope. Empty, ``None``, and ``False`` sources use ``fallback``.
    """

    mapped = _MappedArray(source, map_fn, fallback)
    return create_memo(mapped)


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
