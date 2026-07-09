# solid-tk examples

Run examples from the repository root with `python -m examples.<name>`.

## What To Try Next

- `python -m examples.counter`: signals, components, control flow, and typed props.
- `python -m examples.control_demo`: `Show`, `Switch`, `For`, `Index`, and `Dynamic`.
- `python -m examples.layout_demo`: stacks, spacing, padding, child layout overrides, and styles.
- `python -m examples.context_typed`: typed context plus first-class component children.
- `python -m examples.store_demo`: immutable store updates, lenses, and reconciliation.
- `python -m examples.scheduler_demo`: `after`, `interval`, `defer`, and thread-to-UI dispatch.
- `python -m examples.resource_demo`: worker-thread resources with loading and retry states.
- `python -m examples.error_boundary_demo`: render/update error recovery.
- `python -m examples.portal_demo`: mounting a subtree into a `tk.Toplevel`.

If you are new to the project, try `counter`, then `control_demo`, then
`layout_demo`. After that, pick `context_typed` if you are building app-wide
state, or `resource_demo` if you need background work.
