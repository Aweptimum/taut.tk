from __future__ import annotations

from solid_tk import component
from solid_tk import context
from solid_tk import runtime
from solid_tk import widgets


def test_context_reads_default_value():
    theme = context.create_context("light")

    @component
    def ThemedLabel(props):
        return widgets.Label(text=context.use_context(theme))

    mount = runtime.create_root(lambda: ThemedLabel(), title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "light"


def test_context_preserves_explicit_none_default():
    maybe_value = context.create_context(None)

    @component
    def MaybeLabel(props):
        return widgets.Label(text=lambda: "missing" if context.use_context(maybe_value) is None else "set")

    mount = runtime.create_root(lambda: MaybeLabel(), title="Demo")
    label = mount.widget.children[0]

    assert label.props["text"] == "missing"
    assert maybe_value.has_default


def test_provider_supplies_context_to_callable_child():
    theme = context.create_context("light")

    @component
    def ThemedLabel(props):
        return widgets.Label(text=context.use_context(theme))

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
        return widgets.Label(text=context.use_context(theme))

    mount = runtime.create_root(
        lambda: ThemeProvider(children=lambda: ThemedLabel()),
        title="Demo",
    )
    label = mount.widget.children[0]

    assert label.props["text"] == "dark"


def test_nested_provider_uses_nearest_context_value():
    theme = context.create_context("light")

    @component
    def ThemedLabel(props):
        return widgets.Label(text=context.use_context(theme))

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
