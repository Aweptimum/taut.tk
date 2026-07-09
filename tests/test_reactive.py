from __future__ import annotations

from solid_tk import create_signal


def test_create_signal_sets_values_and_updates_from_current_value():
    count, set_count = create_signal(0)

    set_count(2)

    assert count() == 2

    set_count(lambda value: value + 1)

    assert count() == 3
