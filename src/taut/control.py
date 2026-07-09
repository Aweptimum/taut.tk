from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from inspect import Parameter
from inspect import signature
from typing import Any
from typing import cast

from .reactive import Accessor
from .reactive import Mutator
from .reactive import create_signal
from .reactive import is_signal
from .reactive import read
from .reactive import to_accessor
from .runtime import MountedNode
from .runtime import Node
from .runtime import Owner
from .runtime import get_current_owner
from .runtime import normalize_child
from .runtime import use_owner
from .stores import MutableList

ErrorFallback = Callable[[Exception, Callable[[], None]], Any] | Callable[[], Any] | Any


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
        self.child_source = children
        self.fallback = fallback
        self.active: Node | None = None
        self.active_key: bool | None = None
        self.fragment_children = MutableList[Node](wrap=False)

    def mount(self, parent: Any | None) -> Any:
        self.widget = parent
        with use_owner(self.owner):
            self.update()
        self.owner.effect(self.update)
        return parent

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
        source = self.child_source if key else self.fallback
        if source is None:
            self.fragment_children.replace([])
            return
        child = source() if callable(source) else source
        self.active = normalize_child(child)
        self.fragment_children.replace([self.active])

    def unmount(self) -> None:
        if self.active is not None:
            self.active.unmount()
            self.active = None
        self.fragment_children.replace([])
        self.owner.dispose()
        self.widget = None


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
        self.fragment_children = MutableList[Node](wrap=False)

    def mount(self, parent: Any | None) -> Any:
        self.widget = parent
        with use_owner(self.owner):
            self.update()
        self.owner.effect(self.update)
        return parent

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
            next_instances[key] = node

        self.instances = next_instances
        self.order = next_keys
        self.fragment_children.replace([self.instances[key] for key in self.order])

    def unmount(self) -> None:
        for key in reversed(self.order):
            self.instances[key].unmount()
        self.instances.clear()
        self.order.clear()
        self.fragment_children.replace([])
        self.owner.dispose()
        self.widget = None


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
        self.fragment_children = MutableList[Node](wrap=False)

    def mount(self, parent: Any | None) -> Any:
        self.widget = parent
        with use_owner(self.owner):
            self.update()
        self.owner.effect(self.update)
        return parent

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
            self.fragment_children.replace([])
            return

        child = source() if callable(source) else source
        self.active = normalize_child(child)
        self.fragment_children.replace([self.active])

    def unmount(self) -> None:
        if self.active is not None:
            self.active.unmount()
            self.active = None
        self.fragment_children.replace([])
        self.owner.dispose()
        self.widget = None


class IndexNode(MountedNode):
    def __init__(
        self,
        each: Any,
        render: Callable[[Any, int], Any],
    ) -> None:
        super().__init__()
        self.each = to_accessor(each)
        self.render = render
        self.items: list[tuple[Accessor[Any], Mutator[Any]]] = []
        self.instances: list[Node] = []
        self.fragment_children = MutableList[Node](wrap=False)

    def mount(self, parent: Any | None) -> Any:
        self.widget = parent
        with use_owner(self.owner):
            self.update()
        self.owner.effect(self.update)
        return parent

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
        self.fragment_children.replace(self.instances)

    def unmount(self) -> None:
        for node in reversed(self.instances):
            node.unmount()
        self.instances.clear()
        self.items.clear()
        self.fragment_children.replace([])
        self.owner.dispose()
        self.widget = None


class DynamicNode(MountedNode):
    def __init__(self, component: Any, **props: Any) -> None:
        super().__init__()
        self.component = component
        self.component_accessor = component if is_signal(component) else None
        self.props = props
        self.active: Node | None = None
        self.active_key: Any = object()
        self.fragment_children = MutableList[Node](wrap=False)

    def mount(self, parent: Any | None) -> Any:
        self.widget = parent
        with use_owner(self.owner):
            self.update()
        self.owner.effect(self.update)
        return parent

    def update(self) -> None:
        if self.widget is None:
            return

        component = (
            self.component_accessor() if self.component_accessor else self.component
        )
        if component is self.active_key:
            return

        if self.active is not None:
            self.active.unmount()
            self.active = None

        self.active_key = component
        child = component(**self.props) if callable(component) else component
        self.active = normalize_child(child)
        self.fragment_children.replace([self.active])

    def unmount(self) -> None:
        if self.active is not None:
            self.active.unmount()
            self.active = None
        self.fragment_children.replace([])
        self.owner.dispose()
        self.widget = None


