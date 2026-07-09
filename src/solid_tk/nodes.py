from __future__ import annotations

import tkinter as tk
from collections.abc import Iterable
from typing import Any

from . import style as style_api
from .props import NodeProps
from .runtime import MountedNode
from .runtime import Node
from .runtime import flatten_child_nodes
from .runtime import mount_fragment_children
from .scheduler import TkScheduler
from .tk_props import LayoutProps

LAYOUT_KEYS = {"pack", "grid", "place"}
INTERNAL_KEYS = {"children", "layout"}


class WidgetNode(MountedNode):
    skipped_props: set[str] = set()

    def __init__(
        self,
        widget_type: type[Any],
        *,
        children: Iterable[Any] = (),
        layout: dict[str, Any] | None = None,
        **props: Any,
    ) -> None:
        super().__init__(children)
        self.widget_type = widget_type
        self.props = NodeProps(props)
        self.layout = layout if layout is not None else {"pack": {}}
        self.mounted_children: list[Node] = []

    def mount(self, parent: Any | None) -> Any:
        ctor_props: dict[str, Any] = {}
        reactive_props: dict[str, Any] = {}

        skipped_props = self.skipped_props | INTERNAL_KEYS | LAYOUT_KEYS
        for name in self.props.names(skip=skipped_props):
            tk_name = event_name(name)
            if self.props.is_binding(name, event=is_event_prop(name)):
                reactive_props[tk_name] = self.props.widget_prop_accessor(name)
            elif is_event_prop(name):
                ctor_props[tk_name] = self.props.read(name)
            else:
                ctor_props[tk_name] = self.props.read(name)

        self.prepare_ctor_props(parent, ctor_props)
        self.widget = (
            self.widget_type(parent, **ctor_props)
            if parent is not None
            else self.widget_type(**ctor_props)
        )
        self.owner.scheduler = TkScheduler(self.widget)
        self.apply_layout()
        self.bind_reactive_props(reactive_props)

        self.owner.effect(self.reconcile_children, accepts_cleanup=False)
        self.owner.run_mounts()

        return self.widget

    def prepare_ctor_props(self, parent: Any | None, props: dict[str, Any]) -> None:
        pass

    def apply_layout(self, *, reset: bool = False) -> None:
        if self.widget is None:
            return
        if reset:
            forget_layout(self.widget)
        if "grid" in self.layout:
            self.widget.grid(**self.layout["grid"])
        elif "place" in self.layout:
            self.widget.place(**self.layout["place"])
        elif "pack" in self.layout:
            self.widget.pack(**self.layout["pack"])

    def bind_reactive_props(self, props: dict[str, Any]) -> None:
        if self.widget is None:
            return
        for name, value in props.items():
            accessor = value

            def make_apply(prop_name: str, prop_accessor: Any):
                def apply() -> None:
                    if self.widget is not None:
                        self.widget.configure(**{prop_name: prop_accessor()})

                return apply

            self.owner.effect(make_apply(name, accessor), accepts_cleanup=False)

    def reconcile_children(self) -> None:
        if self.widget is None:
            return

        from .layout import apply_grid_layout
        from .layout import apply_stack_layout

        mount_fragment_children(self.widget, self.children)

        visible = flatten_child_nodes(self.children)
        visible_set = set(visible)
        for child in reversed(self.mounted_children):
            if child not in visible_set:
                child.unmount()

        stack = getattr(self, "_stack", None)
        grid = getattr(self, "_grid", None)
        if stack is not None:
            apply_stack_layout(visible, stack)
        elif grid is not None:
            apply_grid_layout(visible, grid)

        for child in visible:
            if child.widget is None:
                child.mount(self.widget)
            elif (stack is not None or grid is not None) and isinstance(
                child, WidgetNode
            ):
                child.apply_layout(reset=True)

        self.mounted_children = visible


class ValueWidgetNode(WidgetNode):
    """Base for input widgets"""

    skipped_props = {"value", "on_input"}

    def prepare_ctor_props(self, parent: Any | None, props: dict[str, Any]) -> None:
        if "value" not in self.props:
            return
        if "textvariable" in self.props:
            raise ValueError("value and textvariable cannot be used together")

        variable = tk.StringVar(master=parent)
        props["textvariable"] = variable
        accessor = self.props.prop_accessor("value")
        mutate = self.props.raw("on_input") if "on_input" in self.props else None
        syncing = False

        def sync_from_signal() -> None:
            nonlocal syncing
            value = accessor()
            next_value = "" if value is None else str(value)
            if variable.get() != next_value:
                syncing = True
                try:
                    variable.set(next_value)
                finally:
                    syncing = False

        def sync_to_signal(*_: Any) -> None:
            if mutate is not None and not syncing:
                mutate(variable.get())

        trace_id = variable.trace_add("write", sync_to_signal)
        self.owner.cleanup(lambda: variable.trace_remove("write", trace_id))
        self.owner.effect(sync_from_signal)


def event_name(name: str) -> str:
    if name.startswith("on_"):
        return "command" if name == "on_click" else name[3:]
    return name


def is_event_prop(name: str) -> bool:
    return name == "command" or name.startswith("on_")


def apply_style(props: Any) -> None:
    if "style" not in props:
        return
    styled = props.pop("style")
    styled_props = style_api.style_props(styled)
    style_api.reject_layout_props(styled_props)
    overrides = dict(props)
    props.clear()
    props.update(style_api.merge(styled_props, overrides))


def consume_layout(props: LayoutProps) -> dict[str, Any]:
    for key in ("pack", "grid", "place"):
        if key in props:
            return {key: props.pop(key)}
    return {"pack": {}}


def forget_layout(widget: Any) -> None:
    for name in ("pack_forget", "grid_forget", "place_forget"):
        forget = getattr(widget, name, None)
        if callable(forget):
            forget()


__all__ = [
    "ValueWidgetNode",
    "WidgetNode",
    "apply_style",
    "consume_layout",
    "forget_layout",
]
