from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Any
from typing import Unpack

from .nodes import ValueWidgetNode
from .nodes import WidgetNode
from .nodes import apply_style
from .nodes import consume_layout
from .props import NodeProps
from .runtime import Fragment
from .runtime import MountedNode
from .runtime import Node
from .runtime import mount_child_tree
from .runtime import normalize_child
from .runtime import set_primitive_child_factory
from .runtime import use_owner
from .scheduler import TkScheduler
from .tk_props import ButtonProps
from .tk_props import CheckbuttonProps
from .tk_props import EntryProps
from .tk_props import FrameProps
from .tk_props import LabelProps
from .tk_props import PortalProps
from .tk_props import TkProps


class RootNode(WidgetNode):
    skipped_props = {"title"}

    def mount(self, parent: Any | None = None) -> Any:
        widget = super().mount(None)
        widget.protocol("WM_DELETE_WINDOW", self.unmount)
        if "title" in self.props:
            accessor = self.props.prop_accessor("title")

            def apply_title() -> None:
                if self.widget is not None:
                    self.widget.title(accessor())

            self.owner.effect(apply_title)
        return widget

    def unmount(self) -> None:
        # TODO: Test whether hiding the root before teardown improves close
        # latency on native Tk. On WSL/X11, withdraw() followed by an update
        # left a visible artifacted shell during close. Uncomment below:
        # widget = self.widget
        # if widget is not None:
        #     withdraw = getattr(widget, "withdraw", None)
        #     update = getattr(widget, "update", None)
        #     if callable(withdraw):
        #         withdraw()
        #         if callable(update):
        #             update()
        self.unmount_children()
        self.owner.dispose()
        widget = self.widget
        self.widget = None
        if widget is not None:
            widget.quit()
            widget.destroy()


class PortalNode(MountedNode):
    def __init__(
        self,
        child: Callable[[], Any] | Any,
        *,
        title: Any | None = None,
        on_close: Callable[[], Any] | None = None,
    ) -> None:
        super().__init__()
        self.child_source = child
        self.child: Node | None = None
        self.title = title
        self.on_close = on_close

    def mount(self, parent: Any | None) -> Any:
        self.widget = tk.Toplevel(parent)
        self.owner.scheduler = TkScheduler(self.widget)
        self.widget.protocol("WM_DELETE_WINDOW", self.close)

        if self.title is not None:
            title = NodeProps({"title": self.title}).prop_accessor("title")

            def apply_title() -> None:
                if self.widget is not None:
                    self.widget.title(title())

            self.owner.effect(apply_title)

        with use_owner(self.owner):
            self.child = normalize_child(resolve_portal_child(self.child_source))
        mount_child_tree(self.widget, self.child)
        self.owner.run_mounts()
        return self.widget

    def close(self) -> None:
        if self.widget is None and self.child is None:
            return
        if self.on_close is not None:
            self.on_close()
        if self.widget is not None or self.child is not None:
            self.unmount()

    def unmount(self) -> None:
        if self.widget is None and self.child is None:
            return
        if self.child is not None:
            self.child.unmount()
            self.child = None
        self.owner.dispose()
        widget = self.widget
        self.widget = None
        if widget is not None:
            widget.destroy()


def Tk(*children: Any, **props: Unpack[TkProps]) -> RootNode:
    apply_style(props)
    return RootNode(tk.Tk, children=children, layout={}, **props)


def Portal(child: Callable[[], Any] | Any, **props: Unpack[PortalProps]) -> PortalNode:
    return PortalNode(
        child,
        title=props.get("title"),
        on_close=props.get("on_close"),
    )


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


def resolve_portal_child(child: Callable[[], Any] | Any) -> Any:
    while callable(child) and not (hasattr(child, "mount") and hasattr(child, "unmount")):
        child = child()
    return child


set_primitive_child_factory(lambda child: Label(text=str(child)))

__all__ = [
    "Button",
    "Checkbutton",
    "Entry",
    "Frame",
    "Fragment",
    "Label",
    "Portal",
    "Tk",
]
