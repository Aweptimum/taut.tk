from __future__ import annotations

from typing import Any
from typing import cast

from taut import reactive
from taut import runtime
from taut import tk


def test_portal_mounts_child_in_toplevel():
    mount = runtime.create_root(
        lambda: tk.Portal(lambda: tk.Label(text="Dialog"), title="Settings"),
        title="Demo",
    )
    portal = cast(Any, mount.node).children[0]
    toplevel = portal.widget

    assert toplevel.parent is mount.widget
    assert toplevel.props["title"] == "Settings"
    assert toplevel.children[0].props["text"] == "Dialog"
    assert "WM_DELETE_WINDOW" in toplevel.protocols


def test_portal_mounts_fragment_children_in_toplevel():
    mount = runtime.create_root(
        lambda: tk.Portal(
            lambda: tk.Fragment(
                tk.Label(text="One"),
                tk.Label(text="Two"),
            ),
            title="Settings",
        ),
        title="Demo",
    )
    portal = cast(Any, mount.node).children[0]
    toplevel = portal.widget

    assert [child.props["text"] for child in toplevel.children] == ["One", "Two"]


def test_portal_close_runs_callback_and_destroys_toplevel():
    events = []
    mount = runtime.create_root(
        lambda: tk.Portal(
            lambda: tk.Label(text="Dialog"),
            title="Settings",
            on_close=lambda: events.append("closed"),
        ),
        title="Demo",
    )
    portal = cast(Any, mount.node).children[0]
    toplevel = portal.widget

    toplevel.protocols["WM_DELETE_WINDOW"]()

    assert events == ["closed"]
    assert toplevel.destroyed
    assert portal.widget is None


def test_portal_close_callback_runs_with_portal_owner():
    callbacks = []

    def handle_close():
        callbacks.append(runtime.get_current_owner())
        runtime.after(10, lambda: None)

    mount = runtime.create_root(
        lambda: tk.Portal(
            lambda: tk.Label(text="Dialog"),
            on_close=handle_close,
        ),
        title="Demo",
    )
    portal = cast(Any, mount.node).children[0]
    toplevel = portal.widget

    toplevel.protocols["WM_DELETE_WINDOW"]()

    assert callbacks == [portal.owner]
    assert toplevel.after_cancelled == ["after-1"]


def test_portal_close_is_idempotent():
    events = []
    mount = runtime.create_root(
        lambda: tk.Portal(
            lambda: tk.Label(text="Dialog"),
            title="Settings",
            on_close=lambda: events.append("closed"),
        ),
        title="Demo",
    )
    portal = cast(Any, mount.node).children[0]
    toplevel = portal.widget

    portal.close()
    portal.close()
    portal.unmount()

    assert events == ["closed"]
    assert toplevel.destroy_count == 1
    assert portal.widget is None


def test_portal_title_tracks_signal():
    title, set_title = reactive.create_signal("Settings")

    mount = runtime.create_root(
        lambda: tk.Portal(lambda: tk.Label(text="Dialog"), title=title),
        title="Demo",
    )
    portal = cast(Any, mount.node).children[0]
    toplevel = portal.widget

    assert toplevel.props["title"] == "Settings"

    set_title("Preferences")

    assert toplevel.props["title"] == "Preferences"


def test_portal_disposes_with_root():
    mount = runtime.create_root(
        lambda: tk.Portal(lambda: tk.Label(text="Dialog"), title="Settings"),
        title="Demo",
    )
    portal = cast(Any, mount.node).children[0]
    toplevel = portal.widget

    mount.dispose()

    assert toplevel.destroyed
    assert portal.widget is None
