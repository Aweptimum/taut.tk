from __future__ import annotations

from collections.abc import Callable
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
    cleanups: list[Callable[[], None]] = field(default_factory=list)
    effects: list[Effect] = field(default_factory=list)

    def effect(self, fn: Callable[..., Any]) -> Effect:
        effect = Effect(fn)
        self.effects.append(effect)
        return effect

    def cleanup(self, fn: Callable[[], None]) -> None:
        self.cleanups.append(fn)

    def dispose(self) -> None:
        for effect in reversed(self.effects):
            effect.dispose()
        self.effects.clear()

        for cleanup in reversed(self.cleanups):
            cleanup()
        self.cleanups.clear()


class MountedNode:
    widget: Any | None = None

    def __init__(self) -> None:
        self.owner = Owner()

    def unmount(self) -> None:
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

    child = app() if callable(app) and not hasattr(app, "mount") else app
    node = normalize_child(child)
    node.mount(root)
    return Mount(node=root_node, widget=root)
