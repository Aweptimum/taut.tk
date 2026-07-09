from __future__ import annotations

import threading
import time
from collections.abc import Callable

from reaktiv import Signal

from solid_tk import Button
from solid_tk import Frame
from solid_tk import HStack
from solid_tk import Label
from solid_tk import VStack
from solid_tk import after
from solid_tk import component
from solid_tk import defer
from solid_tk import interval
from solid_tk import on_mount
from solid_tk import to_ui


@component
def scheduler_demo(props):
    tick = Signal(0)
    running = Signal(True)
    deferred_text = Signal("defer: waiting for next event-loop turn")
    delayed_text = Signal("after: scheduled for 900ms")
    worker_text = Signal("to_ui: worker has not reported yet")

    ticker = Label(
        text=lambda: f"interval: tick {tick()}",
        bg="#dbeafe",
        padx=6,
        pady=3,
        place={"x": 12, "y": 22},
    )
    deferred = Label(
        text=deferred_text,
        bg="#dcfce7",
        padx=6,
        pady=3,
        place={"x": 12, "y": 62},
    )
    delayed = Label(
        text=delayed_text,
        bg="#fef3c7",
        padx=6,
        pady=3,
        place={"x": 12, "y": 102},
    )
    worker = Label(
        text=worker_text,
        bg="#fce7f3",
        padx=6,
        pady=3,
        place={"x": 12, "y": 142},
    )

    def setup() -> Callable[[], None]:
        stop_worker = threading.Event()
        dispatch = to_ui()

        def move_ticker() -> None:
            if not running():
                return
            tick.update(lambda value: value + 1)
            if ticker.widget is not None:
                ticker.widget.place_configure(x=12 + (tick() * 18) % 260)

        def move_deferred() -> None:
            deferred_text.set("defer: ran after mount")
            if deferred.widget is not None:
                deferred.widget.place_configure(x=190)

        def finish_delay() -> None:
            delayed_text.set("after: fired once")
            if delayed.widget is not None:
                delayed.widget.place_configure(x=150)

        def worker_task() -> None:
            time.sleep(5)
            if stop_worker.is_set():
                return
            dispatch(lambda: worker_text.set("to_ui: delivered from worker"))
            dispatch(lambda: worker.widget.place_configure(x=96) if worker.widget else None)

        interval(120, move_ticker)
        defer(move_deferred)
        after(900, finish_delay)
        threading.Thread(target=worker_task, daemon=True).start()

        return stop_worker.set

    on_mount(setup)

    return VStack(
        Label(text="Scheduler demo"),
        HStack(
            Button(text="Pause interval", on_click=lambda: running.set(False)),
            Button(text="Resume interval", on_click=lambda: running.set(True)),
        ),
        Frame(
            ticker,
            deferred,
            delayed,
            worker,
            width=420,
            height=190,
            relief="sunken",
            bd=1,
            padx=6,
            pady=6,
        ),
        padx=12,
        pady=12,
    )
