from __future__ import annotations

from typing import Any, Dict, Optional

from .ast_nodes import MintType

SYSTEM_MEMBERS: Dict[str, MintType] = {
    "date": "string",
    "time": "string",
    "datetime": "string",
    "timestamp": "int",
    "year": "int",
    "month": "int",
    "day": "int",
    "weekday": "int",
    "hour": "int",
    "minute": "int",
    "second": "int",
}


def extract_collection_inner(value_type: Optional[MintType], collection_name: str) -> Optional[MintType]:
    if value_type is None:
        return None
    prefix = f"{collection_name}<"
    if not value_type.startswith(prefix) or not value_type.endswith(">"):
        return None
    return value_type[len(prefix):-1].strip()


def is_struct_collection(value_type: Optional[MintType], structs: Dict[str, Dict[str, MintType]]) -> bool:
    inner = extract_collection_inner(value_type, "table")
    if inner is None:
        inner = extract_collection_inner(value_type, "list")
    return inner is not None and inner in structs


def convert_string_to_type(raw: str, field_type: MintType, field_name: str) -> Any:
    if field_type == "string":
        return raw
    if field_type == "int":
        try:
            return int(raw)
        except ValueError:
            raise ValueError(f"valor '{raw}' para campo {field_name} type int")
    if field_type == "float":
        try:
            return float(raw)
        except ValueError:
            raise ValueError(f"valor '{raw}' para campo {field_name} type float")
    if field_type == "bool":
        if raw == "true":
            return True
        if raw == "false":
            return False
        raise ValueError(f"valor '{raw}' para campo {field_name} type bool")
    if field_type == "char":
        if len(raw) != 1:
            raise ValueError(f"valor '{raw}' para campo {field_name} type char")
        return raw
    raise ValueError(f"tipo não suportado em serialização: {field_type}")


def serialize_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
