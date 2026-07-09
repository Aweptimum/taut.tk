# tools/watch_stubs.py
import ast
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .stubs import DEFAULT_OUT_DIR
from .stubs import contains_component_def
from .stubs import main as stub_gen
from .stubs import remove_stub_for_source
from .stubs import remove_stubs_for_source_dir

SRC_ROOT = Path.cwd()

def _ensure_str(string: bytes | str) -> str:
    if not isinstance(string, str):
        string = str(string)
    return string

class StubWatchHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        self.debounce_seconds = 0.25
        self._last_seen: dict[Path, float] = {}

    def on_modified(self, event):
        if event.is_directory:
            return

        path = event_path(event)
        if is_package_init_path(path) and is_stub_relevant_source(path):
            self._regenerate_all()
            return

        self._maybe_generate(event)

    def on_created(self, event):
        if event.is_directory:
            regenerate_all_stubs()
            return

        if is_stub_relevant_source(Path(_ensure_str(event.src_path))):
            regenerate_all_stubs()

    def on_moved(self, event):
        if event.is_directory:
            remove_generated_stub_tree(Path(_ensure_str(event.src_path)))
            regenerate_all_stubs()
            return

        if event_involves_stub_relevant_source(event):
            removed = remove_generated_stub(Path(_ensure_str(event.src_path)))
            if removed or is_stub_relevant_source(event_path(event)):
                regenerate_all_stubs()

    def on_deleted(self, event):
        if event.is_directory:
            if remove_generated_stub_tree(Path(_ensure_str(event.src_path))):
                regenerate_all_stubs()
            return

        if remove_generated_stub(Path(_ensure_str(event.src_path))):
            regenerate_all_stubs()

    def _maybe_generate(self, event):
        if event.is_directory:
            return

        path = event_path(event)

        if not is_stub_source_path(path):
            return

        if not contains_component_def(path):
            return

        self._generate_path(path)

    def _generate_path(self, path: Path) -> None:
        if self._debounced(path):
            return

        print(f"Regenerating stub for {path}")

        stub_gen(paths=[path], out_dir=DEFAULT_OUT_DIR)

    def _regenerate_all(self) -> None:
        if self._debounced(SRC_ROOT):
            return
        regenerate_all_stubs()

    def _debounced(self, path: Path) -> bool:
        now = time.monotonic()
        last = self._last_seen.get(path, 0)
        if now - last < self.debounce_seconds:
            return True
        self._last_seen[path] = now
        return False


def remove_generated_stub(path: Path) -> bool:
    if not is_python_source_path(path):
        return False
    return remove_stub_for_source(path, DEFAULT_OUT_DIR)


def remove_generated_stub_tree(path: Path) -> bool:
    return remove_stubs_for_source_dir(path, DEFAULT_OUT_DIR)


def regenerate_all_stubs() -> None:
    print(f"Regenerating stubs for {SRC_ROOT}")
    stub_gen(paths=[SRC_ROOT], out_dir=DEFAULT_OUT_DIR)


def is_stub_relevant_source(path: Path) -> bool:
    if is_stub_source_path(path):
        return True
    return package_init_imports_component_defs(path)


def is_stub_source_path(path: Path) -> bool:
    return path.suffix == ".py" and not is_package_init_path(path)


def is_package_init_path(path: Path) -> bool:
    return path.name == "__init__.py"


def is_python_source_path(path: Path) -> bool:
    return path.suffix == ".py"


def package_init_imports_component_defs(path: Path) -> bool:
    if not is_package_init_path(path):
        return False

    try:
        module = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False

    return any(
        contains_component_def(import_path)
        for import_path in imported_module_paths(path, module)
    )


def imported_module_paths(path: Path, module: ast.Module) -> list[Path]:
    paths: list[Path] = []
    for node in module.body:
        if not isinstance(node, ast.ImportFrom) or node.module is None:
            continue

        base = import_base_path(path, node.level)
        import_path = base.joinpath(*node.module.split("."))
        paths.extend([import_path.with_suffix(".py"), import_path / "__init__.py"])
    return paths


def import_base_path(path: Path, level: int) -> Path:
    if level == 0:
        return SRC_ROOT

    base = path.parent
    for _ in range(level - 1):
        base = base.parent
    return base


def event_involves_stub_relevant_source(event) -> bool:
    return is_stub_relevant_source(Path(_ensure_str(event.src_path))) or is_stub_relevant_source(
        event_path(event)
    ) or generated_stub_has_reexports(Path(_ensure_str(event.src_path)))


def generated_stub_has_reexports(path: Path) -> bool:
    if not is_package_init_path(path):
        return False

    try:
        stub_path = DEFAULT_OUT_DIR / path.resolve().relative_to(SRC_ROOT).with_suffix(
            ".pyi"
        )
        stub_text = stub_path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return False

    return any(line.startswith("from ") for line in stub_text.splitlines())


def event_path(event) -> Path:
    return Path(getattr(event, "dest_path", None) or _ensure_str(event.src_path))


def main(args):
    observer = Observer()
    observer.schedule(
        StubWatchHandler(),
        str(SRC_ROOT),
        recursive=True,
    )

    observer.start()
    print(f"Watching {SRC_ROOT} for .py changes...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main([])
