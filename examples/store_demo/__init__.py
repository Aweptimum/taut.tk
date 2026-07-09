"""Store example application."""

from examples.store_demo.component import store_demo
from solid_tk import create_root


def main() -> None:
    mount = create_root(store_demo, title="Solid TK Stores")
    mount.widget.mainloop()


if __name__ == "__main__":
    main()
