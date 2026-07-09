from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from reaktiv import Signal

from .reactive import is_signal
from .runtime import MountedNode
from .runtime import Node
from .runtime import normalize_child


class Props:
    def __init__(self, values: Mapping[str, Any]) -> None:
        self._values = dict(values)
        self._signals: dict[str, Any] = {
            key: self._wrap(value) for key, value in self._values.items()
        }

    def _wrap(self, value: Any) -> Any:
        if is_signal(value):
            return value
        return Signal(value)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._signals[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def get(self, name: str, default: Any = None) -> Any:
        return self._signals.get(name, Signal(default))

    def raw(self, name: str, default: Any = None) -> Any:
        return self._values.get(name, default)


class ComponentNode(MountedNode):
    def __init__(self, component: "Component", rendered: Node) -> None:
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
