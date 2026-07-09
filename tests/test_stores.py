from __future__ import annotations

from dataclasses import dataclass

from solid_tk import stores


@dataclass(frozen=True)
class User:
    name: str
    age: int


@dataclass(frozen=True)
class AppState:
    user: User
    todos: list[str]


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
