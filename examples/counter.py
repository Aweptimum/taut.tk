from __future__ import annotations

from reaktiv import Signal

from solid_tk import Button
from solid_tk import Component
from solid_tk import For
from solid_tk import Label
from solid_tk import Show
from solid_tk import VStack
from solid_tk import create_root


class Counter(Component):
    def setup(self) -> None:
        self.count = Signal(0)
        self.todos = Signal(["wire props", "own effects", "dispose cleanly"])

    def render(self):
        return VStack(
            Label(text=lambda: f"{self.props.title()}: {self.count()}"),
            Button(
                text="Increment", on_click=lambda: self.count.update(lambda n: n + 1)
            ),
            Show(
                lambda: self.count() % 2 == 0,
                lambda: Label(text="Even"),
                fallback=lambda: Label(text="Odd"),
            ),
            For(self.todos, lambda item: Label(text=item), key=lambda item: item),
            padx=12,
            pady=12,
        )


def main() -> None:
    mount = create_root(lambda: Counter(title="Solid TK"), title="Solid TK")
    mount.widget.mainloop()


if __name__ == "__main__":
    main()
