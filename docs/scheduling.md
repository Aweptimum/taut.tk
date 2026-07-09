# Scheduling

Scheduling helpers run callbacks on Tk's event loop and keep those callbacks
owned by the component or root that created them. Callbacks are cancelled
automatically when their owner is disposed.

## API

Import scheduling helpers from `taut.runtime`:

```python
from taut.runtime import after
from taut.runtime import defer
from taut.runtime import interval
from taut.runtime import to_ui
```

These helpers must be called inside a taut.tk owner, such as during component
rendering, an effect, `on_mount`, or another owned callback.

## `after`

`after(ms, fn)` schedules `fn` once after `ms` milliseconds:

```python
after(500, lambda: set_status("half a second later"))
```

It returns a cancel handle:

```python
handle = after(1000, save)
handle.cancel()
```

The handle is also cancelled automatically when the current owner is disposed.

## `defer`

`defer(fn)` schedules `fn` for the next event-loop turn:

```python
defer(lambda: print("mounted, then deferred"))
```

It is equivalent to `after(0, fn)`.

## `interval`

`interval(ms, fn)` runs `fn` repeatedly:

```python
interval(1000, lambda: set_count(lambda value: value + 1))
```

The next tick is scheduled only after the callback returns, so callbacks do not
pile up concurrently. Return `False` to stop:

```python
interval(1000, lambda: False if done() else tick())
```

Keep interval callbacks small. Tk runs UI work on one event loop, so slow
callbacks still block the interface.

## `to_ui`

`to_ui()` captures an owner-bound dispatcher that can be passed to worker code.
The dispatcher runs callbacks back on Tk's UI thread and restores the original
owner context.

```python
dispatch = to_ui()

def worker():
    result = load_data()
    dispatch(lambda: set_result(result))
```

After the owner is disposed, dispatching becomes a no-op and pending callbacks
are cancelled where possible.

## Owner Context

Scheduled callbacks run with the owner that created them. That means lifecycle
helpers and context lookups still work inside callbacks:

```python
@component
def Clock(props):
    now, set_now = create_signal("...")
    interval(1000, lambda: set_now(time.strftime("%H:%M:%S")))
    return tk.Label(text=now)
```

When `Clock` is unmounted, the interval is cancelled.

## Error Behavior

Scheduled callbacks run later, outside render/update flow. `ErrorBoundary`
catches render and reactive update errors in its child subtree, but deferred
callback errors are not treated as render errors.

## Example

See `examples/scheduler_demo` for moving labels, `after`, `interval`, `defer`,
and a worker-thread callback:

```sh
python -m examples.scheduler_demo
```
