from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from ide.models.table_definition import FieldDefinition, TableDefinition
from ide.services.workbench_service import WorkbenchService
from mintlang.mintdb import MintDB


class TableService:
    def __init__(self, workbench: WorkbenchService) -> None:
        self.workbench = workbench
        self._ensure_database()

    def _ensure_database(self) -> None:
        if self.workbench.database_path.exists():
            return
        db = MintDB()
        db.create(str(self.workbench.database_path))
        db.open(str(self.workbench.database_path))
        db.close()

    @contextmanager
    def _db(self):
        db = MintDB()
        db.open(str(self.workbench.database_path))
        try:
            yield db
        finally:
            db.close()

    def list_tables(self) -> list[TableDefinition]:
        with self._db() as db:
            tables = []
            for row in db.show_tables():
                payload = db.describe_table(row['table'])
                payload.update(db.schemas.get(row['table'], {}))
                definition = self._definition_from_db(payload)
                tables.append(definition)
            return tables

    def get_table(self, name: str) -> TableDefinition | None:
        with self._db() as db:
            try:
                payload = db.describe_table(name)
                payload.update(db.schemas.get(name, {}))
                return self._definition_from_db(payload)
            except Exception:
                return None

    def save_table(self, definition: TableDefinition) -> Path:
        with self._db() as db:
            if definition.name not in db.catalog:
                db.create_table(definition.name, [self._column_from_field(field) for field in definition.fields])
            schema = db.schemas[definition.name]
            schema['name'] = definition.name
            schema['description'] = definition.description
            schema['module'] = definition.module
            schema['generated_code_path'] = definition.generated_code_path
            schema['columns'] = [self._column_from_field(field) for field in definition.fields]
            db.schemas[definition.name] = schema
            db._write_catalog(list(db.catalog.values()), list(db.schemas.values()), db.indexes)
            db._refresh_header_checksum()
        return self.workbench.database_path

    def delete_table(self, name: str) -> None:
        with self._db() as db:
            if name not in db.catalog:
                return
            db.catalog.pop(name, None)
            db.schemas.pop(name, None)
            db.indexes.pop(name, None)
            db._write_catalog(list(db.catalog.values()), list(db.schemas.values()), db.indexes)
            db._refresh_header_checksum()

    def generate_mint_definition(self, definition: TableDefinition) -> Path:
        generated_dir = self.workbench.generated_dir / 'tables'
        generated_dir.mkdir(parents=True, exist_ok=True)
        file_path = generated_dir / f'{definition.name.lower()}.mint'
        cols = []
        for field in definition.fields:
            parts = [field.name, field.field_type]
            if field.primary_key:
                parts.extend(['primary', 'key'])
            cols.append(' '.join(parts))
        command = f"table create {definition.name} ({', '.join(cols)})."
        lines = [
            'db open ".mint_workbench/workbench.mintdb".',
            command,
            f'" Description: {definition.description}',
            '',
        ]
        file_path.write_text('\n'.join(lines), encoding='utf-8')
        definition.generated_code_path = str(file_path)
        self.save_table(definition)
        return file_path

    def ensure_example_table(self) -> None:
        if self.list_tables():
            return
        sample = TableDefinition(
            name='erp_customer',
            description='Cadastro de clientes do ERP Mint.',
            module='sales',
            fields=[
                FieldDefinition(name='id', description='Identificador', field_type='uuid', required=True, primary_key=True),
                FieldDefinition(name='name', description='Nome do cliente', field_type='string', length='120', required=True),
                FieldDefinition(name='tax_id', description='Documento fiscal', field_type='char', length='14'),
                FieldDefinition(name='active', description='Cliente ativo', field_type='bool', default_value='true'),
            ],
        )
        self.save_table(sample)
        self.generate_mint_definition(sample)

    def _column_from_field(self, field: FieldDefinition) -> dict:
        return {
            'name': field.name,
            'type': field.field_type,
            'description': field.description,
            'length': field.length,
            'scale': field.scale,
            'required': field.required,
            'primary_key': field.primary_key,
            'default_value': field.default_value,
            'notes': field.notes,
        }

    def _definition_from_db(self, payload: dict) -> TableDefinition:
        return TableDefinition(
            name=payload.get('table', payload.get('name', '')),
            description=payload.get('description', ''),
            module=payload.get('module', 'core'),
            generated_code_path=payload.get('generated_code_path', ''),
            fields=[
                FieldDefinition(
                    name=column.get('name', ''),
                    description=column.get('description', ''),
                    field_type=column.get('type', 'string'),
                    length=str(column.get('length', '')),
                    scale=str(column.get('scale', '')),
                    required=bool(column.get('required', False)),
                    primary_key=bool(column.get('primary_key', False)),
                    default_value=str(column.get('default_value', '')),
                    notes=str(column.get('notes', '')),
                )
                for column in payload.get('columns', [])
            ],
        )
