"""Required-context example application."""

from examples.context_typed.component import dark_context_demo
from solid_tk import create_root


def main() -> None:
    mount = create_root(dark_context_demo, title="Solid TK Dark Context")
    mount.widget.mainloop()


if __name__ == "__main__":
    main()
