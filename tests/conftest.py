from __future__ import annotations

from types import SimpleNamespace

import pytest
from fakes import FakeStringVar
from fakes import FakeStyle
from fakes import FakeTk
from fakes import FakeWidget

from solid_tk import ttk
from solid_tk import widgets


@pytest.fixture(autouse=True)
def fake_tk(monkeypatch):
    FakeStyle.configured = {}
    ttk._configured_styles.clear()
    monkeypatch.setattr(
        widgets,
        "tk",
        SimpleNamespace(
            Button=FakeWidget,
            Checkbutton=FakeWidget,
            Entry=FakeWidget,
            Frame=FakeWidget,
            Label=FakeWidget,
            StringVar=FakeStringVar,
            Tk=FakeTk,
        ),
    )
    monkeypatch.setattr(
        ttk,
        "ttk",
        SimpleNamespace(
            Button=FakeWidget,
            Checkbutton=FakeWidget,
            Combobox=FakeWidget,
            Entry=FakeWidget,
            Frame=FakeWidget,
            Label=FakeWidget,
            Progressbar=FakeWidget,
            Separator=FakeWidget,
            Style=FakeStyle,
        ),
    )
