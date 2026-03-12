from __future__ import annotations

import hashlib
import json
import struct
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .errors import RuntimeMintError

MAGIC = b"MINTDB01"
VERSION = 1
HEADER_FMT = "<8sIQQQQQQI32s"
HEADER_SIZE = struct.calcsize(HEADER_FMT)
CATALOG_RESERVED = 64 * 1024
CATALOG_START = HEADER_SIZE
DATA_START = CATALOG_START + CATALOG_RESERVED
BLOCK_HEADER_FMT = "<IIIIQII32s"
BLOCK_HEADER_SIZE = struct.calcsize(BLOCK_HEADER_FMT)
BLOCK_ACTIVE = 1
BLOCK_TOMBSTONE = 2


@dataclass
class TableMeta:
    table_id: int
    name: str
    schema_offset: int
    first_data_block_offset: int
    last_data_block_offset: int
    active_records: int
    removed_records: int
    version: int
    flags: int


class MintDB:
    def __init__(self):
        self.path: Optional[Path] = None
        self.catalog: Dict[str, TableMeta] = {}
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.header: Optional[Dict[str, Any]] = None

    def create(self, path: str) -> None:
        p = Path(path)
        if p.suffix.lower() != ".mintdb":
            raise RuntimeMintError("DB CREATE exige arquivo com extensão .mintdb.")
        p.parent.mkdir(parents=True, exist_ok=True)
        now = int(time.time())
        empty_catalog = self._serialize_catalog([], [])
        empty_catalog += b"\x00" * (CATALOG_RESERVED - len(empty_catalog))
        with p.open("wb") as f:
            header = self._pack_header(
                created_at=now,
                updated_at=now,
                catalog_offset=CATALOG_START,
                data_offset=DATA_START,
                free_offset=0,
                flags=0,
                checksum=b"\x00" * 32,
            )
            f.write(header)
            f.write(empty_catalog)
            checksum = self._compute_global_checksum(p)
            f.seek(0)
            f.write(self._pack_header(now, now, CATALOG_START, DATA_START, 0, 0, checksum))

    def open(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            raise RuntimeMintError(f"Banco não encontrado: {path}")
        with p.open("rb") as f:
            raw = f.read(HEADER_SIZE)
            if len(raw) != HEADER_SIZE:
                raise RuntimeMintError("Arquivo MintDB corrompido: header incompleto.")
            head = self._unpack_header(raw)
        if head["magic"] != MAGIC:
            raise RuntimeMintError("Arquivo inválido: assinatura MintDB ausente.")
        if head["version"] != VERSION:
            raise RuntimeMintError(f"Versão MintDB não suportada: {head['version']}.")
        self._validate_offsets(p, head)
        expected = self._compute_global_checksum(p)
        if expected != head["checksum"]:
            raise RuntimeMintError("Falha de integridade: arquivo MintDB foi alterado/corrompido.")
        self.path = p
        self.header = head
        tables, schemas = self._read_catalog()
        self.catalog = {t.name: t for t in tables}
        self.schemas = {s["name"]: s for s in schemas}

    def create_table(self, table_name: str, columns: List[Dict[str, Any]]) -> None:
        self._ensure_open()
        if table_name in self.catalog:
            raise RuntimeMintError(f"Tabela '{table_name}' já existe.")
        table_id = max((t.table_id for t in self.catalog.values()), default=0) + 1
        schema = {"name": table_name, "columns": columns}
        schema_bytes = json.dumps(schema, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        schema_offset = self._append_bytes(schema_bytes)
        meta = TableMeta(table_id, table_name, schema_offset, 0, 0, 0, 0, 1, 0)
        tables = list(self.catalog.values()) + [meta]
        schemas = list(self.schemas.values()) + [schema]
        self._write_catalog(tables, schemas)
        self.catalog[table_name] = meta
        self.schemas[table_name] = schema

    def append_record(self, table_name: str, record: Dict[str, Any]) -> None:
        self._ensure_open()
        meta = self._table_meta(table_name)
        rec_bytes = json.dumps(record, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        payload = struct.pack("<I", 1) + struct.pack("<I", len(rec_bytes)) + rec_bytes
        block_offset = self._append_block(meta.table_id, BLOCK_ACTIVE, payload, 1, 0)
        if meta.first_data_block_offset == 0:
            meta.first_data_block_offset = block_offset
        meta.last_data_block_offset = block_offset
        meta.active_records += 1
        meta.version += 1
        self._persist_table_meta(meta)

    def select(self, table_name: str) -> List[Dict[str, Any]]:
        meta = self._table_meta(table_name)
        rows: List[Dict[str, Any]] = []
        current = meta.first_data_block_offset
        while current:
            bh = self._read_block_header(current)
            if bh["table_id"] != meta.table_id:
                raise RuntimeMintError("Falha de integridade: bloco aponta para tabela inválida.")
            payload = self._read_bytes(current + BLOCK_HEADER_SIZE, bh["payload_size"])
            if hashlib.sha256(payload).digest() != bh["checksum"]:
                raise RuntimeMintError("Falha de integridade: bloco de dados corrompido.")
            rows.extend(self._decode_payload_rows(payload))
            current = bh["next_offset"]
        return [r for r in rows if not r.get("__deleted__", False)]

    def update(self, table_name: str, updater, predicate) -> int:
        rows = self.select(table_name)
        changed = 0
        for r in rows:
            if predicate(r):
                nr = dict(r)
                updater(nr)
                nr["__versioned_from__"] = r
                self.append_record(table_name, nr)
                self.append_record(table_name, {**r, "__deleted__": True})
                changed += 1
        return changed

    def delete(self, table_name: str, predicate) -> int:
        rows = self.select(table_name)
        removed = 0
        for r in rows:
            if predicate(r):
                self.append_record(table_name, {**r, "__deleted__": True})
                removed += 1
        if removed:
            meta = self._table_meta(table_name)
            meta.removed_records += removed
            self._persist_table_meta(meta)
        return removed

    def _decode_payload_rows(self, payload: bytes) -> List[Dict[str, Any]]:
        i = 0
        count = struct.unpack_from("<I", payload, i)[0]
        i += 4
        rows = []
        for _ in range(count):
            ln = struct.unpack_from("<I", payload, i)[0]
            i += 4
            raw = payload[i:i + ln]
            i += ln
            rows.append(json.loads(raw.decode("utf-8")))
        return rows

    def _append_block(self, table_id: int, status: int, payload: bytes, record_count: int, next_offset: int) -> int:
        self._ensure_open()
        assert self.path is not None
        with self.path.open("r+b") as f:
            f.seek(0, 2)
            offset = f.tell()
            checksum = hashlib.sha256(payload).digest()
            header = struct.pack(
                BLOCK_HEADER_FMT,
                1,
                table_id,
                len(payload),
                record_count,
                next_offset,
                status,
                0,
                checksum,
            )
            f.write(header)
            f.write(payload)
        return offset

    def _read_block_header(self, offset: int) -> Dict[str, Any]:
        assert self.path is not None
        with self.path.open("rb") as f:
            f.seek(offset)
            raw = f.read(BLOCK_HEADER_SIZE)
        if len(raw) != BLOCK_HEADER_SIZE:
            raise RuntimeMintError("Falha de integridade: header de bloco inválido.")
        ver, tid, psz, rcount, next_off, status, flags, checksum = struct.unpack(BLOCK_HEADER_FMT, raw)
        return {
            "version": ver,
            "table_id": tid,
            "payload_size": psz,
            "record_count": rcount,
            "next_offset": next_off,
            "status": status,
            "flags": flags,
            "checksum": checksum,
        }

    def _read_bytes(self, offset: int, size: int) -> bytes:
        assert self.path is not None
        with self.path.open("rb") as f:
            f.seek(offset)
            b = f.read(size)
        if len(b) != size:
            raise RuntimeMintError("Falha de integridade: leitura incompleta de bloco.")
        return b

    def _append_bytes(self, data: bytes) -> int:
        assert self.path is not None
        with self.path.open("r+b") as f:
            f.seek(0, 2)
            off = f.tell()
            f.write(data)
        return off

    def _read_catalog(self) -> Tuple[List[TableMeta], List[Dict[str, Any]]]:
        assert self.path is not None
        assert self.header is not None
        with self.path.open("rb") as f:
            f.seek(self.header["catalog_offset"])
            cat = f.read(CATALOG_RESERVED)
        return self._deserialize_catalog(cat)

    def _write_catalog(self, tables: List[TableMeta], schemas: List[Dict[str, Any]]) -> None:
        assert self.path is not None
        payload = self._serialize_catalog(tables, schemas)
        if len(payload) > CATALOG_RESERVED:
            raise RuntimeMintError("Catálogo excedeu limite da beta MintDB.")
        payload += b"\x00" * (CATALOG_RESERVED - len(payload))
        with self.path.open("r+b") as f:
            f.seek(CATALOG_START)
            f.write(payload)
        self._refresh_header_checksum()

    def _persist_table_meta(self, updated: TableMeta) -> None:
        tables = []
        for t in self.catalog.values():
            tables.append(updated if t.name == updated.name else t)
        self.catalog[updated.name] = updated
        self._write_catalog(tables, list(self.schemas.values()))

    def _serialize_catalog(self, tables: List[TableMeta], schemas: List[Dict[str, Any]]) -> bytes:
        obj = {
            "tables": [
                {
                    "table_id": t.table_id,
                    "name": t.name,
                    "schema_offset": t.schema_offset,
                    "first_data_block_offset": t.first_data_block_offset,
                    "last_data_block_offset": t.last_data_block_offset,
                    "active_records": t.active_records,
                    "removed_records": t.removed_records,
                    "version": t.version,
                    "flags": t.flags,
                }
                for t in tables
            ],
            "schemas": schemas,
            "free_blocks": [],
        }
        raw = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return struct.pack("<I", len(raw)) + raw

    def _deserialize_catalog(self, data: bytes) -> Tuple[List[TableMeta], List[Dict[str, Any]]]:
        ln = struct.unpack_from("<I", data, 0)[0]
        raw = data[4:4 + ln]
        if not raw:
            return [], []
        obj = json.loads(raw.decode("utf-8"))
        tables = [
            TableMeta(
                table_id=t["table_id"],
                name=t["name"],
                schema_offset=t["schema_offset"],
                first_data_block_offset=t["first_data_block_offset"],
                last_data_block_offset=t["last_data_block_offset"],
                active_records=t["active_records"],
                removed_records=t["removed_records"],
                version=t["version"],
                flags=t["flags"],
            )
            for t in obj.get("tables", [])
        ]
        return tables, obj.get("schemas", [])

    def _compute_global_checksum(self, p: Path) -> bytes:
        with p.open("rb") as f:
            b = f.read()
        zeroed = bytearray(b)
        start = struct.calcsize("<8sIQQQQQQI")
        zeroed[start:start + 32] = b"\x00" * 32
        return hashlib.sha256(bytes(zeroed)).digest()

    def _validate_offsets(self, p: Path, head: Dict[str, Any]) -> None:
        size = p.stat().st_size
        if head["catalog_offset"] != CATALOG_START or head["data_offset"] < DATA_START:
            raise RuntimeMintError("Falha de integridade: offsets de metadata inválidos.")
        if head["catalog_offset"] + CATALOG_RESERVED > size:
            raise RuntimeMintError("Falha de integridade: catálogo fora dos limites do arquivo.")

    def _pack_header(self, created_at: int, updated_at: int, catalog_offset: int, data_offset: int, free_offset: int, flags: int, checksum: bytes) -> bytes:
        return struct.pack(HEADER_FMT, MAGIC, VERSION, created_at, updated_at, catalog_offset, data_offset, free_offset, 0, flags, checksum)

    def _unpack_header(self, raw: bytes) -> Dict[str, Any]:
        magic, version, created, updated, catalog, data, free_off, reserved, flags, checksum = struct.unpack(HEADER_FMT, raw)
        return {
            "magic": magic,
            "version": version,
            "created_at": created,
            "updated_at": updated,
            "catalog_offset": catalog,
            "data_offset": data,
            "free_offset": free_off,
            "reserved": reserved,
            "flags": flags,
            "checksum": checksum,
        }

    def _refresh_header_checksum(self) -> None:
        assert self.path is not None
        assert self.header is not None
        now = int(time.time())
        checksum = self._compute_global_checksum(self.path)
        self.header["updated_at"] = now
        self.header["checksum"] = checksum
        with self.path.open("r+b") as f:
            f.seek(0)
            f.write(self._pack_header(
                self.header["created_at"],
                self.header["updated_at"],
                self.header["catalog_offset"],
                self.header["data_offset"],
                self.header["free_offset"],
                self.header["flags"],
                self.header["checksum"],
            ))

    def _table_meta(self, name: str) -> TableMeta:
        t = self.catalog.get(name)
        if t is None:
            raise RuntimeMintError(f"Tabela '{name}' não existe.")
        return t

    def _ensure_open(self) -> None:
        if self.path is None:
            raise RuntimeMintError("Nenhum banco aberto. Use DB OPEN.")
