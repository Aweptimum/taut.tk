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
        self.column_weights = {}
        self.row_weights = {}
        if parent is not None:
            parent.children.append(self)

    def configure(self, **props):
        self.props.update(props)

    def pack(self, **kwargs):
        self.pack_kwargs = kwargs

    def grid(self, **kwargs):
        self.grid_kwargs = kwargs

    def place(self, **kwargs):
        self.place_kwargs = kwargs

    def columnconfigure(self, index, **kwargs):
        self.column_weights[index] = kwargs

    def rowconfigure(self, index, **kwargs):
        self.row_weights[index] = kwargs

    def pack_forget(self):
        pass

    def destroy(self):
        self.destroy_count += 1
        self.destroyed = True

    def title(self, value):
        self.props["title"] = value

    def quit(self):
        self.quit_called = True

    def protocol(self, name, callback):
        self.protocols[name] = callback

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
