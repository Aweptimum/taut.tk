from __future__ import annotations

from dataclasses import dataclass

from solid_tk import runtime
from solid_tk import stores
from solid_tk import widgets


@dataclass(frozen=True)
class User:
    name: str
    age: int


@dataclass(frozen=True)
class AppState:
    user: User
    todos: list[str]


class MutableUser:
    def __init__(self, name: str, todos: list[str]) -> None:
        self.name = name
        self.todos = todos


def test_store_setter_replaces_state():
    state, set_state = stores.create_store({"count": 0})

    set_state({"count": 1})

    assert state() == {"count": 1}


def test_store_setter_updates_state():
    state, set_state = stores.create_store({"count": 0})

    set_state(lambda current: {**current, "count": current["count"] + 1})

    assert state() == {"count": 1}


def test_store_lens_updates_nested_mapping_value():
    state, set_state = stores.create_store({"user": {"name": "Ada", "age": 36}})
    name = set_state.at("user", "name")

    name.set("Grace")

    assert name() == "Grace"
    assert state() == {"user": {"name": "Grace", "age": 36}}


def test_store_lens_updates_nested_list_value():
    state, set_state = stores.create_store({"todos": ["wire props", "own effects"]})
    first = set_state.at("todos", 0)

    first.update(str.upper)

    assert first() == "WIRE PROPS"
    assert state() == {"todos": ["WIRE PROPS", "own effects"]}


def test_store_lens_updates_dataclass_field():
    state, set_state = stores.create_store(
        AppState(user=User(name="Ada", age=36), todos=["ship stores"])
    )
    name = set_state.at("user", "name")

    name.set("Grace")

    assert name() == "Grace"
    assert state() == AppState(user=User(name="Grace", age=36), todos=["ship stores"])


def test_produce_updates_with_mutable_draft():
    state, set_state = stores.create_store({"todos": ["wire props"]})

    set_state(stores.produce(lambda draft: draft["todos"].append("ship stores")))

    assert state() == {"todos": ["wire props", "ship stores"]}


def test_produce_can_return_replacement():
    state, set_state = stores.create_store({"count": 1})

    set_state(stores.produce(lambda draft: {"count": draft["count"] + 1}))

    assert state() == {"count": 2}


def test_reconcile_updates_nested_values_and_preserves_equal_branches():
    profile = {"name": "Ada", "age": 36}
    current_todos = ["wire props"]
    state, set_state = stores.create_store({"profile": profile, "todos": current_todos})

    set_state(
        stores.reconcile({"profile": {"name": "Ada", "age": 37}, "todos": current_todos})
    )

    assert state()["profile"] == {"name": "Ada", "age": 37}
    assert state()["todos"] is current_todos


def test_reconcile_updates_dataclass_values():
    state, set_state = stores.create_store(
        AppState(user=User(name="Ada", age=36), todos=["ship stores"])
    )

    set_state(
        stores.reconcile(AppState(user=User(name="Ada", age=37), todos=["ship stores"]))
    )

    assert state() == AppState(user=User(name="Ada", age=37), todos=["ship stores"])


def test_unwrap_reads_store_accessors_lenses_and_nested_values():
    state, set_state = stores.create_store({"user": {"name": "Ada"}})
    name = set_state.at("user", "name")

    assert stores.unwrap(state) == {"user": {"name": "Ada"}}
    assert stores.unwrap({"name": name}) == {"name": "Ada"}


def test_create_mutable_list_mutates_in_place_and_snapshots():
    items = stores.create_mutable(["a"])

    items.append("b")
    items[0] = "A"
    del items[1]
    items.extend(["c", "d"])
    items.replace(["x", "y"])

    assert items.snapshot() == ["x", "y"]
    assert list(items) == ["x", "y"]
    assert items == ["x", "y"]


def test_create_mutable_list_notifies_reactive_reads():
    items = stores.create_mutable(["a"])
    seen = []

    def App():
        runtime.create_effect(lambda: seen.append(tuple(items)))
        return widgets.Label(text="Mutable")

    mount = runtime.create_root(
        App,
        title="Demo",
    )

    assert seen == [("a",)]

    items.append("b")
    items[0] = "A"
    items.replace(["x"])

    assert seen == [("a",), ("a", "b"), ("A", "b"), ("x",)]

    mount.dispose()


def test_create_mutable_wraps_nested_mapping_and_list_values():
    state = stores.create_mutable({"user": {"name": "Ada"}, "todos": ["wire props"]})
    seen = []

    def App():
        runtime.create_effect(
            lambda: seen.append((state["user"]["name"], tuple(state["todos"])))
        )
        return widgets.Label(text="Mutable")

    mount = runtime.create_root(App, title="Demo")

    assert seen == [("Ada", ("wire props",))]

    state["user"]["name"] = "Grace"
    state["todos"].append("own effects")

    assert seen == [
        ("Ada", ("wire props",)),
        ("Grace", ("wire props",)),
        ("Grace", ("wire props", "own effects")),
    ]
    assert stores.unwrap(state) == {
        "user": {"name": "Grace"},
        "todos": ["wire props", "own effects"],
    }

    mount.dispose()


def test_create_mutable_wraps_attribute_objects():
    user = stores.create_mutable(MutableUser("Ada", ["wire props"]))
    seen = []

    def App():
        runtime.create_effect(lambda: seen.append((user.name, tuple(user.todos))))
        return widgets.Label(text="Mutable")

    mount = runtime.create_root(App, title="Demo")

    assert seen == [("Ada", ("wire props",))]

    user.name = "Grace"
    user.todos.append("own effects")

    assert seen == [
        ("Ada", ("wire props",)),
        ("Grace", ("wire props",)),
        ("Grace", ("wire props", "own effects")),
    ]
    assert stores.unwrap(user) == {
        "name": "Grace",
        "todos": ["wire props", "own effects"],
    }

    mount.dispose()
