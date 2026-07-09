import argparse
from pathlib import Path

from taut.cli.stubs import main_cli as stubby
from taut.cli.watch import main as watcher


def main():
    parser = argparse.ArgumentParser(description="taut.tk development tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_stubs = subparsers.add_parser("stubs", help="Generate taut.tk .pyi stubs.")
    parser_stubs.add_argument("paths", nargs="+", type=Path)
    parser_stubs.add_argument(
        "-o",
        "--out-dir",
        default="typings",
        type=Path,
        help="Directory for generated stubs. Defaults to typings.",
    )
    parser_stubs.add_argument(
        "--in-place",
        action="store_true",
        help="Write sibling .pyi files next to source files.",
    )
    parser_stubs.set_defaults(func=stubby)

    parser_watch = subparsers.add_parser("watch", help="Regenerate .pyi stubs on edits.")
    parser_watch.set_defaults(func=watcher)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
