from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from typing import Protocol


class ChildLayout(Protocol):
    """Controls how a container lays out its visible children."""

    def prepare(self, parent: Any, children: Sequence[Any]) -> None: ...

    def reconcile(
        self,
        parent: Any,
        previous: Sequence[Any],
        current: Sequence[Any],
    ) -> None: ...


class NativeLayout:
    """Preserve child-provided geometry while keeping pack order in sync."""

    def prepare(self, parent: Any, children: Sequence[Any]) -> None:
        pass

    def reconcile(
        self,
        parent: Any,
        previous: Sequence[Any],
        current: Sequence[Any],
    ) -> None:
        previous_packed = packed_children(previous)
        current_packed = packed_children(current)
        current_ids = {id(child) for child in current_packed}
        previous_ids = {id(child) for child in previous_packed}

        # Removed widgets disappear in place and new widgets are appended by Tk.
        # Re-pack only when that natural result differs from the desired order.
        natural_order = [
            child for child in previous_packed if id(child) in current_ids
        ]
        natural_order.extend(
            child for child in current_packed if id(child) not in previous_ids
        )
        if same_nodes(natural_order, current_packed):
            return

        for child in current_packed:
            child.apply_layout(reset=True)


def packed_children(children: Sequence[Any]) -> list[Any]:
    return [
        child
        for child in children
        if "pack" in getattr(child, "layout", {})
        and callable(getattr(child, "apply_layout", None))
    ]


def same_nodes(left: Sequence[Any], right: Sequence[Any]) -> bool:
    return len(left) == len(right) and all(
        left_child is right_child
        for left_child, right_child in zip(left, right, strict=True)
    )


__all__ = ["ChildLayout", "NativeLayout", "same_nodes"]
