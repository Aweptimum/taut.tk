from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Mapping
from collections.abc import MutableMapping
from collections.abc import MutableSequence
from copy import copy
from copy import deepcopy
from dataclasses import fields
from dataclasses import is_dataclass
from dataclasses import replace
from typing import Any
from typing import Generic
from typing import TypeVar
from typing import cast
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


class MutableBase:
    def __init__(self) -> None:
        self._version, self._set_version = create_signal(0)

    def _track(self) -> None:
        self._version()

    def _notify(self) -> None:
        self._set_version(lambda version: version + 1)


class MutableList(MutableBase, MutableSequence[T]):
    """Reactive mutable list proxy.

    Reads track a private version signal; writes mutate the backing list in
    place and bump the version so effects/memos that read the list re-run.
    """

    def __init__(self, initial: Iterable[T] = (), *, wrap: bool = True) -> None:
        super().__init__()
        self._wrap_items = wrap
        self._items = [self._wrap(item) for item in initial]

    def _wrap(self, item: T) -> T:
        if not self._wrap_items:
            return item
        return _wrap_mutable(item)

    def __len__(self) -> int:
        self._track()
        return len(self._items)

    @overload
    def __getitem__(self, index: int) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> list[T]: ...

    def __getitem__(self, index: int | slice) -> T | list[T]:
        self._track()
        return self._items[index]

    @overload
    def __setitem__(self, index: int, value: T) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...

    def __setitem__(self, index: int | slice, value: T | Iterable[T]) -> None:
        if isinstance(index, slice):
            self._items[index] = [self._wrap(item) for item in cast(Iterable[T], value)]
        else:
            self._items[index] = self._wrap(cast(T, value))
        self._notify()

    @overload
    def __delitem__(self, index: int) -> None: ...

    @overload
    def __delitem__(self, index: slice) -> None: ...

    def __delitem__(self, index: int | slice) -> None:
        del self._items[index]
        self._notify()

    def __iter__(self) -> Iterator[T]:
        self._track()
        return iter(self._items)

    def __repr__(self) -> str:
        return repr(self.snapshot())

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MutableList):
            return self.snapshot() == other.snapshot()
        return self.snapshot() == other

    def insert(self, index: int, value: T) -> None:
        self._items.insert(index, self._wrap(value))
        self._notify()

    def replace(self, values: Iterable[T]) -> None:
        self._items[:] = [self._wrap(item) for item in values]
        self._notify()

    def snapshot(self) -> list[T]:
        self._track()
        return list(self._items)


class MutableDict(MutableBase, MutableMapping[Any, Any]):
    """Reactive mutable mapping proxy."""

    def __init__(self, initial: Mapping[Any, Any] = {}) -> None:
        super().__init__()
        self._items = {
            key: _wrap_mutable(value) for key, value in initial.items()
        }

    def __getitem__(self, key: Any) -> Any:
        self._track()
        return self._items[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        self._items[key] = _wrap_mutable(value)
        self._notify()

    def __delitem__(self, key: Any) -> None:
        del self._items[key]
        self._notify()

    def __iter__(self) -> Iterator[Any]:
        self._track()
        return iter(self._items)

    def __len__(self) -> int:
        self._track()
        return len(self._items)

    def __repr__(self) -> str:
        return repr(self.snapshot())

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MutableDict):
            return self.snapshot() == other.snapshot()
        return self.snapshot() == other

    def replace(self, values: Mapping[Any, Any]) -> None:
        self._items.clear()
        self._items.update(
            {key: _wrap_mutable(value) for key, value in values.items()}
        )
        self._notify()

    def snapshot(self) -> dict[Any, Any]:
        self._track()
        return dict(self._items)


