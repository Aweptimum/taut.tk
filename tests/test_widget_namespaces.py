from __future__ import annotations

from fakes import FakeStyle

from taut import layout
from taut import reactive
from taut import runtime
from taut import style
from taut import tk
from taut import ttk


def test_tk_namespace_exposes_classic_widgets():
    assert set(tk.__all__) == {
        "Button",
        "Canvas",
        "Checkbutton",
        "Entry",
        "Frame",
        "Fragment",
        "Label",
        "LabelFrame",
        "Listbox",
        "Menu",
        "Menubutton",
        "Message",
        "OptionMenu",
        "PanedWindow",
        "PhotoImage",
        "Portal",
        "Radiobutton",
        "Scale",
        "Scrollbar",
        "Spinbox",
        "Text",
        "Tk",
    }

    option_var = object()
    mount = runtime.create_root(
        lambda: layout.VStack(
            tk.Button(text="OK"),
            tk.Canvas(width=320, height=180, bg="black"),
            tk.Checkbutton(text="Check"),
            tk.Entry(value="entry"),
            tk.Frame(),
            tk.Label(text="Classic"),
            tk.LabelFrame(text="Group"),
            tk.Listbox(height=4),
            tk.Menu(tearoff=False),
            tk.Menubutton(text="Menu"),
            tk.Message(text="Message"),
            tk.OptionMenu(variable=option_var, value="one", values=("two", "three")),
            tk.PanedWindow(orient="horizontal"),
            tk.Radiobutton(text="Radio", value="a"),
            tk.Scale(from_=0, to=100, value=25),
            tk.Scrollbar(orient="vertical"),
            tk.Spinbox(from_=0, to=10),
            tk.Text(width=40, height=8),
        ),
        title="Demo",
    )
    stack = mount.widget.children[0]
    (
        button,
        canvas,
        checkbutton,
        entry,
        frame,
        label,
        label_frame,
        listbox,
        menu,
        menubutton,
        message,
        option_menu,
        paned_window,
        radiobutton,
        scale,
        scrollbar,
        spinbox,
        text,
    ) = stack.children

    assert button.props["text"] == "OK"
    assert canvas.props["width"] == 320
    assert canvas.props["height"] == 180
    assert canvas.props["bg"] == "black"
    assert checkbutton.props["text"] == "Check"
    assert entry.props["textvariable"].get() == "entry"
    assert frame.props == {}
    assert label.props["text"] == "Classic"
    assert label_frame.props["text"] == "Group"
    assert listbox.props["height"] == 4
    assert menu.props["tearoff"] is False
    assert menubutton.props["text"] == "Menu"
    assert message.props["text"] == "Message"
    assert option_menu.args == (option_var, "one", "two", "three")
    assert paned_window.props["orient"] == "horizontal"
    assert radiobutton.props["value"] == "a"
    assert scale.props["from_"] == 0
    assert scale.props["to"] == 100
    assert scale.props["variable"].get() == 25
    assert scrollbar.props["orient"] == "vertical"
    assert spinbox.props["from_"] == 0
    assert text.props["width"] == 40


def test_ttk_namespace_creates_themed_widgets():
    assert set(ttk.__all__) == {
        "Button",
        "Checkbutton",
        "Combobox",
        "Entry",
        "Frame",
        "LabeledScale",
        "Label",
        "LabelFrame",
        "Labelframe",
        "Menubutton",
        "Notebook",
        "OptionMenu",
        "PanedWindow",
        "Panedwindow",
        "Progressbar",
        "Radiobutton",
        "Scale",
        "Scrollbar",
        "Separator",
        "Sizegrip",
        "Spinbox",
        "Treeview",
    }
    assert ttk.Labelframe is ttk.LabelFrame
    assert ttk.Panedwindow is ttk.PanedWindow

    option_var = object()
    mount = runtime.create_root(
        lambda: layout.VStack(
            ttk.Button(text="OK", style="Accent.TButton"),
            ttk.Checkbutton(text="Check"),
            ttk.Combobox(value="A", values=("A", "B")),
            ttk.Entry(value="entry"),
            ttk.Frame(),
            ttk.Label(text="Themed", style="Title.TLabel"),
            ttk.LabelFrame(text="Group"),
            ttk.LabeledScale(from_=0, to=10),
            ttk.Menubutton(text="Menu"),
            ttk.Notebook(),
            ttk.OptionMenu(variable=option_var, default="one", values=("two", "three")),
            ttk.PanedWindow(orient="horizontal"),
            ttk.Progressbar(value=50, maximum=100),
            ttk.Radiobutton(text="Radio", value="a"),
            ttk.Scale(from_=0, to=100, value=25),
            ttk.Scrollbar(orient="vertical"),
            ttk.Separator(orient="horizontal"),
            ttk.Sizegrip(),
            ttk.Spinbox(from_=0, to=10),
            ttk.Treeview(columns=("name",)),
        ),
        title="Demo",
    )
    (
        button,
        checkbutton,
        combobox,
        entry,
        frame,
        label,
        label_frame,
        labeled_scale,
        menubutton,
        notebook,
        option_menu,
        paned_window,
        progress,
        radiobutton,
        scale,
        scrollbar,
        separator,
        sizegrip,
        spinbox,
        treeview,
    ) = mount.widget.children[0].children

    assert button.props["style"] == "Accent.TButton"
    assert checkbutton.props["text"] == "Check"
    assert combobox.props["textvariable"].get() == "A"
    assert combobox.props["values"] == ("A", "B")
    assert entry.props["textvariable"].get() == "entry"
    assert frame.props == {}
    assert label.props["text"] == "Themed"
    assert label.props["style"] == "Title.TLabel"
    assert label_frame.props["text"] == "Group"
    assert labeled_scale.props["from_"] == 0
    assert menubutton.props["text"] == "Menu"
    assert notebook.props == {}
    assert option_menu.args == (option_var, "one", "two", "three")
    assert paned_window.props["orient"] == "horizontal"
    assert progress.props["value"] == 50
    assert progress.props["maximum"] == 100
    assert radiobutton.props["value"] == "a"
    assert scale.props["from_"] == 0
    assert scale.props["to"] == 100
    assert scale.props["variable"].get() == 25
    assert scrollbar.props["orient"] == "vertical"
    assert separator.props["orient"] == "horizontal"
    assert sizegrip.props == {}
    assert spinbox.props["from_"] == 0
    assert treeview.props["columns"] == ("name",)


def test_ttk_entry_value_tracks_signal_changes():
    value, set_value = reactive.create_signal("hello")

    mount = runtime.create_root(lambda: ttk.Entry(value=value), title="Demo")
    entry = mount.widget.children[0]
    variable = entry.props["textvariable"]

    assert variable.get() == "hello"

    set_value("world")

    assert variable.get() == "world"


def test_scale_value_tracks_signal_changes_and_user_input():
    value, set_value = reactive.create_signal(10.0)

    mount = runtime.create_root(
        lambda: tk.Scale(value=value, on_input=set_value),
        title="Demo",
    )
    scale = mount.widget.children[0]
    variable = scale.props["variable"]

    assert variable.get() == 10.0

    set_value(20.0)
    assert variable.get() == 20.0

    variable.set(30.0)
    assert value() == 30.0


def test_photo_image_delegates_to_tkinter():
    image = tk.PhotoImage(file="frame.png")

    assert image.props == {"file": "frame.png"}


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
        lambda: layout.VStack(
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
