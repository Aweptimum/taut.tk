from __future__ import annotations

import ast
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .stub_model import ComponentStub
from .stub_model import ImportStub
from .stub_model import collect_components
from .stub_model import collect_protocols
from .stub_model import collect_public_imports
from .stub_model import render_component

DEFAULT_OUT_DIR = Path("typings")
SKIPPED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "typings",
}


@dataclass
class GeneratedModule:
    output_path: Path
    import_path: str
    components: list[ComponentStub]
    public_imports: list[ImportStub]


def main_cli(args):
    main(args.paths, args.out_dir, args.in_place)


def main(paths: list[Path], out_dir: Path = DEFAULT_OUT_DIR, in_place=False) -> None:
    all_source_paths = list(expand_paths(paths))
    modules = [
        module
        for path in all_source_paths
        if (module := generate_module(path, out_dir, in_place=in_place)) is not None
    ]
    generated_import_paths = {module.import_path for module in modules}

    for module in modules:
        module.output_path.parent.mkdir(parents=True, exist_ok=True)
        module.output_path.write_text(
            render_stub(
                module.components,
                module.public_imports,
                generated_import_paths=generated_import_paths,
            ),
            encoding="utf-8",
        )

    if not in_place:
        write_package_exports(modules, all_source_paths, out_dir)


