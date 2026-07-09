# Context API

`solid-tk` context is built on the current owner scope. A `Provider` creates a
child owner with a context value, and `use_context()` walks parent owners until
it finds the nearest matching value.

## `create_context()`

Create a unique context key.

```python
theme_context = create_context("light")
```

Passing a normal value creates a context with that default. If no provider is
found, `use_context(theme_context)` returns `"light"`.

```python
settings_context = create_context(Settings)
```

Passing a type creates a required-provider context. If no provider is found,
`use_context(settings_context)` returns `None`, so a domain hook can raise a
clear error.

## `Provider()`

Provide a value for a child subtree.

```python
Provider(theme_context, "dark", lambda: App())
```

The child should usually be callable. Python evaluates function arguments before
the function call, so `Provider(theme_context, "dark", App())` creates `App`
before the provider owner exists.

Forwarded component children work too:

```python
@component
def ThemeProvider(props):
    return Provider(theme_context, "dark", props.children)
```

## `use_context()`

Read the nearest provider value, or the context default.

```python
@component
def ThemedLabel(props):
    theme = use_context(theme_context)
    return Label(text=theme)
```

For required contexts, wrap `use_context()` in a domain-specific helper:

```python
settings_context = create_context(Settings)


def use_settings() -> Settings:
    settings = use_context(settings_context)
    if settings is None:
        raise RuntimeError("use_settings must be used within SettingsProvider")
    return settings
```

See [context_typed](../examples/context_typed/) for more in that vein