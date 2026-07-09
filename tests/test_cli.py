from __future__ import annotations

from pathlib import Path

from watchdog.events import DirCreatedEvent
from watchdog.events import DirMovedEvent
from watchdog.events import FileCreatedEvent
from watchdog.events import FileDeletedEvent
from watchdog.events import FileModifiedEvent
from watchdog.events import FileMovedEvent

from solid_tk.cli import stubs
from solid_tk.cli import watch


def test_contains_component_def_returns_false_for_missing_file(tmp_path):
    assert not stubs.contains_component_def(tmp_path / "missing.py")


def test_remove_stub_for_source_deletes_matching_output(monkeypatch, tmp_path):
    source = tmp_path / "examples" / "counter.py"
    output = tmp_path / "typings" / "examples" / "counter.pyi"
    output.parent.mkdir(parents=True)
    output.write_text("def Counter() -> None: ...\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    assert stubs.remove_stub_for_source(source)
    assert not output.exists()


def test_remove_stubs_for_source_dir_deletes_matching_output_tree(monkeypatch, tmp_path):
    source = tmp_path / "examples" / "counter"
    output = tmp_path / "typings" / "examples" / "counter"
    component_stub = output / "component.pyi"
    package_stub = output / "__init__.pyi"
    component_stub.parent.mkdir(parents=True)
    component_stub.write_text("def Counter() -> None: ...\n", encoding="utf-8")
    package_stub.write_text("from .component import Counter as Counter\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    assert stubs.remove_stubs_for_source_dir(source)
    assert not output.exists()


def test_main_refreshes_stale_parent_package_markers(monkeypatch, tmp_path):
    source = tmp_path / "examples" / "counter" / "component.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "\n".join(
            [
                "from typing import Protocol",
                "from solid_tk import component",
                "from solid_tk import reactive",
                "",
                "class CounterProps(Protocol):",
                "    title: reactive.Accessor[str]",
                "",
                "@component",
                "def Counter(props: CounterProps):",
                "    ...",
            ]
        ),
        encoding="utf-8",
    )
    parent_marker = tmp_path / "typings" / "examples" / "__init__.pyi"
    parent_marker.parent.mkdir(parents=True)
    parent_marker.write_text(
        "from __future__ import annotations\n"
        "from .counter import Counter as Counter\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    stubs.main([tmp_path / "examples"], out_dir=tmp_path / "typings")

    assert parent_marker.read_text(encoding="utf-8") == (
        "from __future__ import annotations\n"
    )


def test_main_preserves_mutator_prop_types(monkeypatch, tmp_path):
    source = tmp_path / "examples" / "counter" / "component.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "\n".join(
            [
                "from typing import Protocol",
                "from solid_tk import component",
                "from solid_tk import reactive",
                "",
                "class CounterProps(Protocol):",
                "    count: reactive.Accessor[int]",
                "    set_count: reactive.Mutator[int]",
                "",
                "@component",
                "def Counter(props: CounterProps):",
                "    ...",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    stubs.main([tmp_path / "examples"], out_dir=tmp_path / "typings")

    assert (tmp_path / "typings" / "examples" / "counter" / "component.pyi").read_text(
        encoding="utf-8"
    ) == (
        "from __future__ import annotations\n"
        "\n"
        "from solid_tk import runtime\n"
        "from solid_tk import reactive\n"
        "\n"
        "def Counter(\n"
        "    *,\n"
        "    count: int | reactive.Accessor[int],\n"
        "    set_count: reactive.Mutator[int],\n"
        ") -> runtime.Node: ...\n"
    )


def test_main_writes_unannotated_component_as_no_prop_component(monkeypatch, tmp_path):
    source = tmp_path / "examples" / "layout_demo" / "component.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "\n".join(
            [
                "from solid_tk import component",
                "from examples.layout_demo import styles",
                "",
                "@component",
                "def layout_demo(props):",
                "    ...",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    stubs.main([tmp_path / "examples"], out_dir=tmp_path / "typings")

    assert (
        tmp_path / "typings" / "examples" / "layout_demo" / "component.pyi"
    ).read_text(encoding="utf-8") == (
        "from __future__ import annotations\n"
        "\n"
        "from typing import Any\n"
        "from solid_tk import runtime\n"
        "\n"
        "styles: Any\n"
        "\n"
        "def layout_demo() -> runtime.Node: ...\n"
    )
    assert (
        tmp_path / "typings" / "examples" / "layout_demo" / "__init__.pyi"
    ).read_text(encoding="utf-8") == (
        "from __future__ import annotations\n"
        "\n"
        "from typing import Any\n"
        "\n"
        "styles: Any\n"
    )


def test_main_writes_init_reexports_from_source_init(monkeypatch, tmp_path):
    component = tmp_path / "examples" / "counter" / "component.py"
    source_init = tmp_path / "examples" / "__init__.py"
    component.parent.mkdir(parents=True)
    component.write_text(
        "\n".join(
            [
                "from typing import Protocol",
                "from solid_tk import component",
                "from solid_tk import reactive",
                "",
                "class CounterProps(Protocol):",
                "    title: reactive.Accessor[str]",
                "",
                "class Other:",
                "    pass",
                "",
                "@component",
                "def Counter(props: CounterProps):",
                "    ...",
            ]
        ),
        encoding="utf-8",
    )
    source_init.write_text(
        "\n".join(
            [
                "from examples.counter.component import Counter as Counter",
                "from examples.counter.component import Other as Other",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    stubs.main([tmp_path / "examples"], out_dir=tmp_path / "typings")

    assert (tmp_path / "typings" / "examples" / "__init__.pyi").read_text(
        encoding="utf-8"
    ) == (
        "from __future__ import annotations\n"
        "\n"
        "from .counter.component import Counter as Counter\n"
    )
    assert (tmp_path / "typings" / "examples" / "counter" / "__init__.pyi").read_text(
        encoding="utf-8"
    ) == "from __future__ import annotations\n"


def test_main_writes_public_functions_from_source_init(monkeypatch, tmp_path):
    component = tmp_path / "examples" / "counter" / "component.py"
    source_init = tmp_path / "examples" / "counter" / "__init__.py"
    component.parent.mkdir(parents=True)
    component.write_text(
        "\n".join(
            [
                "from typing import Protocol",
                "from solid_tk import component",
                "from solid_tk import reactive",
                "",
                "class CounterProps(Protocol):",
                "    title: reactive.Accessor[str]",
                "",
                "@component",
                "def counter(props: CounterProps):",
                "    ...",
            ]
        ),
        encoding="utf-8",
    )
    source_init.write_text(
        "\n".join(
            [
                "from examples.counter.component import counter as counter",
                "",
                "def main() -> None:",
                "    ...",
                "",
                "def _private() -> None:",
                "    ...",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    stubs.main([tmp_path / "examples"], out_dir=tmp_path / "typings")

    assert (tmp_path / "typings" / "examples" / "counter" / "__init__.pyi").read_text(
        encoding="utf-8"
    ) == (
        "from __future__ import annotations\n"
        "\n"
        "from .component import counter as counter\n"
        "\n"
        "def main() -> None: ...\n"
    )


def test_main_writes_relative_reexports_from_nested_source_init(monkeypatch, tmp_path):
    component = tmp_path / "examples" / "component.py"
    source_init = tmp_path / "examples" / "counter" / "__init__.py"
    source_init.parent.mkdir(parents=True)
    component.write_text(
        "\n".join(
            [
                "from typing import Protocol",
                "from solid_tk import component",
                "from solid_tk import reactive",
                "",
                "class CounterProps(Protocol):",
                "    title: reactive.Accessor[str]",
                "",
                "@component",
                "def Counter(props: CounterProps):",
                "    ...",
            ]
        ),
        encoding="utf-8",
    )
    source_init.write_text(
        "from examples.component import Counter as Counter\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    stubs.main([tmp_path / "examples"], out_dir=tmp_path / "typings")

    assert (tmp_path / "typings" / "examples" / "counter" / "__init__.pyi").read_text(
        encoding="utf-8"
    ) == (
        "from __future__ import annotations\n"
        "\n"
        "from ..component import Counter as Counter\n"
    )


def test_watch_created_file_regenerates_all(monkeypatch, tmp_path):
    generated_paths = []

    def stub_gen(paths, out_dir) -> None:
        generated_paths.extend(paths)

    monkeypatch.setattr(watch, "SRC_ROOT", tmp_path)
    monkeypatch.setattr(watch, "stub_gen", stub_gen)

    handler = watch.StubWatchHandler()
    handler.on_created(
        FileCreatedEvent(str(tmp_path / "new.py"))
    )

    assert generated_paths == [tmp_path]


def test_watch_modified_init_file_with_component_reexports_regenerates_all(
    monkeypatch, tmp_path
):
    source_init = tmp_path / "examples" / "counter" / "__init__.py"
    component = tmp_path / "examples" / "component.py"
    generated_paths = []
    source_init.parent.mkdir(parents=True)
    component.write_text(
        "\n".join(
            [
                "from typing import Protocol",
                "from solid_tk import component",
                "from solid_tk import reactive",
                "",
                "class CounterProps(Protocol):",
                "    title: reactive.Accessor[str]",
                "",
                "@component",
                "def Counter(props: CounterProps):",
                "    ...",
            ]
        ),
        encoding="utf-8",
    )
    source_init.write_text(
        "from examples.component import Counter as Counter\n",
        encoding="utf-8",
    )

    def stub_gen(paths, out_dir) -> None:
        generated_paths.extend(paths)

    monkeypatch.setattr(watch, "SRC_ROOT", tmp_path)
    monkeypatch.setattr(watch, "stub_gen", stub_gen)

    handler = watch.StubWatchHandler()
    handler.on_modified(
        FileModifiedEvent(str(source_init))
    )

    assert generated_paths == [tmp_path]


def test_watch_modified_plain_init_file_is_ignored(monkeypatch, tmp_path):
    source_init = tmp_path / "examples" / "counter" / "__init__.py"
    generated_paths = []
    source_init.parent.mkdir(parents=True)
    source_init.write_text('"""Counter package."""\n', encoding="utf-8")

    def stub_gen(paths, out_dir) -> None:
        generated_paths.extend(paths)

    monkeypatch.setattr(watch, "SRC_ROOT", tmp_path)
    monkeypatch.setattr(watch, "stub_gen", stub_gen)

    handler = watch.StubWatchHandler()
    handler.on_modified(
        FileModifiedEvent(str(source_init))
    )

    assert generated_paths == []


def test_watch_moved_file_removes_old_stub_and_regenerates_all(monkeypatch, tmp_path):
    source = tmp_path / "old.py"
    destination = tmp_path / "new.py"
    removed_paths = []
    generated_paths = []

    def remove_generated_stub(path: Path) -> bool:
        removed_paths.append(path)
        return False

    def stub_gen(paths, out_dir) -> None:
        generated_paths.extend(paths)

    monkeypatch.setattr(watch, "SRC_ROOT", tmp_path)
    monkeypatch.setattr(watch, "remove_generated_stub", remove_generated_stub)
    monkeypatch.setattr(watch, "stub_gen", stub_gen)

    handler = watch.StubWatchHandler()
    handler.on_moved(
        FileMovedEvent(str(source), str(destination))
    )

    assert removed_paths == [source]
    assert generated_paths == [tmp_path]


def test_watch_moved_file_regenerates_all_when_destination_is_python(
    monkeypatch, tmp_path
):
    source = tmp_path / "old.py"
    destination = tmp_path / "new.py"
    removed_paths = []
    generated_paths = []

    def remove_generated_stub(path: Path) -> bool:
        removed_paths.append(path)
        return True

    def stub_gen(paths, out_dir) -> None:
        generated_paths.extend(paths)

    monkeypatch.setattr(watch, "SRC_ROOT", tmp_path)
    monkeypatch.setattr(watch, "remove_generated_stub", remove_generated_stub)
    monkeypatch.setattr(watch, "stub_gen", stub_gen)

    handler = watch.StubWatchHandler()
    handler.on_moved(
        FileMovedEvent(str(source), str(destination))
    )

    assert removed_paths == [source]
    assert generated_paths == [tmp_path]


def test_watch_moved_init_file_removes_old_stub_and_regenerates_all(
    monkeypatch, tmp_path
):
    source = tmp_path / "examples" / "counter" / "__init__.py"
    destination = tmp_path / "examples" / "__init__.py"
    component = tmp_path / "examples" / "counter" / "component.py"
    removed_paths = []
    generated_paths = []
    component.parent.mkdir(parents=True)
    component.write_text(
        "\n".join(
            [
                "from typing import Protocol",
                "from solid_tk import component",
                "from solid_tk import reactive",
                "",
                "class CounterProps(Protocol):",
                "    title: reactive.Accessor[str]",
                "",
                "@component",
                "def Counter(props: CounterProps):",
                "    ...",
            ]
        ),
        encoding="utf-8",
    )
    destination.write_text(
        "from examples.counter.component import Counter as Counter\n",
        encoding="utf-8",
    )

    def remove_generated_stub(path: Path) -> bool:
        removed_paths.append(path)
        return True

    def stub_gen(paths, out_dir) -> None:
        generated_paths.extend(paths)

    monkeypatch.setattr(watch, "SRC_ROOT", tmp_path)
    monkeypatch.setattr(watch, "remove_generated_stub", remove_generated_stub)
    monkeypatch.setattr(watch, "stub_gen", stub_gen)

    handler = watch.StubWatchHandler()
    handler.on_moved(
        FileMovedEvent(str(source), str(destination))
    )

    assert removed_paths == [source]
    assert generated_paths == [tmp_path]


def test_watch_moved_plain_init_file_is_ignored(monkeypatch, tmp_path):
    source = tmp_path / "examples" / "counter" / "__init__.py"
    destination = tmp_path / "examples" / "__init__.py"
    destination.parent.mkdir(parents=True)
    destination.write_text('"""Examples."""\n', encoding="utf-8")
    generated_paths = []

    def stub_gen(paths, out_dir) -> None:
        generated_paths.extend(paths)

    monkeypatch.setattr(watch, "SRC_ROOT", tmp_path)
    monkeypatch.setattr(watch, "stub_gen", stub_gen)

    handler = watch.StubWatchHandler()
    handler.on_moved(
        FileMovedEvent(str(source), str(destination))
    )

    assert generated_paths == []


def test_watch_moved_init_file_uses_existing_stub_reexports(
    monkeypatch, tmp_path
):
    source = tmp_path / "examples" / "counter" / "__init__.py"
    destination = tmp_path / "examples" / "__init__.py"
    old_stub = tmp_path / "typings" / "examples" / "counter" / "__init__.pyi"
    removed_paths = []
    generated_paths = []
    destination.parent.mkdir(parents=True)
    old_stub.parent.mkdir(parents=True)
    destination.write_text('"""Examples."""\n', encoding="utf-8")
    old_stub.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from .component import Counter as Counter\n",
        encoding="utf-8",
    )

    def remove_generated_stub(path: Path) -> bool:
        removed_paths.append(path)
        return True

    def stub_gen(paths, out_dir) -> None:
        generated_paths.extend(paths)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(watch, "SRC_ROOT", tmp_path)
    monkeypatch.setattr(watch, "remove_generated_stub", remove_generated_stub)
    monkeypatch.setattr(watch, "stub_gen", stub_gen)

    handler = watch.StubWatchHandler()
    handler.on_moved(
        FileMovedEvent(str(source), str(destination))
    )

    assert removed_paths == [source]
    assert generated_paths == [tmp_path]


def test_watch_deleted_event_removes_old_stub_and_regenerates_all(monkeypatch, tmp_path):
    source = tmp_path / "old.py"
    removed_paths = []
    generated_paths = []

    def remove_generated_stub(path: Path) -> bool:
        removed_paths.append(path)
        return True

    def stub_gen(paths, out_dir) -> None:
        generated_paths.extend(paths)

    monkeypatch.setattr(watch, "SRC_ROOT", tmp_path)
    monkeypatch.setattr(watch, "remove_generated_stub", remove_generated_stub)
    monkeypatch.setattr(watch, "stub_gen", stub_gen)

    handler = watch.StubWatchHandler()
    handler.on_deleted(
        FileDeletedEvent(str(source))
    )

    assert removed_paths == [source]
    assert generated_paths == [tmp_path]


def test_watch_moved_directory_removes_old_stubs_and_regenerates_all(
    monkeypatch, tmp_path
):
    source = tmp_path / "old"
    destination = tmp_path / "new"
    removed_paths = []
    generated_paths = []

    def remove_generated_stub_tree(path: Path) -> bool:
        removed_paths.append(path)
        return True

    def stub_gen(paths, out_dir) -> None:
        generated_paths.extend(paths)

    monkeypatch.setattr(watch, "SRC_ROOT", tmp_path)
    monkeypatch.setattr(watch, "remove_generated_stub_tree", remove_generated_stub_tree)
    monkeypatch.setattr(watch, "stub_gen", stub_gen)

    handler = watch.StubWatchHandler()
    handler.on_moved(
        DirMovedEvent(str(source), str(destination))
    )

    assert removed_paths == [source]
    assert generated_paths == [tmp_path]


def test_watch_created_directory_regenerates_all(monkeypatch, tmp_path):
    generated_paths = []

    def stub_gen(paths, out_dir) -> None:
        generated_paths.extend(paths)

    monkeypatch.setattr(watch, "SRC_ROOT", tmp_path)
    monkeypatch.setattr(watch, "stub_gen", stub_gen)

    handler = watch.StubWatchHandler()
    handler.on_created(
        DirCreatedEvent(str(tmp_path / "new"))
    )

    assert generated_paths == [tmp_path]
