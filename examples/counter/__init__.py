"""Example applications."""

from examples.counter.component import Counter as Counter
from examples.counter.component import counter as counter
from solid_tk import create_root
from solid_tk import create_signal


def main() -> None:
    count, set_count = create_signal(0)
    mount = create_root(
        lambda: counter(label="Solid TK", count=count, set_count=set_count),
        title="Solid TK",
    )
    mount.widget.mainloop()


if __name__ == "__main__":
    main()
