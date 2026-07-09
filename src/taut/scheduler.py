from __future__ import annotations

from collections.abc import Callable
from typing import Any
from typing import Protocol


class CancelHandle(Protocol):
    def cancel(self) -> None: ...


class EventScheduler(Protocol):
    def after(self, ms: int, fn: Callable[[], Any]) -> CancelHandle: ...

    def to_ui(self, fn: Callable[[], Any]) -> CancelHandle: ...


class TkCancelHandle:
    def __init__(self, widget: Any, after_id: str) -> None:
        self.widget = widget
        self.after_id = after_id
        self.cancelled = False
        self.finished = False

    def cancel(self) -> None:
        if self.cancelled or self.finished:
            return
        self.cancelled = True
        self.widget.after_cancel(self.after_id)

    def finish(self) -> None:
        self.finished = True


class TkScheduler:
    def __init__(self, widget: Any) -> None:
        self.widget = widget

    def after(self, ms: int, fn: Callable[[], Any]) -> CancelHandle:
        handle: TkCancelHandle | None = None

        def run() -> Any:
            if handle is not None:
                handle.finish()
            return fn()

        after_id = self.widget.after(max(0, ms), run)
        handle = TkCancelHandle(self.widget, after_id)
        return handle

    def to_ui(self, fn: Callable[[], Any]) -> CancelHandle:
        return self.after(0, fn)
