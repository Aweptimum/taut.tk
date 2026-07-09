from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .reactive import Accessor
from .reactive import Mutator
from .reactive import create_signal
from .reactive import is_signal
from .reactive import read
from .reactive import to_accessor
from .runtime import MountedNode
from .runtime import Node
from .runtime import normalize_child


class ShowNode(MountedNode):
    def __init__(
        self,
        when: Any,
        children: Callable[[], Any] | Any,
        *,
        fallback: Callable[[], Any] | Any | None = None,
    ) -> None:
        super().__init__()
        self.when = to_accessor(when)
        self.children = children
        self.fallback = fallback
        self.active: Node | None = None
        self.active_key: bool | None = None

    def mount(self, parent: Any | None) -> Any:
        from .widgets import tk

        self.widget = tk.Frame(parent)
        self.widget.pack(fill="both", expand=True)
        self.owner.effect(self.update)
        return self.widget

    def update(self) -> None:
        if self.widget is None:
            return
        key = bool(self.when())
        if key == self.active_key:
            return
        if self.active is not None:
            self.active.unmount()
            self.active = None
        self.active_key = key
        source = self.children if key else self.fallback
        if source is None:
            return
        child = source() if callable(source) else source
        self.active = normalize_child(child)
        self.active.mount(self.widget)

    def unmount(self) -> None:
        if self.active is not None:
            self.active.unmount()
            self.active = None
        super().unmount()


class ForNode(MountedNode):
    def __init__(
        self,
        each: Any,
        render: Callable[[Any], Any],
        *,
        key: Callable[[Any], Any] | None = None,
    ) -> None:
        super().__init__()
        self.each = to_accessor(each)
        self.render = render
        self.key = key if key is not None else id
        self.instances: dict[Any, Node] = {}
        self.order: list[Any] = []

    def mount(self, parent: Any | None) -> Any:
        from .widgets import tk

        self.widget = tk.Frame(parent)
        self.widget.pack(fill="both", expand=True)
        self.owner.effect(self.update)
        return self.widget

    def update(self) -> None:
        if self.widget is None:
            return
        items = list(read(self.each))
        next_keys = [self.key(item) for item in items]
        next_key_set = set(next_keys)

        for stale in [key for key in self.order if key not in next_key_set]:
            node = self.instances.pop(stale)
            node.unmount()

        next_instances: dict[Any, Node] = {}
        for item, key in zip(items, next_keys, strict=True):
            node = self.instances.get(key)
            if node is None:
                node = normalize_child(self.render(item))
                node.mount(self.widget)
            next_instances[key] = node

        self.instances = next_instances
        self.order = next_keys
        self.repack()

    def repack(self) -> None:
        for key in self.order:
            widget = self.instances[key].widget
            if widget is not None:
                widget.pack_forget()
                widget.pack(side="top", fill="x", anchor="w")

    def unmount(self) -> None:
        for key in reversed(self.order):
            self.instances[key].unmount()
        self.instances.clear()
        self.order.clear()
        super().unmount()


@dataclass
class MatchCase:
    when: Any
    children: Callable[[], Any] | Any


class SwitchNode(MountedNode):
    def __init__(
        self,
        cases: tuple[MatchCase, ...],
        *,
        fallback: Callable[[], Any] | Any | None = None,
    ) -> None:
        super().__init__()
        self.cases = [(to_accessor(case.when), case.children) for case in cases]
        self.fallback = fallback
        self.active: Node | None = None
        self.active_key: Any = object()

    def mount(self, parent: Any | None) -> Any:
        from .widgets import tk

        self.widget = tk.Frame(parent)
        self.widget.pack(fill="both", expand=True)
        self.owner.effect(self.update)
        return self.widget

    def update(self) -> None:
        if self.widget is None:
            return

        next_key: int | None = None
        source = self.fallback
        for index, (when, children) in enumerate(self.cases):
            if bool(when()):
                next_key = index
                source = children
                break

        if next_key == self.active_key:
            return

        if self.active is not None:
            self.active.unmount()
            self.active = None

        self.active_key = next_key
        if source is None:
            return

        child = source() if callable(source) else source
        self.active = normalize_child(child)
        self.active.mount(self.widget)

    def unmount(self) -> None:
        if self.active is not None:
            self.active.unmount()
            self.active = None
        super().unmount()


class IndexNode(MountedNode):
    def __init__(self, each: Any, render: Callable[[Any, int], Any]) -> None:
        super().__init__()
        self.each = to_accessor(each)
        self.render = render
        self.items: list[tuple[Accessor[Any], Mutator[Any]]] = []
        self.instances: list[Node] = []

    def mount(self, parent: Any | None) -> Any:
        from .widgets import tk

        self.widget = tk.Frame(parent)
        self.widget.pack(fill="both", expand=True)
        self.owner.effect(self.update)
        return self.widget

    def update(self) -> None:
        if self.widget is None:
            return

        items = list(read(self.each))
        for index in range(len(items), len(self.instances)):
            self.instances[index].unmount()

        self.instances = self.instances[: len(items)]
        self.items = self.items[: len(items)]

        for index, item in enumerate(items):
            if index < len(self.items):
                _accessor, mutate = self.items[index]
                mutate(item)
                continue

            accessor, mutate = create_signal(item)
            self.items.append((accessor, mutate))
            node = normalize_child(self.render(accessor, index))
            self.instances.append(node)
            node.mount(self.widget)

        self.repack()

    def repack(self) -> None:
        for node in self.instances:
            if node.widget is not None:
                node.widget.pack_forget()
                node.widget.pack(side="top", fill="x", anchor="w")

    def unmount(self) -> None:
        for node in reversed(self.instances):
            node.unmount()
        self.instances.clear()
        self.items.clear()
        super().unmount()


class DynamicNode(MountedNode):
    def __init__(self, component: Any, **props: Any) -> None:
        super().__init__()
        self.component = component
        self.component_accessor = component if is_signal(component) else None
        self.props = props
        self.active: Node | None = None
        self.active_key: Any = object()

    def mount(self, parent: Any | None) -> Any:
        from .widgets import tk

        self.widget = tk.Frame(parent)
        self.widget.pack(fill="both", expand=True)
        self.owner.effect(self.update)
        return self.widget

    def update(self) -> None:
        if self.widget is None:
            return

        component = self.component_accessor() if self.component_accessor else self.component
        if component is self.active_key:
            return

        if self.active is not None:
            self.active.unmount()
            self.active = None

        self.active_key = component
        child = component(**self.props) if callable(component) else component
        self.active = normalize_child(child)
        self.active.mount(self.widget)

    def unmount(self) -> None:
        if self.active is not None:
            self.active.unmount()
            self.active = None
        super().unmount()


def Show(
    when: Any,
    children: Callable[[], Any] | Any,
    *,
    fallback: Callable[[], Any] | Any | None = None,
) -> ShowNode:
    return ShowNode(when, children, fallback=fallback)


def For(
    each: Any,
    render: Callable[[Any], Any],
    *,
    key: Callable[[Any], Any] | None = None,
) -> ForNode:
    return ForNode(each, render, key=key)


def Match(when: Any, children: Callable[[], Any] | Any) -> MatchCase:
    return MatchCase(when, children)


def Switch(
    *cases: MatchCase,
    fallback: Callable[[], Any] | Any | None = None,
) -> SwitchNode:
    return SwitchNode(cases, fallback=fallback)


def Index(each: Any, render: Callable[[Any, int], Any]) -> IndexNode:
    return IndexNode(each, render)


def Dynamic(component: Any, **props: Any) -> DynamicNode:
    return DynamicNode(component, **props)
