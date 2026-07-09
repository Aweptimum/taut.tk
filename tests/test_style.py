from __future__ import annotations

import json
import os
from pathlib import Path
from textwrap import dedent

import pyright

from solid_tk import layout
from solid_tk import reactive
from solid_tk import runtime
from solid_tk import style
from solid_tk import tk


def test_define_can_name_styles():
    title = style.define("title", font=("TkDefaultFont", 13, "bold"))
    panel = style.define("panel", padding=12, gap=8)

    assert title.props() == {"font": ("TkDefaultFont", 13, "bold")}
    assert title.name == "Title"
    assert panel.props() == {"padding": 12, "gap": 8}
    assert panel.name == "Panel"


def test_typed_style_helpers_create_styles():
    base = style.define(text="Title", fg="blue", padding=8, gap=6)
    title = style.label(text="Title", fg="blue")
    page = style.stack(padding=8, gap=6)

    assert base.props() == {"text": "Title", "fg": "blue", "padding": 8, "gap": 6}
    assert title.props() == {"text": "Title", "fg": "blue"}
    assert page.props() == {"padding": 8, "gap": 6}


def test_merge_applies_styles_in_order_and_ignores_falsey_values():
    base = style.define("base", fg="black", padx=4)
    muted = style.define("muted", fg="gray")

    props = style.merge(
        base,
        False,
        None,
        muted,
        {"pady": 2},
        fg="red",
    )

    assert props == {"fg": "red", "padx": 4, "pady": 2}
    assert props.name == "Muted"


def test_merged_styles_can_be_applied_to_tk():
    page_style = style.define("page", padding=8, gap=6)
    title_style = style.define("title", fg="blue", font=("TkDefaultFont", 13, "bold"))

    mount = runtime.create_root(
        lambda: layout.VStack(
            tk.Label(text="Styled", **style.merge(title_style)),
            **style.merge(page_style),
        ),
        title="Demo",
    )
    page = mount.widget.children[0]
    label = page.children[0]

    assert page.props["padx"] == 8
    assert page.props["pady"] == 8
    assert label.props["fg"] == "blue"
    assert label.props["font"] == ("TkDefaultFont", 13, "bold")


def test_component_applies_styles_defaults_and_call_overrides():
    base = style.define(fg="black", padx=4)
    accent = style.define(fg="blue", pady=2)
    StyledLabel = style.component(tk.Label, base, accent, text="Styled")

    mount = runtime.create_root(
        lambda: StyledLabel(fg="red"),
        title="Demo",
    )
    label = mount.widget.children[0]

    assert label.props["text"] == "Styled"
    assert label.props["fg"] == "red"
    assert label.props["padx"] == 4
    assert label.props["pady"] == 2


def test_component_preserves_children():
    StyledStack = style.component(layout.VStack, style.define(gap=6, padding=8))

    mount = runtime.create_root(
        lambda: StyledStack(
            tk.Label(text="One"),
            tk.Label(text="Two"),
        ),
        title="Demo",
    )
    stack = mount.widget.children[0]
    first, second = stack.children

    assert stack.props["padx"] == 8
    assert stack.props["pady"] == 8
    assert first.pack_kwargs["pady"] == (0, 6)
    assert second.props["text"] == "Two"


def test_style_values_can_be_reactive():
    color, set_color = reactive.create_signal("blue")
    accent = style.define("accent", fg=color)

    mount = runtime.create_root(
        lambda: tk.Label(text="Accent", **style.merge(accent)),
        title="Demo",
    )
    label = mount.widget.children[0]

    assert label.props["fg"] == "blue"

    set_color("green")

    assert label.props["fg"] == "green"


def test_style_rejects_parent_layout_props_for_tk_widgets():
    floating = style.define("floating", pack={"fill": "x"})

    try:
        tk.Label(text="Bad", style=floating)
    except ValueError as exc:
        assert str(exc) == "style cannot define parent layout props: pack"
    else:
        raise AssertionError("expected style layout props to be rejected")


def test_style_rejects_parent_layout_props_for_ttk_widgets():
    floating = style.define("floating", grid={"row": 0})

    try:
        from solid_tk import ttk

        ttk.Label(text="Bad", style=floating)
    except ValueError as exc:
        assert str(exc) == "style cannot define parent layout props: grid"
    else:
        raise AssertionError("expected style layout props to be rejected")


def test_typed_style_helpers_reject_invalid_props(tmp_path: Path):
    sample = tmp_path / "typed_styles.py"
    sample.write_text(
        dedent(
            """
            from solid_tk import style

            title = style.label(text="Title", fg="blue")
            bad = style.label(not_a_label_prop=True)
            """
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}

    result = pyright.run(
        "--outputjson",
        str(sample),
        check=False,
        cwd=Path.cwd(),
        env=env,
        text=True,
        capture_output=True,
    )

    stdout = result.stdout if isinstance(result.stdout, str) else result.stdout.decode()
    stderr = result.stderr if isinstance(result.stderr, str) else result.stderr.decode()
    assert result.returncode == 1, stdout + stderr
    output = json.loads(stdout)
    messages = [diagnostic["message"] for diagnostic in output["generalDiagnostics"]]

    assert any('No parameter named "not_a_label_prop"' in msg for msg in messages)


def test_define_keeps_mixed_style_dicts_typed(tmp_path: Path):
    sample = tmp_path / "mixed_styles.py"
    sample.write_text(
        dedent(
            """
            from solid_tk import style

            styles = {
                "title": style.define(text="Title"),
                "page": style.define(gap=8),
            }

            reveal_type(styles["title"])
            bad = style.define(not_a_style_prop=True)
            """
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}

    result = pyright.run(
        "--outputjson",
        str(sample),
        check=False,
        cwd=Path.cwd(),
        env=env,
        text=True,
        capture_output=True,
    )

    stdout = result.stdout if isinstance(result.stdout, str) else result.stdout.decode()
    stderr = result.stderr if isinstance(result.stderr, str) else result.stderr.decode()
    assert result.returncode == 1, stdout + stderr
    output = json.loads(stdout)
    messages = [diagnostic["message"] for diagnostic in output["generalDiagnostics"]]

    assert any("Style[StyleProps]" in msg for msg in messages)
    assert any('No overloads for "define" match the provided arguments' in msg for msg in messages)


def test_named_module_styles_keep_static_attributes_visible(tmp_path: Path):
    styles_module = tmp_path / "styles.py"
    styles_module.write_text(
        dedent(
            """
            from solid_tk import style

            page = style.define("page", gap=8)
            title = style.define("title", text="Title")
            """
        ),
        encoding="utf-8",
    )
    sample = tmp_path / "component.py"
    sample.write_text(
        dedent(
            """
            import styles

            reveal_type(styles.page)
            missing = styles.missing
            """
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": f"{Path.cwd() / 'src'}:{tmp_path}"}

    result = pyright.run(
        "--outputjson",
        str(sample),
        check=False,
        cwd=Path.cwd(),
        env=env,
        text=True,
        capture_output=True,
    )

    stdout = result.stdout if isinstance(result.stdout, str) else result.stdout.decode()
    stderr = result.stderr if isinstance(result.stderr, str) else result.stderr.decode()
    assert result.returncode == 1, stdout + stderr
    output = json.loads(stdout)
    messages = [diagnostic["message"] for diagnostic in output["generalDiagnostics"]]

    assert any("Style[StyleProps]" in msg for msg in messages)
    assert any('"missing" is not a known attribute of module "styles"' in msg for msg in messages)
