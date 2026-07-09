"""Context example application."""

from examples.context_demo.component import context_demo
from solid_tk.runtime import create_root


def main() -> None:
    mount = create_root(context_demo, title="Solid TK Context")
    mount.widget.mainloop()


if __name__ == "__main__":
    main()
