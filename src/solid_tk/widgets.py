from __future__ import annotations

import tkinter as tk
from collections.abc import Iterable
from typing import Any

from .reactive import read
from .reactive import to_accessor
from .runtime import MountedNode
from .runtime import normalize_child

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
        super().__init__()
        self.widget_type = widget_type
        self.props = props
        self.children = [normalize_child(child) for child in children]
        self.layout = layout if layout is not None else {"pack": {}}

    def mount(self, parent: Any | None) -> Any:
        ctor_props: dict[str, Any] = {}
        reactive_props: dict[str, Any] = {}

        for name, value in self.props.items():
            if (
                name in self.skipped_props
                or name in INTERNAL_KEYS
                or name in LAYOUT_KEYS
            ):
                continue
            tk_name = event_name(name)
            if should_bind_reactively(name, value):
                reactive_props[tk_name] = value
            elif is_event_prop(name):
                ctor_props[tk_name] = read(value) if hasattr(value, "get") else value
            else:
                ctor_props[tk_name] = read(value)

        self.widget = (
            self.widget_type(parent, **ctor_props)
            if parent is not None
            else self.widget_type(**ctor_props)
        )
        self.apply_layout()
        self.bind_reactive_props(reactive_props)

        for child in self.children:
            child.mount(self.widget)

        return self.widget

    def apply_layout(self) -> None:
        if self.widget is None:
            return
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
            accessor = to_accessor(value)

            def make_apply(prop_name: str, prop_accessor: Any):
                def apply() -> None:
                    if self.widget is not None:
                        self.widget.configure(**{prop_name: prop_accessor()})

                return apply

            self.owner.effect(make_apply(name, accessor))

    def unmount(self) -> None:
        for child in reversed(self.children):
            child.unmount()
        self.children.clear()
        super().unmount()


class RootNode(WidgetNode):
    skipped_props = {"title"}

    def mount(self, parent: Any | None = None) -> Any:
        widget = super().mount(None)
        title = self.props.get("title")
        if title is not None:
            accessor = to_accessor(title)

            def apply_title() -> None:
                if self.widget is not None:
                    self.widget.title(accessor())

            self.owner.effect(apply_title)
        return widget

    def unmount(self) -> None:
        for child in reversed(self.children):
            child.unmount()
        self.children.clear()
        self.owner.dispose()
        widget = self.widget
        self.widget = None
        if widget is not None:
            widget.quit()
            widget.destroy()


def event_name(name: str) -> str:
    if name.startswith("on_"):
        return "command" if name == "on_click" else name[3:]
    return name


def should_bind_reactively(name: str, value: Any) -> bool:
    if is_event_prop(name):
        return False
    return callable(value)


def is_event_prop(name: str) -> bool:
    return name == "command" or name.startswith("on_")


def Tk(*children: Any, **props: Any) -> RootNode:
    return RootNode(tk.Tk, children=children, layout={}, **props)


def Frame(*children: Any, **props: Any) -> WidgetNode:
    layout = consume_layout(props)
    return WidgetNode(tk.Frame, children=children, layout=layout, **props)


def Label(*children: Any, **props: Any) -> WidgetNode:
    layout = consume_layout(props)
    return WidgetNode(tk.Label, children=children, layout=layout, **props)


def Button(*children: Any, **props: Any) -> WidgetNode:
    layout = consume_layout(props)
    return WidgetNode(tk.Button, children=children, layout=layout, **props)


def Entry(*children: Any, **props: Any) -> WidgetNode:
    layout = consume_layout(props)
    return WidgetNode(tk.Entry, children=children, layout=layout, **props)


def Checkbutton(*children: Any, **props: Any) -> WidgetNode:
    layout = consume_layout(props)
    return WidgetNode(tk.Checkbutton, children=children, layout=layout, **props)


def VStack(*children: Any, **props: Any) -> WidgetNode:
    layout = consume_layout(props)
    node = WidgetNode(tk.Frame, children=children, layout=layout, **props)
    for child in node.children:
        if isinstance(child, WidgetNode):
            child.layout = {"pack": {"side": "top", "fill": "x", "anchor": "w"}}
    return node


def HStack(*children: Any, **props: Any) -> WidgetNode:
    layout = consume_layout(props)
    node = WidgetNode(tk.Frame, children=children, layout=layout, **props)
    for child in node.children:
        if isinstance(child, WidgetNode):
            child.layout = {"pack": {"side": "left", "anchor": "center"}}
    return node


def consume_layout(props: dict[str, Any]) -> dict[str, Any]:
    for key in ("pack", "grid", "place"):
        if key in props:
            return {key: props.pop(key)}
    return {"pack": {}}
