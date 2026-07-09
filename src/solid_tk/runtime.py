from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Protocol

from reaktiv import Effect


class Node(Protocol):
    widget: Any | None

    def mount(self, parent: Any | None) -> Any: ...

    def unmount(self) -> None: ...


@dataclass
class Mount:
    node: Node
    widget: Any

    def dispose(self) -> None:
        self.node.unmount()


@dataclass
class Owner:
    parent: Owner | None = None
    context: Mapping[Any, Any] = field(default_factory=dict)
    cleanups: list[Callable[[], None]] = field(default_factory=list)
    effects: list[Effect] = field(default_factory=list)
    mounts: list[Callable[[], Any]] = field(default_factory=list)
    mounted: bool = False

    def effect(self, fn: Callable[..., Any]) -> Effect:
        effect = Effect(fn)
        self.effects.append(effect)
        return effect

    def cleanup(self, fn: Callable[[], None]) -> None:
        self.cleanups.append(fn)

    def on_mount(self, fn: Callable[[], Any]) -> None:
        if self.mounted:
            self._run_mount(fn)
            return
        self.mounts.append(fn)

    def run_mounts(self) -> None:
        self.mounted = True
        mounts = self.mounts
        self.mounts = []
        for fn in mounts:
            self._run_mount(fn)

    def _run_mount(self, fn: Callable[[], Any]) -> None:
        cleanup = fn()
        if callable(cleanup):
            self.cleanup(cleanup)

    def dispose(self) -> None:
        for effect in reversed(self.effects):
            effect.dispose()
        self.effects.clear()

        for cleanup in reversed(self.cleanups):
            cleanup()
        self.cleanups.clear()
        self.mounts.clear()
        self.mounted = False


_current_owner: ContextVar[Owner | None] = ContextVar("solid_tk_current_owner", default=None)


@contextmanager
def use_owner(owner: Owner):
    token = _current_owner.set(owner)
    try:
        yield
    finally:
        _current_owner.reset(token)


def get_current_owner() -> Owner | None:
    return _current_owner.get()


def current_owner() -> Owner:
    owner = get_current_owner()
    if owner is None:
        raise RuntimeError("lifecycle helpers must be called inside a solid-tk owner")
    return owner


def create_effect(fn: Callable[..., Any]) -> Effect:
    return current_owner().effect(fn)


def on_cleanup(fn: Callable[[], None]) -> None:
    current_owner().cleanup(fn)


def on_mount(fn: Callable[[], Any]) -> None:
    current_owner().on_mount(fn)


class MountedNode:
    widget: Any | None = None

    def __init__(self, children: Iterable[Any] = (), *, owner: Owner | None = None) -> None:
        self.owner = owner if owner is not None else Owner()
        self.children = [normalize_child(child) for child in children]

    def mount_children(self) -> None:
        if self.widget is None:
            return
        for child in self.children:
            child.mount(self.widget)

    def append_child(self, child: Any) -> Node:
        node = normalize_child(child)
        self.children.append(node)
        return node

    def unmount_children(self) -> None:
        for child in reversed(self.children):
            child.unmount()
        self.children.clear()

    def unmount(self) -> None:
        self.unmount_children()
        self.owner.dispose()
        widget = self.widget
        self.widget = None
        if widget is not None:
            widget.destroy()


def normalize_child(child: Any) -> Node:
    if hasattr(child, "mount") and hasattr(child, "unmount"):
        return child
    from .widgets import Label

    return Label(text=str(child))


def create_root(app: Callable[[], Node] | Node, *, title: str | None = None) -> Mount:
    from .widgets import Tk

    root_node = Tk(title=title) if title is not None else Tk()
    root = root_node.mount(None)

    with use_owner(root_node.owner):
        child = app() if callable(app) and not hasattr(app, "mount") else app
    node = root_node.append_child(child)
    node.mount(root)
    return Mount(node=root_node, widget=root)
