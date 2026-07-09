from __future__ import annotations

import threading
import time
from collections.abc import Callable

from taut import component
from taut.layout import HStack
from taut.layout import VStack
from taut.reactive import create_signal
from taut.runtime import after
from taut.runtime import defer
from taut.runtime import interval
from taut.runtime import on_mount
from taut.runtime import to_ui
from taut.tk import Button
from taut.tk import Frame
from taut.tk import Label


@component
def scheduler_demo(props):
    tick, set_tick = create_signal(0)
    running, set_running = create_signal(True)
    deferred_text, set_deferred_text = create_signal("defer: waiting for next event-loop turn")
    delayed_text, set_delayed_text = create_signal("after: scheduled for 900ms")
    worker_text, set_worker_text = create_signal("to_ui: worker has not reported yet")

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
            set_tick(lambda value: value + 1)
            if ticker.widget is not None:
                ticker.widget.place_configure(x=12 + (tick() * 18) % 260)

        def move_deferred() -> None:
            set_deferred_text("defer: ran after mount")
            if deferred.widget is not None:
                deferred.widget.place_configure(x=190)

        def finish_delay() -> None:
            set_delayed_text("after: fired once")
            if delayed.widget is not None:
                delayed.widget.place_configure(x=150)

        def worker_task() -> None:
            time.sleep(5)
            if stop_worker.is_set():
                return
            dispatch(lambda: set_worker_text("to_ui: delivered from worker"))
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
            Button(text="Pause interval", on_click=lambda: set_running(False)),
            Button(text="Resume interval", on_click=lambda: set_running(True)),
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