def _call_error_fallback(
    fallback: Callable[..., Any],
    error: Exception,
    reset: Callable[[], None],
) -> Any:
    try:
        parameters = signature(fallback).parameters.values()
    except (TypeError, ValueError):
        return fallback(error, reset)

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
    if has_varargs or len(positional) >= 2:
        return fallback(error, reset)
    return fallback()


class ErrorBoundaryNode(MountedNode):
    def __init__(
        self,
        children: Callable[[], Any] | Any,
        *,
        fallback: ErrorFallback = None,
    ) -> None:
        owner = Owner(parent=get_current_owner(), error_handler=self.handle_error)
        super().__init__(owner=owner)
        self.child_source = children
        self.fallback = fallback
        self.error, self.set_error = create_signal(cast(Any, None))
        self.active: Node | None = None
        self.active_kind: str | None = None
        self.mounting_child = False
        self.fragment_children = MutableList[Node](wrap=False)

    def mount(self, parent: Any | None) -> Any:
        self.widget = parent
        with use_owner(self.owner):
            self.update()
        self.owner.effect(self.update)
        return parent

    def update(self) -> None:
        if self.widget is None:
            return

        error = self.error()
        if error is not None:
            self.show_fallback(error)
            return

        if self.active_kind == "child":
            return

        self.unmount_active()
        try:
            self.mounting_child = True
            self.active = self.mount_source(self.child_source, owner=self.owner)
        except Exception as exc:
            self.handle_error(exc)
            self.show_fallback(exc)
            return
        finally:
            self.mounting_child = False
        error = self.error()
        if error is not None:
            self.show_fallback(error)
            return
        self.active_kind = "child"
        self.fragment_children.replace([self.active])

    def mount_source(self, source: Callable[[], Any] | Any, *, owner: Owner) -> Node:
        if self.widget is None:
            raise RuntimeError("cannot mount ErrorBoundary child before boundary")

        node: Node | None = None
        try:
            with use_owner(owner):
                child = source() if callable(source) else source
                node = normalize_child(child)
            return node
        except Exception:
            if node is not None:
                node.unmount()
            raise

    def show_fallback(self, error: Exception) -> None:
        if self.active_kind == "fallback":
            return

        self.unmount_active()
        try:
            self.active = self.mount_fallback(error)
        except Exception as exc:
            self.handle_fallback_error(exc)
            return
        else:
            self.active_kind = "fallback"
            self.fragment_children.replace([self.active])

    def mount_fallback(self, error: Exception) -> Node:
        owner = self.owner.parent
        if owner is None:
            raise error

        if self.fallback is None:
            return self.mount_source(str(error), owner=owner)

        source = self.fallback
        if callable(source):
            fallback = source

            def render_fallback() -> Any:
                return _call_error_fallback(fallback, error, self.reset)

            source = render_fallback
        return self.mount_source(source, owner=owner)

    def handle_fallback_error(self, error: Exception) -> None:
        if self.owner.parent is None:
            raise error
        self.owner.parent.handle_error(error)

    def handle_error(self, error: Exception) -> None:
        self.set_error(error)
        if self.widget is not None and not self.mounting_child:
            self.show_fallback(error)

    def reset(self) -> None:
        self.active_kind = None
        self.set_error(None)

    def unmount_active(self) -> None:
        if self.active is not None:
            self.active.unmount()
            self.active = None
        self.active_kind = None
        self.fragment_children.replace([])

    def unmount(self) -> None:
        self.unmount_active()
        self.owner.dispose()
        self.widget = None


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


def Index(
    each: Any,
    render: Callable[[Any, int], Any],
) -> IndexNode:
    return IndexNode(each, render)


def Dynamic(component: Any, **props: Any) -> DynamicNode:
    return DynamicNode(component, **props)


def ErrorBoundary(
    children: Callable[[], Any] | Any,
    *,
    fallback: ErrorFallback = None,
) -> ErrorBoundaryNode:
    return ErrorBoundaryNode(children, fallback=fallback)
