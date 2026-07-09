from __future__ import annotations

import threading

from solid_tk import component
from solid_tk import runtime
from solid_tk import widgets


def test_after_runs_once_and_is_cancelled_on_cleanup():
    events = []

    @component
    def App(props):
        runtime.after(10, lambda: events.append("after"))
        return widgets.Label(text="App")

    mount = runtime.create_root(App, title="Demo")
    after_id = next(iter(mount.widget.after_callbacks))

    mount.dispose()

    assert after_id in mount.widget.after_cancelled
    assert events == []


def test_defer_runs_on_next_event_loop_turn_with_owner_context():
    owners = []

    @component
    def App(props):
        owner = runtime.get_current_owner()
        runtime.defer(lambda: owners.append(runtime.get_current_owner() is owner))
        return widgets.Label(text="App")

    mount = runtime.create_root(App, title="Demo")

    mount.widget.run_next_after()

    assert owners == [True]


def test_defer_can_be_scheduled_from_on_mount():
    events = []

    @component
    def App(props):
        runtime.on_mount(lambda: runtime.defer(lambda: events.append("mounted")))
        return widgets.Label(text="App")

    mount = runtime.create_root(App, title="Demo")

    mount.widget.run_next_after()

    assert events == ["mounted"]


def test_interval_repeats_until_cleanup():
    ticks = []

    @component
    def App(props):
        runtime.interval(5, lambda: ticks.append("tick"))
        return widgets.Label(text="App")

    mount = runtime.create_root(App, title="Demo")

    first_id = mount.widget.run_next_after()
    second_id = mount.widget.run_next_after()

    assert ticks == ["tick", "tick"]

    mount.dispose()

    assert first_id not in mount.widget.after_cancelled
    assert second_id not in mount.widget.after_cancelled
    assert len(mount.widget.after_cancelled) == 1


def test_interval_stops_when_callback_returns_false():
    ticks = []

    @component
    def App(props):
        runtime.interval(5, lambda: ticks.append("tick") or False)
        return widgets.Label(text="App")

    mount = runtime.create_root(App, title="Demo")

    mount.widget.run_next_after()

    assert ticks == ["tick"]
    assert mount.widget.after_callbacks == {}


def test_to_ui_can_capture_dispatcher_for_later_thread_callbacks():
    events = []
    dispatchers = []

    @component
    def App(props):
        dispatchers.append(runtime.to_ui())
        return widgets.Label(text="App")

    mount = runtime.create_root(App, title="Demo")

    dispatchers[0](lambda: events.append("worker result"))
    mount.widget.run_next_after()

    assert events == ["worker result"]

    mount.dispose()
    handle = dispatchers[0](lambda: events.append("too late"))

    handle.cancel()
    assert events == ["worker result"]


def test_to_ui_dispatcher_cancels_callbacks_dispatched_during_disposal():
    events = []
    errors = []
    dispatchers = []

    @component
    def App(props):
        dispatchers.append(runtime.to_ui())
        return widgets.Label(text="App")

    mount = runtime.create_root(App, title="Demo")
    dispatch = dispatchers[0]
    started = threading.Barrier(2)

    def worker():
        try:
            started.wait()
            for _ in range(20):
                dispatch(lambda: events.append("worker result"))
        except Exception as exc:  # pragma: no cover - surfaced by assertion
            errors.append(exc)

    thread = threading.Thread(target=worker)
    thread.start()
    started.wait()
    mount.dispose()
    thread.join()

    while mount.widget.after_callbacks:
        mount.widget.run_next_after()

    assert errors == []
    assert events == []


def test_root_callback_lifecycle_helpers_are_owned():
    events = []

    def App():
        runtime.on_mount(lambda: events.append("mount"))
        runtime.on_cleanup(lambda: events.append("cleanup"))
        return widgets.Label(text="Root")

    mount = runtime.create_root(App, title="Demo")

    assert events == ["mount"]

    mount.dispose()

    assert events == ["mount", "cleanup"]
