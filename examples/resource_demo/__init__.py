"""Resource example application."""

from examples.resource_demo.component import resource_demo
from solid_tk.runtime import create_root


def main() -> None:
    mount = create_root(resource_demo, title="Solid TK Resource")
    mount.widget.mainloop()


if __name__ == "__main__":
    main()
