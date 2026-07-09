from __future__ import annotations

from types import SimpleNamespace

import pytest
from fakes import FakeDoubleVar
from fakes import FakePhotoImage
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
        Canvas=FakeWidget,
        Checkbutton=FakeWidget,
        DoubleVar=FakeDoubleVar,
        Entry=FakeWidget,
        Frame=FakeWidget,
        Label=FakeWidget,
        LabelFrame=FakeWidget,
        Listbox=FakeWidget,
        Menu=FakeWidget,
        Menubutton=FakeWidget,
        Message=FakeWidget,
        OptionMenu=FakeWidget,
        PanedWindow=FakeWidget,
        PhotoImage=FakePhotoImage,
        Radiobutton=FakeWidget,
        Scale=FakeWidget,
        Scrollbar=FakeWidget,
        Spinbox=FakeWidget,
        StringVar=FakeStringVar,
        Text=FakeWidget,
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
            LabeledScale=FakeWidget,
            LabelFrame=FakeWidget,
            Labelframe=FakeWidget,
            Label=FakeWidget,
            Menubutton=FakeWidget,
            Notebook=FakeWidget,
            OptionMenu=FakeWidget,
            PanedWindow=FakeWidget,
            Panedwindow=FakeWidget,
            Progressbar=FakeWidget,
            Radiobutton=FakeWidget,
            Scale=FakeWidget,
            Scrollbar=FakeWidget,
            Separator=FakeWidget,
            Sizegrip=FakeWidget,
            Spinbox=FakeWidget,
            Style=FakeStyle,
            Treeview=FakeWidget,
        ),
    )
