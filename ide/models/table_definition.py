from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SUPPORTED_FIELD_TYPES = [
    "int",
    "float",
    "string",
    "char",
    "bool",
    "decimal",
    "date",
    "datetime",
    "time",
    "text",
    "long",
    "double",
    "bytes",
    "uuid",
    "json",
]


@dataclass
class FieldDefinition:
    name: str = ""
    description: str = ""
    field_type: str = "string"
    length: str = ""
    scale: str = ""
    required: bool = False
    primary_key: bool = False
    default_value: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "field_type": self.field_type,
            "length": self.length,
            "scale": self.scale,
            "required": self.required,
            "primary_key": self.primary_key,
            "default_value": self.default_value,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FieldDefinition":
        return cls(
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            field_type=str(data.get("field_type", "string")),
            length=str(data.get("length", "")),
            scale=str(data.get("scale", "")),
            required=bool(data.get("required", False)),
            primary_key=bool(data.get("primary_key", False)),
            default_value=str(data.get("default_value", "")),
            notes=str(data.get("notes", "")),
        )


@dataclass
class TableDefinition:
    name: str
    description: str = ""
    module: str = "core"
    fields: list[FieldDefinition] = field(default_factory=list)
    generated_code_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "module": self.module,
            "fields": [field.to_dict() for field in self.fields],
            "generated_code_path": self.generated_code_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TableDefinition":
        return cls(
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            module=str(data.get("module", "core")),
            fields=[FieldDefinition.from_dict(item) for item in data.get("fields", [])],
            generated_code_path=str(data.get("generated_code_path", "")),
        )
