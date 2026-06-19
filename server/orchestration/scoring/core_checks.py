from __future__ import annotations

import importlib.util
from typing import Any

import sqlparse

from orchestration.planning.plan_schema import AgentSpec, ExpectedOutputField


def _expected_output(spec: AgentSpec | dict[str, Any]) -> dict[str, ExpectedOutputField | dict[str, Any]]:
    if isinstance(spec, AgentSpec):
        return spec.expected_output
    return spec.get("expected_output", spec)


def _field_value(field: ExpectedOutputField | dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(field, ExpectedOutputField):
        return getattr(field, key, default)
    return field.get(key, default)


def all_required_fields_present(output: dict[str, Any], spec: AgentSpec | dict[str, Any]) -> bool:
    expected = _expected_output(spec)
    for field_name, field in expected.items():
        if _field_value(field, "required", True) and field_name not in output:
            return False
    return True


def no_nullable_pk(output: dict[str, Any], spec: AgentSpec | dict[str, Any]) -> bool:
    pk_field = output.get("pk_field")
    if not pk_field:
        return False
    columns = output.get("columns") or []
    if not isinstance(columns, list):
        return False
    for column in columns:
        if not isinstance(column, dict):
            continue
        if column.get("name") == pk_field and column.get("nullable") is True:
            return False
    return True


def types_are_valid(output: dict[str, Any], spec: AgentSpec | dict[str, Any]) -> bool:
    expected = _expected_output(spec)
    type_map = {
        "str": str,
        "int": int,
        "float": (int, float),
        "bool": bool,
        "list": list,
        "dict": dict,
    }
    for field_name, field in expected.items():
        if field_name not in output:
            continue
        value = output[field_name]
        if value is None:
            if _field_value(field, "nullable", False):
                continue
            return False
        expected_type = _field_value(field, "type", "any")
        if expected_type != "any" and not isinstance(value, type_map[expected_type]):
            return False
        min_length = _field_value(field, "min_length")
        if min_length is not None and hasattr(value, "__len__") and len(value) < int(min_length):
            return False
    return True


def output_not_empty(output: dict[str, Any], spec: AgentSpec | dict[str, Any]) -> bool:
    if not output:
        return False
    return any(value not in (None, "", [], {}) for value in output.values())


def imports_resolve(output: dict[str, Any], spec: AgentSpec | dict[str, Any]) -> bool:
    imports = output.get("imports", [])
    if imports in (None, ""):
        return True
    if not isinstance(imports, list):
        return False
    for import_name in imports:
        if not import_name:
            continue
        module_name = str(import_name).split()[0].strip()
        if module_name.endswith(".py") or "/" in module_name:
            continue
        try:
            if importlib.util.find_spec(module_name) is None:
                return False
        except (ImportError, ModuleNotFoundError, ValueError):
            return False
    return True


def routes_not_empty(output: dict[str, Any], spec: AgentSpec | dict[str, Any]) -> bool:
    routes = output.get("routes")
    return isinstance(routes, list) and len(routes) > 0


def sql_syntax_valid(output: dict[str, Any], spec: AgentSpec | dict[str, Any]) -> bool:
    sql = output.get("create_sql") or output.get("sql")
    if not sql:
        return False
    if not isinstance(sql, str):
        return False
    statements = [statement for statement in sqlparse.parse(sql) if statement.tokens]
    if not statements:
        return False
    return all(statement.get_type() != "UNKNOWN" for statement in statements)


CORE_CHECKS = {
    "all_required_fields_present": all_required_fields_present,
    "no_nullable_pk": no_nullable_pk,
    "types_are_valid": types_are_valid,
    "output_not_empty": output_not_empty,
    "imports_resolve": imports_resolve,
    "routes_not_empty": routes_not_empty,
    "sql_syntax_valid": sql_syntax_valid,
}
