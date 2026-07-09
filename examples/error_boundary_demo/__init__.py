"""Error boundary example application."""

from examples.error_boundary_demo.component import error_boundary_demo
from taut.runtime import create_root


def main() -> None:
    mount = create_root(error_boundary_demo, title="Solid TK Error Boundary")
    mount.widget.mainloop()


if __name__ == "__main__":
    main()
