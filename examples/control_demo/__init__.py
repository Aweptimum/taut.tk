"""Control-flow example application."""

from examples.control_demo.component import control_demo
from taut.runtime import create_root


def main() -> None:
    mount = create_root(control_demo, title="Solid TK Control Flow")
    mount.widget.mainloop()


if __name__ == "__main__":
    main()
