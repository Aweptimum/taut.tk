from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any
from typing import Generic
from typing import Literal
from typing import Protocol
from typing import TypedDict
from typing import TypeVar
from typing import cast
from typing import overload

from reaktiv import untracked

from . import runtime
from .reactive import Accessor
from .reactive import Mutator
from .reactive import create_signal
from .reactive import to_accessor

T = TypeVar("T")
S = TypeVar("S")
S_contra = TypeVar("S_contra", contravariant=True)
R = TypeVar("R", default=Any)

type ResourceState = Literal["errored", "pending", "ready", "refreshing", "unresolved"]
type ResourceMutation[T] = T | None | Callable[[T | None], T | None]
type ResourceSourceValue[S] = S | Literal[False] | None
type ResourceSource[S] = ResourceSourceValue[S] | Callable[[], ResourceSourceValue[S]]
type ResourceActions[T, R] = tuple[
    Callable[[ResourceMutation[T]], T | None],
    Callable[[R | bool | None], None],
]
type ResourceReturn[S, T, R] = tuple[Resource[S, T, R], ResourceActions[T, R]]


class SourceInfo(Generic[T, R], TypedDict):
    """Metadata passed to a resource fetcher.

    ``value`` is the latest resolved value before this fetch started.
    ``refetching`` is ``False`` for source-driven fetches, ``True`` for a plain
    manual refetch, or the custom value passed to ``refetch(info)``.
    """

    value: T | None
    refetching: R | bool | None


class ResourceFetcher(Protocol[S_contra, T, R]):
    """Callable used by ``create_resource`` to load a value off the UI thread."""

    def __call__(self, source: S_contra, info: SourceInfo[T, R]) -> T: ...


class ResourceOptions(TypedDict, Generic[T], total=False):
    """Optional resource configuration.

    ``initial_value`` seeds ``resource.latest()`` and starts the resource in the
    ``"ready"`` state. ``storage`` can replace the default signal used for the
    cached value. ``name`` is kept for diagnostics and debugging.
    """

    initial_value: T
    name: str
    storage: Callable[[T | None], tuple[Accessor[T | None], Mutator[T | None]]]


class Resource(Generic[S, T, R]):
    """Async resource accessor with Solid-style loading, error, and state flags.

    Call the resource to read the latest value. Use ``resource.loading()``,
    ``resource.error()``, ``resource.state()``, and ``resource.latest()`` for
    reactive status. Values are fetched on a worker thread and published back
    through the current owner's UI dispatcher. Superseded requests are not
    forcibly stopped; their results are ignored if a newer request has started.
    """

    def __init__(
        self,
        fetcher: ResourceFetcher[S, T, R],
        options: ResourceOptions[T],
        source: Accessor[ResourceSourceValue[S]],
    ) -> None:
        self._fetcher = fetcher
        self._source = source
        self._error: tuple[Accessor[Any], Mutator[Any]] = create_signal(None)
        self._loading: tuple[Accessor[bool], Mutator[bool]] = create_signal(False)
        initial_value = options.get("initial_value")
        storage = options.get("storage")
        self._latest: tuple[Accessor[T | None], Mutator[T | None]] = (
            storage(initial_value) if storage is not None else create_signal(initial_value)
        )
        initial_state: ResourceState = "ready" if "initial_value" in options else "unresolved"
        self._state: tuple[Accessor[ResourceState], Mutator[ResourceState]] = (
            create_signal(initial_state)
        )
        self._dispatch = runtime.to_ui()
        self._request_id = 0
        self.name = options.get("name")

    def __call__(self) -> T | None:
        """Return the latest resolved or mutated value."""

        return self._latest[0]()

    @property
    def error(self) -> Accessor[Any]:
        """Accessor for the latest fetch exception, or ``None``."""

        return self._error[0]

    @property
    def latest(self) -> Accessor[T | None]:
        """Accessor for the latest resolved or mutated value."""

        return self._latest[0]

    @property
    def loading(self) -> Accessor[bool]:
        """Accessor that is true while the current request is running."""

        return self._loading[0]

    @property
    def state(self) -> Accessor[ResourceState]:
        """Accessor for the resource state string."""

        return self._state[0]

    def _mutate(self, value: ResourceMutation[T]) -> T | None:
        self._latest[1](value)
        next_value = self._latest[0]()
        self._error[1](None)
        self._loading[1](False)
        self._state[1]("unresolved" if next_value is None else "ready")
        return next_value

    def _refetch(self, info: R | bool | None = True) -> None:
        self._run(refetching=info)

    def _run(self, *, refetching: R | bool | None) -> None:
        src = self._source()
        if src is False or src is None:
            self._loading[1](False)
            if self._latest[0]() is None:
                self._state[1]("unresolved")
            return

        fetcher = self._fetcher
        current_value = untracked(lambda: self.latest())
        self._request_id += 1
        request_id = self._request_id

        self._error[1](None)
        self._loading[1](True)
        self._state[1]("refreshing" if current_value is not None else "pending")

        def task() -> None:
            try:
                info: SourceInfo[T, R] = {
                    "value": current_value,
                    "refetching": refetching,
                }
                result = fetcher(src, info)
            except Exception as exc:
                error = exc
                self._dispatch(lambda: self._reject(error, request_id))
            else:
                self._dispatch(lambda: self._resolve(result, request_id))

        threading.Thread(target=task, daemon=True).start()

    def _reject(self, exc: Exception, request_id: int) -> None:
        if request_id != self._request_id:
            return

        self._error[1](exc)
        self._loading[1](False)
        self._state[1]("errored")

    def _resolve(self, value: T, request_id: int) -> None:
        if request_id != self._request_id:
            return

        self._latest[1](value)
        self._error[1](None)
        self._loading[1](False)
        self._state[1]("ready")


@overload
def create_resource(
    fetcher: ResourceFetcher[Literal[True], T, R],
    options: ResourceOptions[T] | None = None,
) -> ResourceReturn[Literal[True], T, R]: ...


@overload
def create_resource(
    fetcher: ResourceFetcher[S, T, R],
    options: ResourceOptions[T] | None,
    source: ResourceSource[S],
) -> ResourceReturn[S, T, R]: ...


def create_resource(
    fetcher: ResourceFetcher[Any, T, R],
    options: ResourceOptions[T] | None = None,
    source: ResourceSource[Any] = True,
) -> ResourceReturn[Any, T, R]:
    """Create a Solid-style async resource.

    The fetcher runs on a worker thread and receives ``(source, info)``. Source
    changes trigger a fetch automatically; ``False`` and ``None`` sources are
    disabled. The returned actions are ``(mutate, refetch)``. Newer requests
    supersede older ones by ignoring stale completions; Python worker threads
    are not killed.
    """

    resource = Resource(
        fetcher,
        options or {},
        cast(Accessor[ResourceSourceValue[Any]], to_accessor(source)),
    )

    runtime.create_effect(lambda: resource._run(refetching=False))

    def mutate(value: ResourceMutation[T]) -> T | None:
        return resource._mutate(value)

    def refetch(info: R | bool | None = True) -> None:
        resource._refetch(info)

    return resource, (mutate, refetch)
