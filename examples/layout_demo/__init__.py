"""Layout example application."""

from examples.layout_demo.component import layout_demo
from taut.runtime import create_root


def main() -> None:
    mount = create_root(layout_demo, title="Solid TK Layout")
    mount.widget.minsize(520, 360)
    mount.widget.mainloop()


if __name__ == "__main__":
    main()
