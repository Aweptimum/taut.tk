# Reactive Primitives

`solid-tk` uses small Python wrappers around `reaktiv` signals. The public API
keeps reads and writes separate:

```python
count, set_count = create_signal(0)

count()
set_count(1)
set_count(lambda value: value + 1)
```

## Accessors And Mutators

An `Accessor[T]` is a callable read handle:

```python
label = Label(text=lambda: f"Count: {count()}")
```

A `Mutator[T]` writes a value or updates from the current value:

```python
set_count(3)
set_count(lambda current: current + 1)
```

Writable widgets receive accessors and mutators separately:

```python
text, set_text = create_signal("")
Entry(value=text, on_input=set_text)
```

## `create_signal`

Create a reactive value:

```python
name, set_name = create_signal("Ada")
```

Pass the accessor directly to widgets when the widget should track the value:

```python
Label(text=name)
```

Use a lambda for derived widget values:

```python
Label(text=lambda: f"Hello {name()}")
```

## `create_memo`

Create a cached derived value:

```python
first, set_first = create_signal("Ada")
last, set_last = create_signal("Lovelace")

full_name = create_memo(lambda: f"{first()} {last()}")
```

Memos are accessors:

```python
Label(text=full_name)
```

## `create_selector`

Create a predicate for checking whether a key matches a source value:

```python
selected_id, set_selected_id = create_signal(1)
is_selected = create_selector(selected_id)

Label(
    text="Ada",
    bg=lambda: "#dbeafe" if is_selected(1) else "#ffffff",
)
```

Custom equality is supported:

```python
selected_user, set_selected_user = create_signal({"id": 1})
is_selected = create_selector(
    selected_user,
    equals=lambda key, user: key == user["id"],
)
```

This currently provides the ergonomic API, not Solid's per-key subscription
optimization.

## `on`

Use `on(source, fn)` when an effect should track one explicit source but ignore
other reactive reads inside the callback:

```python
create_effect(
    on(
        selected_id,
        lambda selected: print("selected", selected, "while count is", count()),
    )
)
```

Changing `selected_id` reruns the effect. Changing `count` alone does not.

Use `defer=True` to skip the initial callback:

```python
create_effect(on(selected_id, lambda selected: load(selected), defer=True))
```

## `untrack`

Use `untrack(fn)` for one-off reads that should not subscribe the current
effect:

```python
create_effect(
    lambda: print(
        "tracked",
        selected_id(),
        "untracked",
        untrack(count),
    )
)
```

Changing `selected_id` reruns the effect. Changing `count` alone does not.

## `to_accessor` And `read`

`to_accessor(value)` normalizes values into accessors:

```python
to_accessor("Ada")
to_accessor(lambda: name())
to_accessor(name)
```

`read(value)` unwraps an accessor, signal, callable, or plain value:

```python
read(name)
read(lambda: f"Hello {name()}")
read("plain")
```

These helpers are mostly used by the framework, but they are useful when writing
small abstractions.
