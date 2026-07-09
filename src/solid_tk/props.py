from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Mapping
from typing import Any

from reaktiv import Computed
from reaktiv import Signal

from .reactive import Accessor
from .reactive import is_signal
from .reactive import read


class NodeProps:
    """Shared prop container for components and widget nodes.

    Props have value semantics by default: existing signals are preserved, while
    plain values and callbacks are wrapped in ``Signal``. Widget nodes can opt
    into binding semantics for a prop, where a callable means "derive this value
    reactively" instead of "this value is a callback".
    """

    def __init__(self, values: Mapping[str, Any]) -> None:
        self._values = dict(values)
        self._signals: dict[str, Accessor[Any]] = {
            key: self._wrap(value) for key, value in self._values.items()
        }

    def _wrap(self, value: Any) -> Accessor[Any]:
        if is_signal(value):
            return value
        return Signal(value)

    def __contains__(self, name: str) -> bool:
        return name in self._values

    def __getattr__(self, name: str) -> Accessor[Any]:
        try:
            return self._signals[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def names(self, *, skip: Iterable[str] = ()) -> list[str]:
        skipped = set(skip)
        return [name for name in self._values if name not in skipped]

    def get(self, name: str, default: Any = None) -> Accessor[Any]:
        if name in self._signals:
            return self._signals[name]
        return Signal(default)

    def raw(self, name: str, default: Any = None) -> Any:
        return self._values.get(name, default)

    def read(self, name: str, default: Any = None) -> Any:
        if name not in self._values:
            return default
        return read(self._signals[name])

    def is_binding(self, name: str, *, event: bool = False) -> bool:
        if event or name not in self._values:
            return False
        value = self._values[name]
        return is_signal(value) or callable(value)

    def prop_accessor(self, name: str) -> Accessor[Any]:
        """Return an accessor for the prop value.

        Existing signals are preserved, callable values become ``Computed``
        bindings, and plain values use their stored signal wrapper.
        """
        value = self._values[name]
        if is_signal(value):
            return value
        if callable(value):
            return Computed(value)
        return self._signals[name]

    def widget_prop_accessor(self, name: str) -> Accessor[Any]:
        """Return an accessor for the concrete value a widget should receive.

        Component props can wrap callable values, such as ``text=lambda: ...``.
        This keeps the binding reactive but unwraps that forwarded callable so
        Tk receives its result instead of the function object.
        """
        prop_accessor = self.prop_accessor(name)

        def read_widget_value() -> Any:
            value = prop_accessor()
            return value() if callable(value) else value

        return Computed(read_widget_value)


class Props(NodeProps):
    """Component props.

    This subclass exists to keep the public component API descriptive while
    sharing the same normalization machinery as widget nodes.
    """