def expand_paths(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(
                child for child in path.rglob("*.py") if not is_skipped_path(child)
            )
        elif path.suffix == ".py":
            yield path


def is_skipped_path(path: Path) -> bool:
    return any(part in SKIPPED_DIRS for part in path.parts)


def output_path_for(path: Path, out_dir: Path, in_place: bool) -> Path:
    if in_place:
        return path.with_suffix(".pyi")

    rel = path.resolve().relative_to(Path.cwd())
    return out_dir / rel.with_suffix(".pyi")


def read_module(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return None


def remove_stub_for_source(
    path: Path,
    out_dir: Path = DEFAULT_OUT_DIR,
    in_place: bool = False,
) -> bool:
    try:
        output_path = output_path_for(path, out_dir, in_place)
    except ValueError:
        return False
    try:
        output_path.unlink()
    except FileNotFoundError:
        return False
    return True


def remove_stubs_for_source_dir(
    path: Path,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> bool:
    try:
        rel = path.resolve().relative_to(Path.cwd())
    except ValueError:
        return False
    output_dir = out_dir / rel
    if not output_dir.is_dir():
        return False

    shutil.rmtree(output_dir)
    return True


def generate_module(
    path: Path,
    out_dir: Path,
    *,
    in_place: bool,
) -> GeneratedModule | None:
    module = read_module(path)
    if module is None:
        return None
    components = collect_components(module, collect_protocols(module))
    if not components:
        return None
    output_path = output_path_for(path, out_dir, in_place)
    return GeneratedModule(
        output_path=output_path,
        import_path=module_import_path(path),
        components=components,
        public_imports=collect_public_imports(module),
    )


def contains_component_def(path: Path) -> bool:
    return bool(component_stubs_for(path))


def component_stubs_for(path: Path) -> list[ComponentStub]:
    module = read_module(path)
    if module is None:
        return []
    return collect_components(module, collect_protocols(module))


def module_import_path(path: Path) -> str:
    module_path = path.with_suffix("") if path.suffix == ".py" else path
    try:
        module_path = module_path.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        pass
    return ".".join(module_path.parts)


def render_stub(
    components: list[ComponentStub],
    public_imports: list[ImportStub] | None = None,
    generated_import_paths: set[str] | None = None,
) -> str:
    imports = collect_stub_imports(components)
    public_imports = public_imports or []
    generated_import_paths = generated_import_paths or set()
    public_import_lines = render_public_imports(public_imports, generated_import_paths)
    lines = ["from __future__ import annotations", ""]
    import_lines = format_imports([*imports, *public_import_lines])
    if import_lines:
        lines.extend([*import_lines, ""])
    for component in components:
        lines.extend(render_component(component))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_public_imports(
    public_imports: list[ImportStub],
    generated_import_paths: set[str],
) -> list[str]:
    lines: list[str] = []
    for import_stub in public_imports:
        import_path = f"{import_stub.module}.{import_stub.name}"
        if import_path in generated_import_paths:
            lines.append(
                f"from {import_stub.module} import {import_stub.name} "
                f"as {import_stub.export_name}"
            )
    return lines


def format_imports(imports: list[str]) -> list[str]:
    stdlib = sorted(line for line in imports if is_stdlib_import(line))
    relative = sorted(line for line in imports if line.startswith("from ."))
    absolute = sorted(
        line
        for line in imports
        if line not in stdlib and line not in relative
    )
    sections = [stdlib, absolute, relative]
    lines: list[str] = []
    for section in sections:
        if not section:
            continue
        if lines:
            lines.append("")
        lines.extend(section)
    return lines


def is_stdlib_import(line: str) -> bool:
    return line.startswith("from collections.") or line.startswith("from typing ")


def collect_stub_imports(components: list[ComponentStub]) -> list[str]:
    external_types = {
        field.external_type for component in components for field in component.fields
    }
    imports = []
    if any("Callable" in external_type for external_type in external_types):
        imports.append("from collections.abc import Callable")
    if components or "Any" in external_types:
        imports.append("from typing import Any")
    if components:
        imports.append("from taut import runtime")
    if any("reactive." in external_type for external_type in external_types):
        imports.append("from taut import reactive")
    return imports


def write_package_exports(
    modules: list[GeneratedModule],
    source_paths: list[Path],
    out_dir: Path,
) -> None:
    packages = package_marker_dirs(modules, source_paths, out_dir)
    components_by_module = {
        module.import_path: {component.name for component in module.components}
        for module in modules
    }
    generated_modules = {module.import_path for module in modules}
    attrs_by_package = public_attrs_by_package(modules)

    for package_dir in sorted(packages):
        marker = package_dir / "__init__.pyi"
        marker.parent.mkdir(parents=True, exist_ok=True)
        source_init_path = source_init_for_marker(package_dir, out_dir)
        marker.write_text(
            render_init_stub(
                source_init_path,
                components_by_module,
                generated_modules,
                attrs_by_package.get(module_import_path(source_init_path.parent), set()),
            ),
            encoding="utf-8",
        )


def public_attrs_by_package(modules: list[GeneratedModule]) -> dict[str, set[str]]:
    attrs_by_package: dict[str, set[str]] = {}
    for module in modules:
        package = module_import_path(Path(*module.import_path.split(".")[:-1]))
        if not package:
            continue
        for import_stub in module.public_imports:
            if import_stub.module == package:
                attrs_by_package.setdefault(package, set()).add(import_stub.export_name)
    return attrs_by_package


def package_marker_dirs(
    modules: list[GeneratedModule],
    source_paths: list[Path],
    out_dir: Path,
) -> set[Path]:
    package_dirs: set[Path] = set()
    out_dir = out_dir.resolve()
    for module in modules:
        directory = module.output_path.parent.resolve()
        while directory != out_dir and out_dir in directory.parents:
            package_dirs.add(directory)
            directory = directory.parent

    for init_path in source_paths:
        if init_path.name != "__init__.py":
            continue
        try:
            package_dirs.add(output_path_for(init_path, out_dir, in_place=False).parent)
        except ValueError:
            pass
    return package_dirs


def source_init_for_marker(package_dir: Path, out_dir: Path) -> Path:
    rel = package_dir.resolve().relative_to(out_dir.resolve())
    return Path.cwd() / rel / "__init__.py"


def render_init_stub(
    source_init_path: Path,
    components_by_module: dict[str, set[str]],
    generated_modules: set[str],
    package_attrs: set[str] | None = None,
) -> str:
    reexports: list[str] = []
    functions: list[str] = []
    attrs = sorted(package_attrs or set())
    module = read_module(source_init_path)

    package_import_path = module_import_path(source_init_path.parent)
    if module is not None:
        for node in module.body:
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                import_path = resolve_import_from(source_init_path, node)
                component_names = components_by_module.get(import_path)
                module_ref = marker_import_ref(package_import_path, import_path)
                for alias in node.names:
                    export_name = alias.asname or alias.name
                    if component_names and alias.name in component_names:
                        reexports.append(
                            f"from {module_ref} import {alias.name} as {export_name}"
                        )
                    elif f"{import_path}.{alias.name}" in generated_modules:
                        reexports.append(
                            f"from {module_ref} import {alias.name} as {export_name}"
                        )
            elif isinstance(node, ast.FunctionDef) and is_public_name(node.name):
                functions.append(render_function_stub(node))

    reexports.extend(
        f"from . import {name} as {name}"
        for name in attrs
        if f"{package_import_path}.{name}" in generated_modules
    )
    imports = (
        ["from typing import Any"]
        if any_function_uses_any(functions)
        else []
    )
    import_lines = format_imports([*imports, *reexports])
    sections = [["from __future__ import annotations"], import_lines, functions]
    lines = [line for section in sections if section for line in (*section, "")]
    return "\n".join(lines).rstrip() + "\n"


def is_public_name(name: str) -> bool:
    return not name.startswith("_")


def render_function_stub(node: ast.FunctionDef) -> str:
    returns = ast.unparse(node.returns) if node.returns is not None else "Any"
    return f"def {node.name}({ast.unparse(node.args)}) -> {returns}: ..."


def any_function_uses_any(functions: list[str]) -> bool:
    return any(" -> Any:" in function for function in functions)


def resolve_import_from(source_path: Path, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""

    package_path = source_path.parent
    for _ in range(node.level - 1):
        package_path = package_path.parent
    package_import_path = module_import_path(package_path)
    if not node.module:
        return package_import_path
    return f"{package_import_path}.{node.module}"


def marker_import_ref(package_import_path: str, import_path: str) -> str:
    package_parts = package_import_path.split(".")
    import_parts = import_path.split(".")
    common = 0
    for package_part, import_part in zip(package_parts, import_parts):
        if package_part != import_part:
            break
        common += 1

    up_levels = len(package_parts) - common
    remainder = ".".join(import_parts[common:])
    return "." * (up_levels + 1) + remainder
