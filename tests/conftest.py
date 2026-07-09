from __future__ import annotations

from types import SimpleNamespace

import pytest
from fakes import FakeStringVar
from fakes import FakeStyle
from fakes import FakeTk
from fakes import FakeWidget

from solid_tk import layout
from solid_tk import nodes
from solid_tk import tk
from solid_tk import ttk


@pytest.fixture(autouse=True)
def fake_tk(monkeypatch):
    FakeStyle.configured = {}
    ttk._configured_styles.clear()
    fake_tk = SimpleNamespace(
        Button=FakeWidget,
        Checkbutton=FakeWidget,
        Entry=FakeWidget,
        Frame=FakeWidget,
        Label=FakeWidget,
        StringVar=FakeStringVar,
        Tk=FakeTk,
        Toplevel=FakeWidget,
    )
    monkeypatch.setattr(
        tk,
        "tk",
        fake_tk,
    )
    monkeypatch.setattr(layout, "tk", fake_tk)
    monkeypatch.setattr(nodes, "tk", fake_tk)
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
