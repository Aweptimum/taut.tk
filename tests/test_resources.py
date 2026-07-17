from __future__ import annotations

from threading import Event
from time import monotonic
from time import sleep
from typing import Optional
from typing import cast

from taut import component
from taut import reactive
from taut import resource
from taut import runtime
from taut import tk


def run_pending_ui(widget, *, limit: int = 20) -> None:
    runs = 0
    while widget.after_callbacks and runs < limit:
        runs += 1
        widget.run_next_after()
    assert widget.after_callbacks == {}


def wait_until(condition, timeout: float = 1) -> None:
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        if condition():
            return
        sleep(0.001)
    assert condition()


def wait_for_ui_callback(widget) -> None:
    wait_until(lambda: bool(widget.after_callbacks))


def test_resource_resolves_on_ui_thread():
    done = Event()
    resources = []

    def fetcher(source, info):
        done.wait(1)
        return f"{source}:done:{info['value']}"

    @component
    def App(props):
        res, _actions = resource.create_resource(fetcher, None)
        resources.append(res)
        return tk.Label(text=lambda: res() or "loading")

    mount = runtime.create_root(App, title="Demo")
    label = mount.widget.children[0]
    res = resources[0]

    assert res.loading() is True
    assert res.state() == "pending"
    assert label.props["text"] == "loading"

    done.set()
    wait_for_ui_callback(mount.widget)
    run_pending_ui(mount.widget)

    assert res() == "True:done:None"
    assert res.latest() == "True:done:None"
    assert res.error() is None
    assert res.loading() is False
    assert res.state() == "ready"
    assert label.props["text"] == "True:done:None"


def test_resource_rejects_on_ui_thread():
    done = Event()
    resources = []

    def fetcher(source, info):
        done.wait(1)
        raise ValueError("boom")

    @component
    def App(props):
        res, _actions = resource.create_resource(fetcher, None)
        resources.append(res)
        return tk.Label(text="App")

    mount = runtime.create_root(App, title="Demo")
    res = resources[0]

    done.set()
    wait_for_ui_callback(mount.widget)
    run_pending_ui(mount.widget)

    assert isinstance(res.error(), ValueError)
    assert str(res.error()) == "boom"
    assert res.loading() is False
    assert res.state() == "errored"


def test_resource_passes_source_value_to_fetcher_and_refetches_when_source_changes():
    calls = []
    resources = []
    source, set_source = reactive.create_signal("alpha")

    def fetcher(source, info):
        calls.append((source, info["value"], info["refetching"]))
        return source.upper()

    @component
    def App(props):
        res, _actions = resource.create_resource(fetcher, None, source)
        resources.append(res)
        return tk.Label(text=lambda: res() or "loading")

    mount = runtime.create_root(App, title="Demo")

    wait_for_ui_callback(mount.widget)
    run_pending_ui(mount.widget)

    set_source("beta")
    wait_for_ui_callback(mount.widget)
    run_pending_ui(mount.widget)

    assert calls == [
        ("alpha", None, False),
        ("beta", "ALPHA", False),
    ]
    assert resources[0]() == "BETA"


def test_resource_does_not_fetch_for_disabled_source_until_enabled():
    calls = []
    resources = []
    source, set_source = reactive.create_signal(cast(Optional[str], None))

    def fetcher(source, info):
        calls.append(source)
        return f"value:{source}"

    @component
    def App(props):
        res, _actions = resource.create_resource(fetcher, None, source)
        resources.append(res)
        return tk.Label(text="App")

    mount = runtime.create_root(App, title="Demo")
    res = resources[0]

    assert calls == []
    assert res.loading() is False
    assert res.state() == "unresolved"

    set_source("ready")
    wait_for_ui_callback(mount.widget)
    run_pending_ui(mount.widget)

    assert calls == ["ready"]
    assert res() == "value:ready"
    assert res.state() == "ready"


@pytest.mark.parametrize("disabled", [None, False])
def test_resource_ignores_in_flight_result_when_source_is_disabled(disabled):
    done = Event()
    resources = []
    source, set_source = reactive.create_signal(cast(str | bool | None, "ready"))

    def fetcher(source, info):
        done.wait(1)
        return f"value:{source}"

    @component
    def App(props):
        res, _actions = resource.create_resource(fetcher, None, source)
        resources.append(res)
        return tk.Label(text="App")

    mount = runtime.create_root(App, title="Demo")
    res = resources[0]

    assert res.loading() is True
    assert res.state() == "pending"

    set_source(disabled)

    assert res.loading() is False
    assert res.state() == "unresolved"

    done.set()
    wait_for_ui_callback(mount.widget)
    run_pending_ui(mount.widget)

    assert res() is None
    assert res.loading() is False
    assert res.state() == "unresolved"


def test_resource_refetch_passes_custom_refetch_info_and_refreshing_state():
    calls = []
    resources = []
    actions = []

    def fetcher(source, info):
        calls.append((source, info["value"], info["refetching"]))
        return f"result:{len(calls)}"

    @component
    def App(props):
        res, resource_actions = resource.create_resource(fetcher, None)
        resources.append(res)
        actions.append(resource_actions)
        return tk.Label(text=lambda: res() or "loading")

    mount = runtime.create_root(App, title="Demo")
    run_pending_ui(mount.widget)
    res = resources[0]
    _mutate, refetch = actions[0]

    assert res() == "result:1"

    refetch("manual")

    assert res.loading() is True
    assert res.state() == "refreshing"

    run_pending_ui(mount.widget)

    assert calls == [
        (True, None, False),
        (True, "result:1", "manual"),
    ]
    assert res() == "result:2"


def test_resource_mutate_updates_value_without_fetching():
    calls = []
    resources = []
    actions = []

    def fetcher(source, info):
        calls.append(source)
        return 1

    @component
    def App(props):
        res, resource_actions = resource.create_resource(fetcher, None)
        resources.append(res)
        actions.append(resource_actions)
        return tk.Label(text=lambda: str(res()))

    mount = runtime.create_root(App, title="Demo")
    run_pending_ui(mount.widget)
    res = resources[0]
    mutate, _refetch = actions[0]

    mutate(lambda previous: (previous or 0) + 1)

    assert calls == [True]
    assert res() == 2
    assert res.latest() == 2
    assert res.loading() is False
    assert res.state() == "ready"


def test_resource_ignores_stale_results():
    pending = []
    resources = []
    actions = []

    def fetcher(source, info):
        done = Event()
        result = f"result:{len(pending) + 1}"
        pending.append((result, done))
        done.wait(1)
        return result

    @component
    def App(props):
        res, resource_actions = resource.create_resource(fetcher, None)
        resources.append(res)
        actions.append(resource_actions)
        return tk.Label(text=lambda: res() or "loading")

    mount = runtime.create_root(App, title="Demo")
    res = resources[0]
    _mutate, refetch = actions[0]

    refetch("newer")

    wait_until(lambda: len(pending) == 2)

    first_result, first_done = pending[0]
    second_result, second_done = pending[1]
    assert first_result == "result:1"
    assert second_result == "result:2"

    second_done.set()
    wait_for_ui_callback(mount.widget)
    run_pending_ui(mount.widget)

    first_done.set()
    wait_for_ui_callback(mount.widget)
    run_pending_ui(mount.widget)

    assert res() == "result:2"
