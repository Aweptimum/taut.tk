from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any
from typing import TypeVar
from typing import cast

from .props import Props
from .runtime import MountedNode
from .runtime import Node
from .runtime import normalize_child

TProps = TypeVar("TProps")


class ComponentNode(MountedNode):
    def __init__(self, component: Any, rendered: Node) -> None:
        super().__init__()
        self.component = component
        self.rendered = rendered

    def mount(self, parent: Any | None) -> Any:
        self.widget = self.rendered.mount(parent)
        return self.widget

    def unmount(self) -> None:
        self.owner.dispose()
        self.rendered.unmount()
        self.widget = None


def component(fn: Callable[[TProps], Any]) -> Callable[..., ComponentNode]:
    """Wrap a function component in a mountable node factory."""

    @wraps(fn)
    def factory(**props: Any) -> ComponentNode:
        component_props = Props(props)
        rendered = normalize_child(fn(cast(TProps, component_props)))
        return ComponentNode(fn, rendered)

    return factory


class Component:
    """Base class whose constructor returns a renderable node.

    Subclasses implement ``render`` and read props with ``self.props.name()``.
    Existing reaktiv signals are preserved, while plain values and callbacks are
    wrapped in ``Signal`` so component props always have accessor semantics.
    """

    props: Props

    def __new__(cls, **props: Any) -> ComponentNode:  # type: ignore[override]
        instance = super().__new__(cls)
        instance.props = Props(props)
        instance.setup()
        rendered = normalize_child(instance.render())
        return ComponentNode(instance, rendered)

    def setup(self) -> None:
        pass

    def render(self) -> Node:
        raise NotImplementedError