class MutableObject(MutableBase):
    """Reactive mutable object proxy."""

    def __init__(self, initial: Any) -> None:
        object.__setattr__(self, "_values", {})
        super().__init__()
        object.__getattribute__(self, "_values").update(
            {
                key: _wrap_mutable(value)
                for key, value in vars(initial).items()
                if not key.startswith("_")
            }
        )

    def __getattr__(self, name: str) -> Any:
        values = object.__getattribute__(self, "_values")
        try:
            self._track()
            return values[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        values = object.__getattribute__(self, "_values")
        values[name] = _wrap_mutable(value)
        self._notify()

    def __delattr__(self, name: str) -> None:
        values = object.__getattribute__(self, "_values")
        try:
            del values[name]
        except KeyError as exc:
            raise AttributeError(name) from exc
        self._notify()

    def __repr__(self) -> str:
        return repr(self.snapshot())

    def replace(self, value: Any) -> None:
        values = object.__getattribute__(self, "_values")
        values.clear()
        values.update(
            {
                key: _wrap_mutable(item)
                for key, item in vars(value).items()
                if not key.startswith("_")
            }
        )
        self._notify()

    def snapshot(self) -> dict[str, Any]:
        self._track()
        return dict(object.__getattribute__(self, "_values"))


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
        self._path_accessor = create_memo(
            lambda: read_path(self._accessor(), self._path)
        )

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


def create_store(initial: T, /) -> tuple[Accessor[T], StoreSetter[T]]:
    signal, set_signal = create_signal(initial)
    return signal, StoreSetter(signal, set_signal)


@overload
def create_mutable[T](initial: list[T], /) -> MutableList[T]: ...


@overload
def create_mutable(initial: Mapping[Any, Any], /) -> MutableDict: ...


@overload
def create_mutable[T](initial: T, /) -> T: ...


def create_mutable(initial: Any, /) -> Any:
    return _wrap_mutable(initial)


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
    if isinstance(value, MutableDict):
        return {key: unwrap(item) for key, item in value.items()}
    if isinstance(value, MutableObject):
        return {
            key: unwrap(item)
            for key, item in object.__getattribute__(value, "_values").items()
        }
    if isinstance(value, Mapping):
        return {key: unwrap(item) for key, item in value.items()}
    if isinstance(value, MutableList):
        return [unwrap(item) for item in value]
    if isinstance(value, list):
        return [unwrap(item) for item in value]
    if isinstance(value, tuple):
        return type(value)(unwrap(item) for item in value)
    if is_dataclass(value) and not isinstance(value, type):
        updates = {
            field.name: unwrap(getattr(value, field.name)) for field in fields(value)
        }
        return replace(value, **updates)
    return value


def _wrap_mutable(value: T) -> T:
    if isinstance(value, MutableBase):
        return value
    if isinstance(value, Mapping):
        return cast(T, MutableDict(value))
    if isinstance(value, list):
        return cast(T, MutableList(value))
    if is_mutable_object(value):
        return cast(T, MutableObject(value))
    return value


def is_mutable_object(value: Any) -> bool:
    if isinstance(value, type):
        return False
    if is_dataclass(value):
        return False
    return hasattr(value, "__dict__")


def read_path(value: Any, path: tuple[PathKey, ...]) -> Any:
    current = value
    for key in path:
        current = read_key(current, key)
    return current


def read_key(value: Any, key: PathKey) -> Any:
    if isinstance(value, Mapping):
        return value[key]
    if isinstance(value, list | tuple):
        if not isinstance(key, int):
            raise TypeError(f"cannot read sequence key {key!r}")
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
        if not isinstance(key, int):
            raise TypeError(f"cannot write sequence key {key!r}")
        items = list(value)
        items[key] = child
        return items
    if isinstance(value, tuple):
        if not isinstance(key, int):
            raise TypeError(f"cannot write sequence key {key!r}")
        items = list(value)
        items[key] = child
        return type(value)(items)
    if is_dataclass(value) and not isinstance(value, type) and isinstance(key, str):
        return replace(value, **{key: child})
    if isinstance(key, str):
        clone = copy(value) if hasattr(value, "__copy__") else copy_attrs(value)
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


def reconcile_mapping(
    current: Mapping[Any, Any], value: Mapping[Any, Any]
) -> dict[Any, Any]:
    result = dict(current)
    for key, next_item in value.items():
        result[key] = (
            reconcile_value(current[key], next_item) if key in current else next_item
        )
    for key in set(current) - set(value):
        del result[key]
    return current if isinstance(current, dict) and result == current else result


def reconcile_list(current: list[Any], value: list[Any]) -> list[Any]:
    result = [
        reconcile_value(old, new) if index < len(current) else new
        for index, (old, new) in enumerate(zip(current, value, strict=False))
    ]
    if len(value) > len(current):
        result.extend(value[len(current) :])
    return current if result == current else result


def reconcile_tuple(
    current: tuple[Any, ...], value: tuple[Any, ...]
) -> tuple[Any, ...]:
    result = tuple(
        reconcile_value(old, new) if index < len(current) else new
        for index, (old, new) in enumerate(zip(current, value, strict=False))
    )
    if len(value) > len(current):
        result = (*result, *value[len(current) :])
    return current if result == current else type(value)(result)


def reconcile_dataclass(current: Any, value: Any) -> Any:
    updates = {
        field.name: reconcile_value(
            getattr(current, field.name), getattr(value, field.name)
        )
        for field in fields(current)
    }
    return (
        current
        if all(getattr(current, key) is item for key, item in updates.items())
        else replace(current, **updates)
    )


def copy_attrs(value: Any) -> Any:
    clone = object.__new__(type(value))
    clone.__dict__.update(value.__dict__)
    return clone
