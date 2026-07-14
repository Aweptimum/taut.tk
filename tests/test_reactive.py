from __future__ import annotations

from reaktiv import Effect

from taut import reactive
from taut import runtime


def test_create_signal_sets_values_and_updates_from_current_value():
    count, set_count = reactive.create_signal(0)

    set_count(2)

    assert count() == 2

    set_count(lambda value: value + 1)

    assert count() == 3


def test_create_selector_matches_current_source_value():
    selected, set_selected = reactive.create_signal("a")
    is_selected = reactive.create_selector(selected)

    assert is_selected("a") is True
    assert is_selected("b") is False

    set_selected("b")

    assert is_selected("a") is False
    assert is_selected("b") is True


def test_create_selector_accepts_custom_equality():
    selected, set_selected = reactive.create_signal({"id": 1})
    is_selected = reactive.create_selector(
        selected,
        equals=lambda key, value: key == value["id"],
    )

    assert is_selected(1) is True
    assert is_selected(2) is False

    set_selected({"id": 2})

    assert is_selected(1) is False
    assert is_selected(2) is True


def test_memo_runs_under_owner_where_it_was_created():
    source, set_source = reactive.create_signal(0)
    owner = runtime.Owner()
    owners = []

    with runtime.use_owner(owner):
        memo = reactive.create_memo(
            lambda: (source(), owners.append(runtime.get_current_owner()))[0]
        )

    assert memo() == 0

    set_source(1)

    assert memo() == 1
    assert owners == [owner, owner]


def test_memo_keeps_creation_owner_when_read_under_another_owner():
    creation_owner = runtime.Owner()
    reading_owner = runtime.Owner()

    with runtime.use_owner(creation_owner):
        memo = reactive.create_memo(runtime.get_current_owner)

    with runtime.use_owner(reading_owner):
        observed_owner = memo()

    assert observed_owner is creation_owner


def test_on_tracks_only_explicit_source():
    source, set_source = reactive.create_signal("a")
    incidental, set_incidental = reactive.create_signal(0)
    events = []
    effect = Effect(reactive.on(source, lambda value: events.append((value, incidental()))))

    assert events == [("a", 0)]

    set_incidental(1)

    assert events == [("a", 0)]

    set_source("b")

    assert events == [("a", 0), ("b", 1)]

    effect.dispose()


def test_on_can_defer_initial_run():
    source, set_source = reactive.create_signal("a")
    events = []
    effect = Effect(reactive.on(source, lambda value: events.append(value), defer=True))

    assert events == []

    set_source("b")

    assert events == ["b"]

    effect.dispose()


def test_untrack_reads_without_subscribing_effect():
    tracked, set_tracked = reactive.create_signal("a")
    incidental, set_incidental = reactive.create_signal(0)
    events = []
    effect = Effect(lambda: events.append((tracked(), reactive.untrack(incidental))))

    assert events == [("a", 0)]

    set_incidental(1)

    assert events == [("a", 0)]

    set_tracked("b")

    assert events == [("a", 0), ("b", 1)]

    effect.dispose()


def test_error_handler_runs_under_owner_where_error_occurred():
    owners = []
    boundary = runtime.Owner(
        error_handler=lambda error: owners.append(runtime.get_current_owner())
    )
    source = runtime.Owner(parent=boundary)

    source.handle_error(ValueError("boom"))

    assert owners == [source]


def test_error_thrown_by_handler_is_forwarded_under_parent_owner():
    events = []

    def outer_handler(error):
        events.append((str(error), runtime.get_current_owner()))

    def inner_handler(error):
        events.append((str(error), runtime.get_current_owner()))
        raise RuntimeError("handler failed")

    outer = runtime.Owner(error_handler=outer_handler)
    inner = runtime.Owner(parent=outer, error_handler=inner_handler)
    source = runtime.Owner(parent=inner)

    source.handle_error(ValueError("original"))

    assert events == [
        ("original", source),
        ("handler failed", outer),
    ]
