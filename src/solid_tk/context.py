from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from typing import Generic
from typing import TypeVar
from typing import cast
from typing import overload

from .runtime import MountedNode
from .runtime import Node
from .runtime import Owner
from .runtime import current_owner
from .runtime import normalize_child
from .runtime import use_owner
from .stores import MutableList

T = TypeVar("T")

_MISSING = object()


@dataclass(eq=False, frozen=True)
class Context(Generic[T]):
    default: T | None = None
    has_default: bool = False


@overload
def create_context() -> Context[Any | None]: ...


@overload
def create_context(type_: type[T], /) -> Context[T | None]: ...


@overload
def create_context(default: T, /) -> Context[T]: ...


def create_context(default: Any = _MISSING) -> Context[Any]:
    """Create a context key.

    Passing a type creates a required-provider context whose missing value is
    ``None``:

    ``create_context(Settings)`` returns ``Context[Settings | None]``.

    Passing any non-type value creates a context with that default:

    ``create_context("light")`` returns ``Context[str]``.
    """
    if isinstance(default, type):
        return Context()
    if default is _MISSING:
        return Context()
    return Context(default=default, has_default=True)


def use_context(context: Context[T]) -> T:
    owner = current_owner()
    while owner is not None:
        if context in owner.context:
            return owner.context[context]
        owner = owner.parent
    if context.has_default:
        return cast(T, context.default)
    return None  # type: ignore[return-value]


class ProviderNode(MountedNode):
    def __init__(self, context: Context[Any], value: Any, child: Callable[[], Any] | Any):
        parent = current_owner()
        owner = Owner(parent=parent, context={context: value})
        super().__init__(owner=owner)
        self.child_source = child
        self.child: Node | None = None
        self.fragment_children = MutableList[Node](wrap=False)

    def mount(self, parent: Any | None) -> Any:
        with use_owner(self.owner):
            child = resolve_child(self.child_source)
            self.child = normalize_child(child)
        self.fragment_children.replace([self.child])
        self.widget = parent
        self.owner.run_mounts()
        return parent

    def unmount(self) -> None:
        if self.widget is None and self.child is None:
            return
        self.owner.dispose()
        if self.child is not None:
            self.child.unmount()
            self.child = None
        self.fragment_children.replace([])
        self.widget = None


def Provider(context: Context[T], value: T, child: Callable[[], Any] | Any) -> ProviderNode:
    return ProviderNode(context, value, child)


def resolve_child(child: Callable[[], Any] | Any) -> Any:
    while callable(child) and not (hasattr(child, "mount") and hasattr(child, "unmount")):
        child = child()
    return child
