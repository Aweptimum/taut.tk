from __future__ import annotations

from typing import Optional


class FakeStringVar:
    def __init__(self, master=None):
        self.master = master
        self.value = ""
        self.traces = {}
        self.next_id = 0

    def get(self):
        return self.value

    def set(self, value):
        self.value = value
        for callback in list(self.traces.values()):
            callback("name", "index", "write")

    def trace_add(self, mode, callback):
        self.next_id += 1
        trace_id = f"trace-{self.next_id}"
        self.traces[trace_id] = callback
        return trace_id

    def trace_remove(self, mode, trace_id):
        self.traces.pop(trace_id, None)


class FakeDoubleVar(FakeStringVar):
    def __init__(self, master=None):
        super().__init__(master)
        self.value = 0.0


class FakePhotoImage:
    def __init__(self, **props):
        self.props = dict(props)


class FakeWidget:
    def __init__(self, parent: Optional[FakeWidget] = None, *args, **props):
        self.parent = parent
        self.args = args
        self.props = dict(props)
        self.children = []
        self.destroyed = False
        self.destroy_count = 0
        self.after_callbacks = {}
        self.after_cancelled = []
        self.next_after_id = 0
        self.protocols = {}
        self.bindings = {}
        self.unbound = []
        self.next_bind_id = 0
        self.column_weights = {}
        self.row_weights = {}
        self.packed_children = []
        if parent is not None:
            parent.children.append(self)

    def configure(self, **props):
        self.props.update(props)

    def pack(self, **kwargs):
        self.pack_kwargs = kwargs
        if self.parent is not None:
            if self in self.parent.packed_children:
                self.parent.packed_children.remove(self)
            self.parent.packed_children.append(self)

    def grid(self, **kwargs):
        self.grid_kwargs = kwargs

    def place(self, **kwargs):
        self.place_kwargs = kwargs

    def columnconfigure(self, index, **kwargs):
        self.column_weights[index] = kwargs

    def rowconfigure(self, index, **kwargs):
        self.row_weights[index] = kwargs

    def pack_forget(self):
        if self.parent is not None and self in self.parent.packed_children:
            self.parent.packed_children.remove(self)

    def destroy(self):
        self.destroy_count += 1
        self.destroyed = True
        self.pack_forget()

    def title(self, value):
        self.props["title"] = value

    def quit(self):
        self.quit_called = True

    def protocol(self, name, callback):
        self.protocols[name] = callback

    def bind(self, sequence, callback):
        self.next_bind_id += 1
        bind_id = f"bind-{self.next_bind_id}"
        self.bindings[(sequence, bind_id)] = callback
        return bind_id

    def unbind(self, sequence, bind_id=None):
        self.unbound.append((sequence, bind_id))
        if bind_id is not None:
            self.bindings.pop((sequence, bind_id), None)

    def run_binding(self, sequence, bind_id=None, event=None):
        if bind_id is None:
            bind_id = next(
                key_bind_id
                for key_sequence, key_bind_id in self.bindings
                if key_sequence == sequence
            )
        return self.bindings[(sequence, bind_id)](event)

    def after(self, ms, callback):
        self.next_after_id += 1
        after_id = f"after-{self.next_after_id}"
        self.after_callbacks[after_id] = (ms, callback)
        return after_id

    def after_cancel(self, after_id):
        self.after_cancelled.append(after_id)
        self.after_callbacks.pop(after_id, None)

    def run_after(self, after_id):
        _ms, callback = self.after_callbacks.pop(after_id)
        callback()

    def run_next_after(self):
        after_id = next(iter(self.after_callbacks))
        self.run_after(after_id)
        return after_id


class FakeTk(FakeWidget):
    def __init__(self, **props):
        super().__init__(None, **props)


class FakeStyle:
    configured = {}

    def configure(self, name, **props):
        self.configured[name] = props
