from __future__ import annotations

import tkinter as tk
from collections.abc import Iterable
from typing import Any
from typing import Unpack

from .props import NodeProps
from .runtime import MountedNode
from .tk_props import ButtonProps
from .tk_props import CheckbuttonProps
from .tk_props import EntryProps
from .tk_props import FrameProps
from .tk_props import LabelProps
from .tk_props import LayoutProps
from .tk_props import StackProps
from .tk_props import TkProps

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

    def mount(self, parent: Any | None) -> Any:
        ctor_props: dict[str, Any] = {}
        reactive_props: dict[str, Any] = {}

        skipped_props = self.skipped_props | INTERNAL_KEYS | LAYOUT_KEYS
        for name in self.props.names(skip=skipped_props):
            tk_name = event_name(name)
            if self.props.is_binding(name, event=is_event_prop(name)):
                reactive_props[tk_name] = self.props.widget_binding(name)
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
        self.apply_layout()
        self.bind_reactive_props(reactive_props)

        self.mount_children()

        return self.widget

    def prepare_ctor_props(self, parent: Any | None, props: dict[str, Any]) -> None:
        pass

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
            accessor = value

            def make_apply(prop_name: str, prop_accessor: Any):
                def apply() -> None:
                    if self.widget is not None:
                        self.widget.configure(**{prop_name: prop_accessor()})

                return apply

            self.owner.effect(make_apply(name, accessor))


class ValueWidgetNode(WidgetNode):
    """Base for input widgets"""

    skipped_props = {"value"}

    def prepare_ctor_props(self, parent: Any | None, props: dict[str, Any]) -> None:
        if "value" not in self.props:
            return
        if "textvariable" in self.props:
            raise ValueError("value and textvariable cannot be used together")

        variable = tk.StringVar(master=parent)
        props["textvariable"] = variable
        accessor = self.props.binding("value")
        raw_value = self.props.raw("value")
        writable = raw_value if hasattr(raw_value, "set") else None
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
            if writable is not None and not syncing:
                writable.set(variable.get())

        trace_id = variable.trace_add("write", sync_to_signal)
        self.owner.cleanup(lambda: variable.trace_remove("write", trace_id))
        self.owner.effect(sync_from_signal)


class RootNode(WidgetNode):
    skipped_props = {"title"}

    def mount(self, parent: Any | None = None) -> Any:
        widget = super().mount(None)
        if "title" in self.props:
            accessor = self.props.binding("title")

            def apply_title() -> None:
                if self.widget is not None:
                    self.widget.title(accessor())

            self.owner.effect(apply_title)
        return widget

    def unmount(self) -> None:
        self.unmount_children()
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


def is_event_prop(name: str) -> bool:
    return name == "command" or name.startswith("on_")


def Tk(*children: Any, **props: Unpack[TkProps]) -> RootNode:
    return RootNode(tk.Tk, children=children, layout={}, **props)


def Frame(*children: Any, **props: Unpack[FrameProps]) -> WidgetNode:
    layout = consume_layout(props)
    return WidgetNode(tk.Frame, children=children, layout=layout, **props)


def Label(*children: Any, **props: Unpack[LabelProps]) -> WidgetNode:
    layout = consume_layout(props)
    return WidgetNode(tk.Label, children=children, layout=layout, **props)


def Button(*children: Any, **props: Unpack[ButtonProps]) -> WidgetNode:
    layout = consume_layout(props)
    return WidgetNode(tk.Button, children=children, layout=layout, **props)


def Entry(*children: Any, **props: Unpack[EntryProps]) -> WidgetNode:
    layout = consume_layout(props)
    return ValueWidgetNode(tk.Entry, children=children, layout=layout, **props)


def Checkbutton(*children: Any, **props: Unpack[CheckbuttonProps]) -> WidgetNode:
    layout = consume_layout(props)
    return WidgetNode(tk.Checkbutton, children=children, layout=layout, **props)


def VStack(*children: Any, **props: Unpack[StackProps]) -> WidgetNode:
    layout = consume_layout(props)
    node = WidgetNode(tk.Frame, children=children, layout=layout, **props)
    for child in node.children:
        if isinstance(child, WidgetNode):
            child.layout = {"pack": {"side": "top", "fill": "x", "anchor": "w"}}
    return node


def HStack(*children: Any, **props: Unpack[StackProps]) -> WidgetNode:
    layout = consume_layout(props)
    node = WidgetNode(tk.Frame, children=children, layout=layout, **props)
    for child in node.children:
        if isinstance(child, WidgetNode):
            child.layout = {"pack": {"side": "left", "anchor": "center"}}
    return node


def consume_layout(props: LayoutProps) -> dict[str, Any]:
    for key in ("pack", "grid", "place"):
        if key in props:
            return {key: props.pop(key)}
    return {"pack": {}}
