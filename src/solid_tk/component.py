from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from inspect import signature
from typing import Any
from typing import Generic
from typing import TypeVar
from typing import cast

from .props import Props
from .runtime import MountedNode
from .runtime import Node
from .runtime import Owner
from .runtime import get_current_owner
from .runtime import normalize_child
from .runtime import use_owner

TProps = TypeVar("TProps")


class ComponentNode(MountedNode):
    def __init__(self, component: Any, rendered: Node, *, owner: Owner) -> None:
        super().__init__(owner=owner)
        self.component = component
        self.rendered = rendered

    def mount(self, parent: Any | None) -> Any:
        self.widget = self.rendered.mount(parent)
        self.owner.run_mounts()
        return self.widget

    def unmount(self) -> None:
        self.owner.dispose()
        self.rendered.unmount()
        self.widget = None


def component(fn: Callable[[TProps], Any]) -> Callable[..., ComponentNode]:
    """Wrap a function component in a mountable node factory."""

    @wraps(fn)
    def factory(**props: Any) -> ComponentNode:
        owner = Owner(parent=get_current_owner())
        component_props = Props(props)
        with use_owner(owner):
            rendered = normalize_child(fn(cast(TProps, component_props)))
        return ComponentNode(fn, rendered, owner=owner)

    return factory


class Component(Generic[TProps]):
    """Base class whose constructor returns a renderable node.

    Subclasses implement ``render`` and read props with ``self.props.name()``.
    Existing reaktiv signals are preserved, while plain values and callbacks are
    wrapped in accessors so component props always have accessor semantics.
    """

    props: TProps

    def __new__(cls, **props: Any) -> ComponentNode:  # type: ignore[override]
        owner = Owner(parent=get_current_owner())
        instance = super().__new__(cls)
        instance.props = cast(TProps, Props(props))
        with use_owner(owner):
            if _accepts_no_args(instance.__init__):
                instance.__init__()
            elif _accepts_props_object(instance.__init__):
                instance.__init__(instance.props)
            else:
                raise TypeError(
                    f"{cls.__name__}.__init__ must accept no arguments or a props object"
                )
            rendered = normalize_child(instance.render())
        return ComponentNode(instance, rendered, owner=owner)

    def __init__(self, props: TProps | None = None) -> None:
        self.setup()

    def setup(self) -> None:
        pass

    def render(self) -> Node:
        raise NotImplementedError


def _accepts_no_args(init: Callable[..., Any]) -> bool:
    return len(signature(init).parameters) == 0


def _accepts_props_object(init: Callable[..., Any]) -> bool:
    parameters = signature(init).parameters
    return len(parameters) == 1 and "props" in parameters
