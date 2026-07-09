from __future__ import annotations

from fakes import FakeStyle

from solid_tk import reactive
from solid_tk import runtime
from solid_tk import style
from solid_tk import tk
from solid_tk import ttk


def test_tk_namespace_exposes_classic_widgets():
    mount = runtime.create_root(
        lambda: tk.VStack(
            tk.Label(text="Classic"),
            tk.Button(text="OK"),
        ),
        title="Demo",
    )
    stack = mount.widget.children[0]
    label, button = stack.children

    assert label.props["text"] == "Classic"
    assert button.props["text"] == "OK"


def test_ttk_namespace_creates_themed_widgets():
    mount = runtime.create_root(
        lambda: tk.VStack(
            ttk.Label(text="Themed", style="Title.TLabel"),
            ttk.Button(text="OK", style="Accent.TButton"),
            ttk.Separator(orient="horizontal"),
            ttk.Progressbar(value=50, maximum=100),
        ),
        title="Demo",
    )
    label, button, separator, progress = mount.widget.children[0].children

    assert label.props["text"] == "Themed"
    assert label.props["style"] == "Title.TLabel"
    assert button.props["style"] == "Accent.TButton"
    assert separator.props["orient"] == "horizontal"
    assert progress.props["value"] == 50
    assert progress.props["maximum"] == 100


def test_ttk_entry_value_tracks_signal_changes():
    value, set_value = reactive.create_signal("hello")

    mount = runtime.create_root(lambda: ttk.Entry(value=value), title="Demo")
    entry = mount.widget.children[0]
    variable = entry.props["textvariable"]

    assert variable.get() == "hello"

    set_value("world")

    assert variable.get() == "world"


def test_named_styles_can_be_used_with_component_helper():
    title = style.define("title", fg="blue", padding=(4, 2))
    Title = style.component(ttk.Label, title)

    mount = runtime.create_root(lambda: Title(text="Styled"), title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "Styled"
    assert label.props["style"] == "Title.TLabel"
    assert FakeStyle.configured["Title.TLabel"] == {
        "foreground": "blue",
        "padding": (4, 2),
    }


def test_tk_and_ttk_receive_the_same_style_differently():
    accent = style.define("accent", fg="green", padx=8)

    mount = runtime.create_root(
        lambda: tk.VStack(
            tk.Label(text="Classic", style=accent),
            ttk.Label(text="Themed", style=accent),
        ),
        title="Demo",
    )
    classic, themed = mount.widget.children[0].children

    assert classic.props["fg"] == "green"
    assert classic.props["padx"] == 8
    assert themed.props["style"] == "Accent.TLabel"
    assert FakeStyle.configured["Accent.TLabel"] == {
        "foreground": "green",
        "padding": 8,
    }
