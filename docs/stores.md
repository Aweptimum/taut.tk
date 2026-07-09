# Stores

Stores are helpers for structured state. Use `create_store()` when you want
immutable updates and path lenses. Use `create_mutable()` when you want
Solid-style mutable objects whose reads are reactive.

## API

Import store helpers from `solid_tk.stores`:

```python
from solid_tk.stores import create_mutable
from solid_tk.stores import create_store
from solid_tk.stores import produce
from solid_tk.stores import reconcile
from solid_tk.stores import unwrap
```

## `create_store`

`create_store(initial)` returns an accessor plus a setter:

```python
state, set_state = create_store({"count": 0, "user": {"name": "Ada"}})

state()
set_state({"count": 1, "user": {"name": "Ada"}})
set_state(lambda current: {**current, "count": current["count"] + 1})
```

The setter works like a signal mutator. It accepts a replacement value or an
updater function.

## Store Lenses

Use `set_state.at(...)` to focus a nested path:

```python
name = set_state.at("user", "name")

tk.Label(text=name)
name.set("Grace")
name.update(lambda value: value.upper())
```

A lens is also an accessor, so it can be passed to widgets or read directly:

```python
name()
tk.Entry(value=name, on_input=name.set)
```

Paths use string keys for mappings/attributes and integer keys for lists or
tuples.

## `produce`

`produce(recipe)` creates an immutable updater from mutable-looking code. The
recipe receives a deep copy of the current value.

```python
set_state(
    produce(lambda draft: draft["todos"].append({"id": 2, "title": "Ship docs"}))
)
```

Return `None` to use the mutated draft. Return another value to replace the
draft result.

## `reconcile`

`reconcile(value)` creates an updater that recursively reuses unchanged nested
values where possible.

```python
set_state(reconcile(next_state))
```

This is useful when replacing a large structure from external data while
preserving object identity for unchanged branches.

## `create_mutable`

`create_mutable(initial)` returns the mutable object itself. Reads track a
private version signal; writes mutate in place and notify dependents.

```python
items = create_mutable(["a"])

create_effect(lambda: print(tuple(items)))

items.append("b")
items[0] = "A"
items.replace(["x", "y"])
```

Mappings and simple attribute objects are wrapped too:

```python
state = create_mutable({"user": {"name": "Ada"}, "todos": []})

create_effect(lambda: print(state["user"]["name"], len(state["todos"])))

state["user"]["name"] = "Grace"
state["todos"].append("write docs")
```

Simple objects with `__dict__` are proxied through attributes:

```python
user = create_mutable(User("Ada"))
user.name = "Grace"
```

This is an attribute-state proxy, not a full class-behavior proxy. Methods on
the original object are not rebound to make internal mutations reactive. If a
method mutates `self.name`, that write bypasses the proxy.
Prefer dictionaries/lists, direct proxy attribute writes, or
immutable store updates for richer domain objects with behavior.

Dataclass instances are not proxied as mutable objects; immutable store updates
fit them better.

## Mutable Collections

Mutable lists support normal `MutableSequence` operations such as indexing,
iteration, `append`, `extend`, deletion, and slice assignment. They also expose:

```python
items.replace(["next"])
items.snapshot()
```

Mutable dictionaries support normal `MutableMapping` operations and:

```python
state.replace({"ready": True})
state.snapshot()
```

## `unwrap`

`unwrap(value)` reads through accessors, lenses, mutable proxies, mappings,
lists, tuples, and dataclasses to produce plain values.

```python
plain = unwrap(state)
```

Use it when serializing, debugging, or passing store data to code that should
not receive reactive proxies.

## Choosing A Store

Use `create_signal()` for scalar values and small independent pieces of state.

Use `create_store()` when you want immutable updates, typed lenses, or undoable
state transitions.

Use `create_mutable()` when in-place list/dict/object operations read better and
the state is local enough that mutation will not surprise callers.

## Example

See `examples/store_demo` for immutable stores, lenses, mutable state, and
reconciliation:

```sh
python -m examples.store_demo
```
