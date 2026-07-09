from __future__ import annotations

from collections.abc import Callable
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import fields
from dataclasses import is_dataclass
from dataclasses import replace
from typing import Any
from typing import Generic
from typing import TypeVar
from typing import overload

from .reactive import Accessor
from .reactive import Mutator
from .reactive import create_memo
from .reactive import create_signal
from .reactive import is_signal

T = TypeVar("T")
V = TypeVar("V")

PathKey = str | int
type StoreUpdate[T] = T | Callable[[T], T]


class StoreSetter(Generic[T]):
    def __init__(self, accessor: Accessor[T], mutate: Mutator[T]) -> None:
        self._accessor = accessor
        self._mutate = mutate

    def __call__(self, update: StoreUpdate[T], /) -> None:
        self._mutate(update)

    def at(self, *path: PathKey) -> StoreLens[Any]:
        if not path:
            raise ValueError("store path cannot be empty")
        return StoreLens(self._accessor, self._mutate, path)


class StoreLens(Generic[V]):
    def __init__(
        self,
        accessor: Accessor[Any],
        mutate: Mutator[Any],
        path: tuple[PathKey, ...],
    ) -> None:
        self._accessor = accessor
        self._mutate = mutate
        self._path = path
        self._path_accessor = create_memo(lambda: read_path(self._accessor(), self._path))

    def __call__(self) -> V:
        return self._path_accessor()

    def set(self, value: V, /) -> None:
        self.update(lambda _: value)

    def update(self, update: Callable[[V], V], /) -> None:
        self._mutate(lambda state: update_path(state, self._path, update))

    def at(self, *path: PathKey) -> StoreLens[Any]:
        if not path:
            raise ValueError("store path cannot be empty")
        return StoreLens(self._accessor, self._mutate, (*self._path, *path))


@overload
def create_store(initial: T, /) -> tuple[Accessor[T], StoreSetter[T]]: ...


def create_store(initial: T, /) -> tuple[Accessor[T], StoreSetter[T]]:
    signal, set_signal = create_signal(initial)
    return signal, StoreSetter(signal, set_signal)


def produce[T](recipe: Callable[[T], T | None]) -> Callable[[T], T]:
    """Create an updater that mutates a deep-copied draft."""

    def update(value: T) -> T:
        draft = deepcopy(value)
        result = recipe(draft)
        return draft if result is None else result

    return update


def reconcile[T](value: T) -> Callable[[T], T]:
    """Create an updater that recursively reconciles toward ``value``."""

    def update(current: T) -> T:
        return reconcile_value(current, value)

    return update


def unwrap(value: Any) -> Any:
    """Read through store accessors/lenses and unwrap nested containers."""

    if isinstance(value, StoreLens) or is_signal(value):
        return unwrap(value())
    if isinstance(value, Mapping):
        return {key: unwrap(item) for key, item in value.items()}
    if isinstance(value, list):
        return [unwrap(item) for item in value]
    if isinstance(value, tuple):
        return type(value)(unwrap(item) for item in value)
    if is_dataclass(value) and not isinstance(value, type):
        updates = {field.name: unwrap(getattr(value, field.name)) for field in fields(value)}
        return replace(value, **updates)
    return value


def read_path(value: Any, path: tuple[PathKey, ...]) -> Any:
    current = value
    for key in path:
        current = read_key(current, key)
    return current


def read_key(value: Any, key: PathKey) -> Any:
    if isinstance(value, Mapping):
        return value[key]
    if isinstance(value, list | tuple):
        return value[key]
    if isinstance(key, str):
        return getattr(value, key)
    raise TypeError(f"cannot read non-string attribute key {key!r}")


def update_path(
    value: Any,
    path: tuple[PathKey, ...],
    update: Callable[[Any], Any],
) -> Any:
    key = path[0]
    if len(path) == 1:
        return write_key(value, key, update(read_key(value, key)))
    child = read_key(value, key)
    next_child = update_path(child, path[1:], update)
    return write_key(value, key, next_child)


def write_key(value: Any, key: PathKey, child: Any) -> Any:
    if isinstance(value, Mapping):
        return {**value, key: child}
    if isinstance(value, list):
        items = list(value)
        items[key] = child
        return items
    if isinstance(value, tuple):
        items = list(value)
        items[key] = child
        return type(value)(items)
    if is_dataclass(value) and isinstance(key, str):
        return replace(value, **{key: child})
    if isinstance(key, str):
        clone = value.__copy__() if hasattr(value, "__copy__") else copy_attrs(value)
        setattr(clone, key, child)
        return clone
    raise TypeError(f"cannot write non-string attribute key {key!r}")


def reconcile_value(current: Any, value: Any) -> Any:
    if current == value:
        return current
    if isinstance(current, Mapping) and isinstance(value, Mapping):
        return reconcile_mapping(current, value)
    if isinstance(current, list) and isinstance(value, list):
        return reconcile_list(current, value)
    if isinstance(current, tuple) and isinstance(value, tuple):
        return reconcile_tuple(current, value)
    if (
        is_dataclass(current)
        and not isinstance(current, type)
        and is_dataclass(value)
        and not isinstance(value, type)
        and type(current) is type(value)
    ):
        return reconcile_dataclass(current, value)
    return value


def reconcile_mapping(current: Mapping[Any, Any], value: Mapping[Any, Any]) -> dict[Any, Any]:
    result = dict(current)
    for key, next_item in value.items():
        result[key] = (
            reconcile_value(current[key], next_item) if key in current else next_item
        )
    for key in set(current) - set(value):
        del result[key]
    return current if result == current else result


def reconcile_list(current: list[Any], value: list[Any]) -> list[Any]:
    result = [
        reconcile_value(old, new) if index < len(current) else new
        for index, (old, new) in enumerate(zip(current, value, strict=False))
    ]
    if len(value) > len(current):
        result.extend(value[len(current) :])
    return current if result == current else result


def reconcile_tuple(current: tuple[Any, ...], value: tuple[Any, ...]) -> tuple[Any, ...]:
    result = tuple(
        reconcile_value(old, new) if index < len(current) else new
        for index, (old, new) in enumerate(zip(current, value, strict=False))
    )
    if len(value) > len(current):
        result = (*result, *value[len(current) :])
    return current if result == current else type(value)(result)


def reconcile_dataclass(current: Any, value: Any) -> Any:
    updates = {
        field.name: reconcile_value(getattr(current, field.name), getattr(value, field.name))
        for field in fields(current)
    }
    return current if all(getattr(current, key) is item for key, item in updates.items()) else replace(current, **updates)


def copy_attrs(value: Any) -> Any:
    clone = object.__new__(type(value))
    clone.__dict__.update(value.__dict__)
    return clone
