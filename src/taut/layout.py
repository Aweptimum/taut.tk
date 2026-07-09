from __future__ import annotations

import tkinter as tk
from collections.abc import Mapping
from typing import Any
from typing import Unpack

from .nodes import WidgetNode
from .nodes import apply_style
from .nodes import consume_layout
from .runtime import normalize_child
from .tk_props import GridItemProps
from .tk_props import GridProps
from .tk_props import GridWeights
from .tk_props import Padding
from .tk_props import StackAlign
from .tk_props import StackItemProps
from .tk_props import StackProps

STACK_KEYS = {"align", "fill", "gap", "grow", "padding"}
GRID_KEYS = {"columns", "column_weights", "gap", "padding", "row_weights", "sticky"}
STACK_ITEM_KEYS = {"align", "fill", "grow", "pack"}


def Item(child: Any, **props: Unpack[StackItemProps]) -> Any:
    apply_style(props)
    node = normalize_child(child)
    setattr(node, "_stack_layout", dict(props))
    return node


def GridItem(child: Any, **props: Unpack[GridItemProps]) -> Any:
    apply_style(props)
    node = normalize_child(child)
    setattr(node, "_grid_layout", dict(props))
    return node


def VStack(*children: Any, **props: Unpack[StackProps]) -> WidgetNode:
    apply_style(props)
    stack = consume_stack(props, axis="vertical")
    layout = consume_layout(props)
    node = WidgetNode(tk.Frame, children=children, layout=layout, **props)
    setattr(node, "_stack", stack)
    apply_stack_layout(list(node.children), stack)
    return node


def HStack(*children: Any, **props: Unpack[StackProps]) -> WidgetNode:
    apply_style(props)
    stack = consume_stack(props, axis="horizontal")
    layout = consume_layout(props)
    node = WidgetNode(tk.Frame, children=children, layout=layout, **props)
    setattr(node, "_stack", stack)
    apply_stack_layout(list(node.children), stack)
    return node


def Grid(*children: Any, **props: Unpack[GridProps]) -> WidgetNode:
    apply_style(props)
    grid = consume_grid(props)
    layout = consume_layout(props)
    node = WidgetNode(tk.Frame, children=children, layout=layout, **props)
    setattr(node, "_grid", grid)
    apply_grid_layout(list(node.children), grid)
    return node


def consume_stack(props: Any, *, axis: str) -> dict[str, Any]:
    stack = {key: props.pop(key) for key in STACK_KEYS if key in props}

    if "padding" in stack:
        padx, pady = resolve_padding(stack["padding"])
        props.setdefault("padx", padx)
        props.setdefault("pady", pady)

    stack.setdefault("axis", axis)
    stack.setdefault("align", "stretch" if axis == "vertical" else "center")
    stack.setdefault("fill", "x" if axis == "vertical" else "none")
    stack.setdefault("gap", 0)
    stack.setdefault("grow", False)
    return stack


def consume_grid(props: Any) -> dict[str, Any]:
    grid = {key: props.pop(key) for key in GRID_KEYS if key in props}

    if "padding" in grid:
        padx, pady = resolve_padding(grid["padding"])
        props.setdefault("padx", padx)
        props.setdefault("pady", pady)

    grid.setdefault("columns", 1)
    grid.setdefault("column_weights", ())
    grid.setdefault("gap", 0)
    grid.setdefault("row_weights", ())
    grid.setdefault("sticky", "nsew")
    return grid


def resolve_padding(padding: Padding) -> tuple[int, int]:
    if isinstance(padding, tuple):
        return padding
    return padding, padding


def apply_stack_layout(children: list[Any], stack: dict[str, Any]) -> None:
    last_index = len(children) - 1
    for index, child in enumerate(children):
        if not isinstance(child, WidgetNode):
            continue
        if "grid" in child.layout or "place" in child.layout:
            continue

        item = stack_item_layout(child)
        pack = stack_pack_options(stack, item, last=index == last_index)
        pack.update(child.layout.get("pack", {}))
        pack.update(item.get("pack", {}))
        child.layout = {"pack": pack}


def apply_grid_layout(children: list[Any], grid: dict[str, Any]) -> None:
    columns = max(1, grid["columns"])
    gap = grid["gap"]
    for index, child in enumerate(children):
        if not isinstance(child, WidgetNode):
            continue
        if "place" in child.layout:
            continue
        item = getattr(child, "_grid_layout", None)
        if item is None:
            item = child.layout.get("grid", {})
            setattr(child, "_grid_layout", item)

        options = {
            "row": index // columns,
            "column": index % columns,
            "sticky": grid["sticky"],
        }
        if gap:
            options["padx"] = gap
            options["pady"] = gap
        options.update(item)
        child.layout = {"grid": options}


def apply_grid_container_layout(widget: Any, grid: dict[str, Any]) -> None:
    for index, weight in grid_weights(grid["column_weights"]):
        widget.columnconfigure(index, weight=weight)
    for index, weight in grid_weights(grid["row_weights"]):
        widget.rowconfigure(index, weight=weight)


def grid_weights(weights: GridWeights) -> list[tuple[int, int]]:
    if isinstance(weights, Mapping):
        return sorted(weights.items())
    return [(index, weight) for index, weight in enumerate(weights)]


def stack_item_layout(child: WidgetNode) -> dict[str, Any]:
    layout = getattr(child, "_stack_layout", {})
    return {key: value for key, value in layout.items() if key in STACK_ITEM_KEYS}


def stack_pack_options(
    stack: dict[str, Any],
    item: dict[str, Any],
    *,
    last: bool,
) -> dict[str, Any]:
    axis = stack["axis"]
    align = item.get("align", stack["align"])
    fill = item.get("fill", stack["fill"])
    grow = item.get("grow", stack["grow"])

    pack: dict[str, Any] = {
        "side": "top" if axis == "vertical" else "left",
        "anchor": stack_anchor(axis, align),
        "expand": grow,
    }
    if fill != "none":
        pack["fill"] = fill
    if stack["gap"] and not last:
        if axis == "vertical":
            pack["pady"] = (0, stack["gap"])
        else:
            pack["padx"] = (0, stack["gap"])
    return pack


def stack_anchor(axis: str, align: StackAlign) -> str:
    if align == "stretch":
        return "w" if axis == "vertical" else "center"
    if axis == "vertical":
        return {"start": "w", "center": "center", "end": "e"}[align]
    return {"start": "n", "center": "center", "end": "s"}[align]


__all__ = [
    "Grid",
    "GridItem",
    "HStack",
    "Item",
    "VStack",
]
