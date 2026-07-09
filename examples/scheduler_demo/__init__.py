"""Scheduler example application."""

from examples.scheduler_demo.component import scheduler_demo
from solid_tk.runtime import create_root


def main() -> None:
    mount = create_root(scheduler_demo, title="Solid TK Scheduler")
    mount.widget.mainloop()


if __name__ == "__main__":
    main()
