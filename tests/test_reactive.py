from __future__ import annotations

from solid_tk import reactive


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
