from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from dataclasses import field
from inspect import signature
from threading import Lock
from typing import Any
from typing import Protocol

from reaktiv import Effect

from .scheduler import CancelHandle
from .scheduler import EventScheduler

ThreadDispatcher = Callable[[Callable[[], Any]], CancelHandle]


class Node(Protocol):
    widget: Any | None

    def mount(self, parent: Any | None) -> Any: ...

    def unmount(self) -> None: ...


@dataclass
class Mount:
    node: Node
    widget: Any

    def dispose(self) -> None:
        self.node.unmount()


@dataclass
class Owner:
    parent: Owner | None = None
    context: Mapping[Any, Any] = field(default_factory=dict)
    scheduler: EventScheduler | None = None
    error_handler: Callable[[Exception], None] | None = None
    cleanups: list[Callable[[], None]] = field(default_factory=list)
    effects: list[Effect] = field(default_factory=list)
    mounts: list[Callable[[], Any]] = field(default_factory=list)
    mounted: bool = False

    def effect(self, fn: Callable[..., Any], *, accepts_cleanup: bool | None = None) -> Effect:
        if accepts_cleanup is None:
            accepts_cleanup = len(signature(fn).parameters) >= 1

        # Change definition of run for benefit of reaktive.Effect
        # reaktiv.Effect also inspects the signature length 
        if accepts_cleanup:

            def run(on_cleanup: Callable[[Callable[[], None]], None]) -> Any: # pyright: ignore[reportRedeclaration]
                try:
                    with use_owner(self):
                        return fn(on_cleanup)
                except Exception as exc:
                    self.handle_error(exc)
                    return None

        else:

            def run() -> Any:
                try:
                    with use_owner(self):
                        return fn()
                except Exception as exc:
                    self.handle_error(exc)
                    return None

        effect = Effect(run)
        self.effects.append(effect)
        return effect

    def handle_error(self, error: Exception) -> None:
        owner: Owner | None = self
        while owner is not None:
            if owner.error_handler is not None:
                owner.error_handler(error)
                return
            owner = owner.parent
        raise error

    def cleanup(self, fn: Callable[[], None]) -> None:
        self.cleanups.append(fn)

    def on_mount(self, fn: Callable[[], Any]) -> None:
        if self.mounted:
            self._run_mount(fn)
            return
        self.mounts.append(fn)

    def run_mounts(self) -> None:
        self.mounted = True
        mounts = self.mounts
        self.mounts = []
        for fn in mounts:
            self._run_mount(fn)

    def _run_mount(self, fn: Callable[[], Any]) -> None:
        try:
            with use_owner(self):
                cleanup = fn()
        except Exception as exc:
            self.handle_error(exc)
            return
        if callable(cleanup):
            self.cleanup(cleanup)

    def dispose(self) -> None:
        for effect in reversed(self.effects):
            effect.dispose()
        self.effects.clear()

        for cleanup in reversed(self.cleanups):
            cleanup()
        self.cleanups.clear()
        self.mounts.clear()
        self.mounted = False


_current_owner: ContextVar[Owner | None] = ContextVar("solid_tk_current_owner", default=None)


@contextmanager
def use_owner(owner: Owner):
    token = _current_owner.set(owner)
    try:
        yield
    finally:
        _current_owner.reset(token)


def get_current_owner() -> Owner | None:
    """Return the current reactive owner, if code is running inside one."""

    return _current_owner.get()


def current_owner() -> Owner:
    """Return the current owner or raise when lifecycle APIs are used out of scope."""

    owner = get_current_owner()
    if owner is None:
        raise RuntimeError("lifecycle helpers must be called inside a solid-tk owner")
    return owner


def current_scheduler() -> EventScheduler:
    """Return the nearest mounted event scheduler for the current owner tree."""

    owner = current_owner()
    while owner is not None:
        if owner.scheduler is not None:
            return owner.scheduler
        owner = owner.parent
    raise RuntimeError("event loop helpers require a mounted solid-tk root")


def create_effect(fn: Callable[..., Any]) -> Effect:
    """Create an owned reactive effect disposed with the current owner."""

    return current_owner().effect(fn)


def on_cleanup(fn: Callable[[], None]) -> None:
    """Register cleanup to run when the current owner is disposed."""

    current_owner().cleanup(fn)


def on_mount(fn: Callable[[], Any]) -> None:
    """Run a callback after the current owner is mounted.

    If the callback returns another callable, that returned callable is
    registered as owner cleanup.
    """

    current_owner().on_mount(fn)


