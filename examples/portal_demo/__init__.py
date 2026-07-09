"""Portal example application."""

from examples.portal_demo.component import portal_demo
from taut.runtime import create_root


def main() -> None:
    mount = create_root(portal_demo, title="Solid TK Portal")
    mount.widget.mainloop()


if __name__ == "__main__":
    main()
