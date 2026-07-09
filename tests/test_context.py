from __future__ import annotations

from solid_tk import Fragment
from solid_tk import component
from solid_tk import context
from solid_tk import layout
from solid_tk import runtime
from solid_tk import tk


def test_context_reads_default_value():
    theme = context.create_context("light")

    @component
    def ThemedLabel(props):
        return tk.Label(text=context.use_context(theme))

    mount = runtime.create_root(lambda: ThemedLabel(), title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "light"


def test_context_preserves_explicit_none_default():
    maybe_value = context.create_context(None)

    @component
    def MaybeLabel(props):
        return tk.Label(text=lambda: "missing" if context.use_context(maybe_value) is None else "set")

    mount = runtime.create_root(lambda: MaybeLabel(), title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "missing"
    assert maybe_value.has_default


def test_provider_supplies_context_to_callable_child():
    theme = context.create_context("light")

    @component
    def ThemedLabel(props):
        return tk.Label(text=context.use_context(theme))

    mount = runtime.create_root(
        lambda: context.Provider(theme, "dark", lambda: ThemedLabel()),
        title="Demo",
    )
    label = mount.widget.children[0]

    assert label.props["text"] == "dark"


def test_provider_accepts_forwarded_component_children():
    theme = context.create_context("light")

    @component
    def ThemeProvider(props):
        return context.Provider(theme, "dark", props.children)

    @component
    def ThemedLabel(props):
        return tk.Label(text=context.use_context(theme))

    mount = runtime.create_root(
        lambda: ThemeProvider(children=lambda: ThemedLabel()),
        title="Demo",
    )
    label = mount.widget.children[0]

    assert label.props["text"] == "dark"


def test_provider_accepts_forwarded_positional_component_children():
    theme = context.create_context("light")

    @component
    def ThemeProvider(props):
        return context.Provider(theme, "dark", props.children)

    @component
    def ThemedLabel(props):
        return tk.Label(text=context.use_context(theme))

    mount = runtime.create_root(
        lambda: ThemeProvider(lambda: ThemedLabel()),
        title="Demo",
    )
    label = mount.widget.children[0]

    assert label.props["text"] == "dark"


def test_provider_fragment_children_are_laid_out_by_parent():
    theme = context.create_context("light")

    @component
    def ThemedLabel(props):
        return tk.Label(text=context.use_context(theme))

    mount = runtime.create_root(
        lambda: layout.VStack(
            tk.Label(text="Before"),
            context.Provider(
                theme,
                "dark",
                lambda: Fragment(
                    ThemedLabel(),
                    tk.Label(text="After provider"),
                ),
            ),
            tk.Label(text="After"),
        ),
        title="Demo",
    )
    stack = mount.widget.children[0]

    assert [child.props["text"] for child in stack.children] == [
        "Before",
        "dark",
        "After provider",
        "After",
    ]


def test_nested_provider_uses_nearest_context_value():
    theme = context.create_context("light")

    @component
    def ThemedLabel(props):
        return tk.Label(text=context.use_context(theme))

    mount = runtime.create_root(
        lambda: context.Provider(
            theme,
            "outer",
            lambda: context.Provider(theme, "inner", lambda: ThemedLabel()),
        ),
        title="Demo",
    )
    label = mount.widget.children[0]

    assert label.props["text"] == "inner"