def after(ms: int, fn: Callable[[], Any]) -> CancelHandle:
    """Schedule ``fn`` once on the current owner's event scheduler.

    The scheduled callback is cancelled automatically when the owner is
    disposed. When it runs, it restores the owner context so lifecycle helpers
    and context lookups still refer to the component that scheduled it.
    """

    owner = current_owner()

    def run() -> Any:
        with use_owner(owner):
            return fn()

    handle = current_scheduler().after(ms, run)
    owner.cleanup(handle.cancel)
    return handle


def defer(fn: Callable[[], Any]) -> CancelHandle:
    """Schedule ``fn`` for the next event-loop turn."""

    return after(0, fn)


def interval(ms: int, fn: Callable[[], Any]) -> CancelHandle:
    """Run ``fn`` repeatedly on the current owner's event scheduler.

    The next tick is scheduled only after ``fn`` returns, so ticks do not pile up
    concurrently. Returning ``False`` stops the interval. The interval is also
    cancelled automatically when the owner is disposed.
    """

    owner = current_owner()
    scheduler = current_scheduler()
    cancelled = False
    active: CancelHandle | None = None

    class IntervalHandle:
        def cancel(self) -> None:
            nonlocal cancelled
            cancelled = True
            if active is not None:
                active.cancel()

    def tick() -> None:
        nonlocal active
        if cancelled:
            return
        with use_owner(owner):
            result = fn()
        if result is False or cancelled:
            return
        active = scheduler.after(ms, tick)

    handle = IntervalHandle()
    active = scheduler.after(ms, tick)
    owner.cleanup(handle.cancel)
    return handle


class NoopCancelHandle:
    def cancel(self) -> None:
        pass


def to_ui() -> ThreadDispatcher:
    """Capture an owner-bound dispatcher for UI work.

    ``dispatch = to_ui(); dispatch(lambda: set_message("done"))``

    Use this inside a component or lifecycle callback, then pass the returned
    dispatcher to worker code that needs to report back to the UI.

    The dispatcher routes the supplied callback back through the owner
    scheduler, restores owner context when it runs, and no-ops after the owner
    has been disposed. The current Tk backend uses Tk's scheduler; a future
    backend can replace that without changing this API.
    """

    owner = current_owner()
    scheduler = current_scheduler()
    cancelled = False
    handles: list[CancelHandle] = []
    lock = Lock()

    def cleanup() -> None:
        nonlocal cancelled
        with lock:
            cancelled = True
            pending = list(handles)
            handles.clear()
        for handle in pending:
            handle.cancel()

    def dispatch(callback: Callable[[], Any]) -> CancelHandle:
        with lock:
            if cancelled:
                return NoopCancelHandle()

        handle: CancelHandle | None = None

        def run() -> Any:
            try:
                with lock:
                    if cancelled:
                        return None
                with use_owner(owner):
                    return callback()
            finally:
                if handle is not None:
                    with lock:
                        if handle in handles:
                            handles.remove(handle)

        handle = scheduler.to_ui(run)
        with lock:
            if cancelled:
                handle.cancel()
                return NoopCancelHandle()
            handles.append(handle)
            return handle

    owner.cleanup(cleanup)
    return dispatch


class MountedNode:
    widget: Any | None = None

    def __init__(self, children: Iterable[Any] = (), *, owner: Owner | None = None) -> None:
        self.owner = owner if owner is not None else Owner(parent=get_current_owner())
        self.children = [normalize_child(child) for child in children]

    def mount_children(self) -> None:
        if self.widget is None:
            return
        for child in self.children:
            child.mount(self.widget)

    def append_child(self, child: Any) -> Node:
        node = normalize_child(child)
        self.children.append(node)
        return node

    def unmount_children(self) -> None:
        for child in reversed(self.children):
            child.unmount()
        self.children.clear()

    def unmount(self) -> None:
        self.unmount_children()
        self.owner.dispose()
        widget = self.widget
        self.widget = None
        if widget is not None:
            widget.destroy()


def normalize_child(child: Any) -> Node:
    if hasattr(child, "mount") and hasattr(child, "unmount"):
        return child
    from .widgets import Label

    return Label(text=str(child))


def create_root(app: Callable[[], Node] | Node, *, title: str | None = None) -> Mount:
    from .widgets import Tk

    root_node = Tk(title=title) if title is not None else Tk()
    root = root_node.mount(None)

    with use_owner(root_node.owner):
        child = app() if callable(app) and not hasattr(app, "mount") else app
    node = root_node.append_child(child)
    expand_root_child(node)
    node.mount(root)
    return Mount(node=root_node, widget=root)


def expand_root_child(node: Node) -> None:
    target: Any = node
    while hasattr(target, "rendered"):
        target = target.rendered
    layout = getattr(target, "layout", None)
    if layout == {"pack": {}}:
        target.layout = {"pack": {"fill": "both", "expand": True}}
