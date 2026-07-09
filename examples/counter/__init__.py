"""Example applications."""

from reaktiv import Signal

from examples.counter.component import Counter as Counter
from examples.counter.component import counter as counter
from solid_tk import create_root


def main() -> None:
    mount = create_root(
        lambda: counter(label="Solid TK", initial=Signal(0)),
        title="Solid TK",
    )
    mount.widget.mainloop()


if __name__ == "__main__":
    main()
