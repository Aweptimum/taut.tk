# Resources

Resources are Solid-style async values for work that should not block Tk's UI
loop. A resource runs a fetcher on a worker thread, then publishes the result
back through the current owner's UI dispatcher.

```python
from solid_tk.resource import SourceInfo
from solid_tk.resource import create_resource


def fetch_user(user_id: int, info: SourceInfo[dict, str]) -> dict:
    return {"id": user_id, "name": "Ada"}


user, (mutate_user, refetch_user) = create_resource(fetch_user, None, user_id)
```

There are two signatures:

```python
resource, (mutate, refetch) = create_resource(fetcher, options=None)
resource, (mutate, refetch) = create_resource(fetcher, options=None, source)
```

The no-source form passes `True` as the fetcher source.

## Reading State

The resource itself is an accessor:

```python
resource()
```

It also exposes status accessors:

```python
resource.latest()
resource.loading()
resource.error()
resource.state()
```

`state()` is one of:

- `"unresolved"`: no enabled source and no value
- `"pending"`: first request is running
- `"refreshing"`: a request is running while an older value exists
- `"ready"`: a value is available
- `"errored"`: the latest request failed

## Fetcher Info

Fetchers receive a `SourceInfo` dictionary:

```python
def fetcher(source, info):
    previous = info["value"]
    refetching = info["refetching"]
```

`info["value"]` is the previous resolved or mutated value. It is read without
tracking so updating the resource value does not cause fetch loops.

`info["refetching"]` is:

- `False` for source-driven fetches
- `True` for a plain `refetch()`
- the custom value passed to `refetch(info)`

## Sources

The source can be a value or an accessor:

```python
resource, actions = create_resource(fetcher, None, user_id)
resource, actions = create_resource(fetcher, None, lambda: user_id())
```

When the source changes, the resource fetches again. `False` and `None` disable
fetching, same as solid:

```python
resource, actions = create_resource(fetcher, None, lambda: selected_id() or None)
```

Other falsy values, such as `0` or `""`, are valid sources.

## Stale Requests

If the source changes or `refetch()` is called while an older request is still
running, the newer request wins. The older worker thread is not killed; Python
does not provide safe general-purpose thread cancellation. Instead, solid-tk
assigns each request an id and ignores completions from stale requests.

That means fetchers should still be written to finish reasonably quickly or use
their own cooperative timeout/cancellation mechanism for long-running work.
Stale requests will not update `latest()`, `error()`, `loading()`, or `state()`
after a newer request has started.

## Actions

`mutate` updates the cached value without running the fetcher:

```python
mutate({"id": 1, "name": "Grace"})
mutate(lambda previous: {**previous, "name": "Grace"} if previous else previous)
```

`refetch` starts a new request:

```python
refetch()
refetch("retry button")
```

`refetch` returns immediately. The value arrives later through `resource()` and
`resource.latest()`.

## Options

Supported options:

```python
resource, actions = create_resource(
    fetcher,
    {
        "initial_value": cached_value,
        "name": "user",
        "storage": custom_storage,
    },
    source,
)
```

`initial_value` seeds `latest()` and starts the resource in `"ready"`.

`storage` can replace the signal used for the cached value. It receives the
initial value and must return `(accessor, mutator)`.

`name` is kept for diagnostics and debugging.

## Threading

Resource fetchers run on worker threads. They should not touch Tk widgets or
mutate signals directly. Use `to_ui()` for progress callbacks from inside a
fetcher, as shown in `examples/resource_demo`.

The public resource API routes completion back through the owner dispatcher.
For free-threaded Python builds, the safest backend strategy is still to keep
all Tk calls on the UI thread.
