from __future__ import annotations

import tkinter as tk
from collections.abc import Iterable
from typing import Any
from typing import Unpack

from . import style as style_api
from .props import NodeProps
from .runtime import MountedNode
from .runtime import normalize_child
from .scheduler import TkScheduler
from .tk_props import ButtonProps
from .tk_props import CheckbuttonProps
from .tk_props import EntryProps
from .tk_props import FrameProps
from .tk_props import LabelProps
from .tk_props import LayoutProps
from .tk_props import Padding
from .tk_props import StackAlign
from .tk_props import StackItemProps
from .tk_props import StackProps
from .tk_props import TkProps

LAYOUT_KEYS = {"pack", "grid", "place"}
INTERNAL_KEYS = {"children", "layout"}
STACK_KEYS = {"align", "fill", "gap", "grow", "padding"}
STACK_ITEM_KEYS = {"align", "fill", "grow", "pack"}


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

        self.mount_children()
        self.owner.run_mounts()

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

            self.owner.effect(make_apply(name, accessor), accepts_cleanup=False)


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


class RootNode(WidgetNode):
    skipped_props = {"title"}

    def mount(self, parent: Any | None = None) -> Any:
        widget = super().mount(None)
        if "title" in self.props:
            accessor = self.props.prop_accessor("title")

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
    apply_style(props)
    return RootNode(tk.Tk, children=children, layout={}, **props)


def Frame(*children: Any, **props: Unpack[FrameProps]) -> WidgetNode:
    apply_style(props)
    layout = consume_layout(props)
    return WidgetNode(tk.Frame, children=children, layout=layout, **props)


def Label(*children: Any, **props: Unpack[LabelProps]) -> WidgetNode:
    apply_style(props)
    layout = consume_layout(props)
    return WidgetNode(tk.Label, children=children, layout=layout, **props)


def Button(*children: Any, **props: Unpack[ButtonProps]) -> WidgetNode:
    apply_style(props)
    layout = consume_layout(props)
    return WidgetNode(tk.Button, children=children, layout=layout, **props)


def Entry(*children: Any, **props: Unpack[EntryProps]) -> WidgetNode:
    apply_style(props)
    layout = consume_layout(props)
    return ValueWidgetNode(tk.Entry, children=children, layout=layout, **props)


def Checkbutton(*children: Any, **props: Unpack[CheckbuttonProps]) -> WidgetNode:
    apply_style(props)
    layout = consume_layout(props)
    return WidgetNode(tk.Checkbutton, children=children, layout=layout, **props)


def Item(child: Any, **props: Unpack[StackItemProps]) -> Any:
    apply_style(props)
    node = normalize_child(child)
    setattr(node, "_stack_layout", dict(props))
    return node


def VStack(*children: Any, **props: Unpack[StackProps]) -> WidgetNode:
    apply_style(props)
    stack = consume_stack(props, axis="vertical")
    layout = consume_layout(props)
    node = WidgetNode(tk.Frame, children=children, layout=layout, **props)
    apply_stack_layout(node.children, stack)
    return node


def HStack(*children: Any, **props: Unpack[StackProps]) -> WidgetNode:
    apply_style(props)
    stack = consume_stack(props, axis="horizontal")
    layout = consume_layout(props)
    node = WidgetNode(tk.Frame, children=children, layout=layout, **props)
    apply_stack_layout(node.children, stack)
    return node


def apply_style(props: Any) -> None:
    if "style" not in props:
        return
    styled = props.pop("style")
    overrides = dict(props)
    props.clear()
    props.update(style_api.merge(styled, overrides))


def consume_layout(props: LayoutProps) -> dict[str, Any]:
    for key in ("pack", "grid", "place"):
        if key in props:
            return {key: props.pop(key)}
    return {"pack": {}}


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
