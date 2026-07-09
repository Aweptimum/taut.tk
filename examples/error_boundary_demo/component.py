from __future__ import annotations

from solid_tk import component
from solid_tk.control import ErrorBoundary
from solid_tk.control import Show
from solid_tk.reactive import create_signal
from solid_tk.widgets import Button
from solid_tk.widgets import HStack
from solid_tk.widgets import Label
from solid_tk.widgets import VStack


@component
def risky_panel(props):
    if props.phase() == "render":
        raise RuntimeError("the panel crashed while rendering")

    def status_text() -> str:
        if props.phase() == "reactive":
            raise RuntimeError("the panel crashed during a reactive update")
        return "The risky panel is healthy."

    return VStack(
        Label(text="Risky panel"),
        Label(text=status_text),
        padx=8,
        pady=8,
        relief="groove",
        bd=1,
    )


@component
def error_boundary_demo(props):
    phase, set_phase = create_signal("ok")
    visible, set_visible = create_signal(True)

    def recover(reset) -> None:
        set_phase("ok")
        set_visible(True)
        reset()

    def crash_on_render() -> None:
        set_visible(False)
        set_phase("render")
        set_visible(True)

    return VStack(
        Label(text="ErrorBoundary demo"),
        HStack(
            Button(text="Healthy", on_click=lambda: set_phase("ok")),
            Button(text="Crash update", on_click=lambda: set_phase("reactive")),
            Button(text="Crash render", on_click=crash_on_render),
        ),
        ErrorBoundary(
            lambda: Show(visible, lambda: risky_panel(phase=phase)),
            fallback=lambda error, reset: VStack(
                Label(text=lambda: f"Caught: {error}"),
                Button(text="Reset boundary", on_click=lambda: recover(reset)),
                padx=8,
                pady=8,
                relief="ridge",
                bd=1,
            ),
        ),
        padx=12,
        pady=12,
    )
