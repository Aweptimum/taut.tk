from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass
class PropField:
    name: str
    internal_type: str
    external_type: str


@dataclass
class ComponentStub:
    name: str
    fields: list[PropField]


@dataclass
class ImportStub:
    module: str
    name: str
    export_name: str


def collect_protocols(module: ast.Module) -> dict[str, list[PropField]]:
    protocols: dict[str, list[PropField]] = {}
    for node in module.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(base_name(base) == "Protocol" for base in node.bases):
            continue

        protocols[node.name] = [
            PropField(
                statement.target.id,
                ast.unparse(statement.annotation),
                external_prop_type(ast.unparse(statement.annotation)),
            )
            for statement in node.body
            if isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
        ]
    return protocols


def collect_components(
    module: ast.Module,
    protocols: dict[str, list[PropField]],
) -> list[ComponentStub]:
    components: list[ComponentStub] = []
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and is_component_function(node):
            protocol_name = first_arg_annotation(node)
        elif isinstance(node, ast.ClassDef) and is_component_class(node):
            protocol_name = init_props_annotation(node)
        else:
            continue

        if protocol_name is None:
            components.append(ComponentStub(node.name, []))
        elif protocol_name in protocols:
            components.append(ComponentStub(node.name, protocols[protocol_name]))
    return components


def collect_public_imports(module: ast.Module) -> list[ImportStub]:
    imports: list[ImportStub] = []
    for node in module.body:
        if not isinstance(node, ast.ImportFrom) or node.module is None:
            continue
        if node.module in {"__future__", "typing"} or node.module.startswith("solid_tk"):
            continue
        module_name = "." * node.level + node.module
        for alias in node.names:
            export_name = alias.asname or alias.name
            if export_name.startswith("_"):
                continue
            imports.append(ImportStub(module_name, alias.name, export_name))
    return imports


def render_component(component: ComponentStub) -> list[str]:
    fields = [field for field in component.fields if field.name != "children"]
    children_field = next(
        (field for field in component.fields if field.name == "children"),
        None,
    )

    if not component.fields:
        return [
            f"def {component.name}("
            "*child_nodes: Any, children: Any = ..."
            ") -> runtime.Node: ..."
        ]

    lines = [f"def {component.name}(", "    *child_nodes: Any,"]
    lines.extend(f"    {field.name}: {field.external_type}," for field in fields)
    if children_field is not None:
        lines.append(f"    children: {children_field.external_type},")
    else:
        lines.append("    children: Any = ...,")
    lines.append(") -> runtime.Node: ...")
    return lines


def is_component_function(node: ast.FunctionDef) -> bool:
    return any(base_name(decorator) == "component" for decorator in node.decorator_list)


def is_component_class(node: ast.ClassDef) -> bool:
    return any(base_name(base) == "Component" for base in node.bases)


def first_arg_annotation(node: ast.FunctionDef) -> str | None:
    if not node.args.args:
        return None
    annotation = node.args.args[0].annotation
    return ast.unparse(annotation) if annotation is not None else None


def init_props_annotation(node: ast.ClassDef) -> str | None:
    for statement in node.body:
        if not isinstance(statement, ast.FunctionDef) or statement.name != "__init__":
            continue
        if len(statement.args.args) < 2:
            return None
        annotation = statement.args.args[1].annotation
        return ast.unparse(annotation) if annotation is not None else None
    return None


def external_prop_type(internal_type: str) -> str:
    if internal_type.startswith("Accessor[") and internal_type.endswith("]"):
        inner = internal_type.removeprefix("Accessor[").removesuffix("]")
        return f"{inner} | reactive.Accessor[{inner}]"
    if internal_type.startswith("reactive.Accessor[") and internal_type.endswith("]"):
        inner = internal_type.removeprefix("reactive.Accessor[").removesuffix("]")
        return f"{inner} | reactive.Accessor[{inner}]"
    if internal_type.startswith("Mutator[") and internal_type.endswith("]"):
        inner = internal_type.removeprefix("Mutator[").removesuffix("]")
        return f"reactive.Mutator[{inner}]"
    if internal_type.startswith("reactive.Mutator[") and internal_type.endswith("]"):
        return internal_type
    return "Any"


def base_name(node: ast.AST) -> str:
    match node:
        case ast.Name(id=name):
            return name
        case ast.Attribute(attr=name):
            return name
        case ast.Call(func=func):
            return base_name(func)
        case ast.Subscript(value=value):
            return base_name(value)
        case _:
            return ""

