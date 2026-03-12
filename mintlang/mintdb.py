from __future__ import annotations

import hashlib
import json
import os
import struct
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .errors import RuntimeMintError

MAGIC = b"MINTDB01"
VERSION = 2
SUPPORTED_VERSIONS = {1, 2}
HEADER_FMT = "<8sIQQQQQQI32s"
HEADER_SIZE = struct.calcsize(HEADER_FMT)
CATALOG_RESERVED = 64 * 1024
CATALOG_START = HEADER_SIZE
DATA_START = CATALOG_START + CATALOG_RESERVED
BLOCK_HEADER_FMT = "<IIIIQII32s"
BLOCK_HEADER_SIZE = struct.calcsize(BLOCK_HEADER_FMT)
BLOCK_ACTIVE = 1


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
        self._lock_fd: Optional[int] = None
        self._lock_path: Optional[Path] = None
        self.indexes: Dict[str, Dict[str, Dict[str, Any]]] = {}

    # lifecycle -----------------------------------------------------------------
    def create(self, path: str) -> None:
        p = Path(path)
        if p.suffix.lower() != ".mintdb":
            raise RuntimeMintError("DB CREATE exige arquivo com extensão .mintdb.")
        if p.exists():
            raise RuntimeMintError(f"DB CREATE falhou: arquivo já existe ({path}).")
        p.parent.mkdir(parents=True, exist_ok=True)
        now = int(time.time())
        empty_catalog = self._serialize_catalog([], [], {})
        empty_catalog += b"\x00" * (CATALOG_RESERVED - len(empty_catalog))
        with p.open("wb") as f:
            f.write(self._pack_header(now, now, CATALOG_START, DATA_START, 0, 0, b"\x00" * 32, VERSION))
            f.write(empty_catalog)
        checksum = self._compute_global_checksum(p)
        with p.open("r+b") as f:
            f.seek(0)
            f.write(self._pack_header(now, now, CATALOG_START, DATA_START, 0, 0, checksum, VERSION))

    def open(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            raise RuntimeMintError(f"Banco não encontrado: {path}")
        self._acquire_lock(p)
        try:
            self._recover_if_needed(p)
            with p.open("rb") as f:
                raw = f.read(HEADER_SIZE)
                if len(raw) != HEADER_SIZE:
                    raise RuntimeMintError("Arquivo MintDB corrompido: header incompleto.")
                head = self._unpack_header(raw)
            if head["magic"] != MAGIC:
                raise RuntimeMintError("Arquivo inválido: assinatura MintDB ausente.")
            if head["version"] not in SUPPORTED_VERSIONS:
                raise RuntimeMintError(f"Versão MintDB não suportada: {head['version']}.")
            self._validate_offsets(p, head)
            expected = self._compute_global_checksum(p)
            if expected != head["checksum"]:
                raise RuntimeMintError("Falha de integridade: arquivo MintDB foi alterado/corrompido.")
            self.path = p
            self.header = head
            tables, schemas, indexes = self._read_catalog()
            self.catalog = {t.name: t for t in tables}
            self.schemas = {s["name"]: s for s in schemas}
            self.indexes = indexes
            self._validate_structure()
            self._validate_indexes_consistency()
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        if self._lock_fd is not None:
            os.close(self._lock_fd)
            self._lock_fd = None
        if self._lock_path and self._lock_path.exists():
            try:
                self._lock_path.unlink()
            except OSError:
                pass
        self._lock_path = None

    # schema/inspection ----------------------------------------------------------
    def create_table(self, table_name: str, columns: List[Dict[str, Any]]) -> None:
        def _op() -> None:
            if table_name in self.catalog:
                raise RuntimeMintError(f"Tabela '{table_name}' já existe.")
            table_id = max((t.table_id for t in self.catalog.values()), default=0) + 1
            schema = {"name": table_name, "columns": columns}
            schema_bytes = json.dumps(schema, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            schema_offset = self._append_bytes(schema_bytes)
            meta = TableMeta(table_id, table_name, schema_offset, 0, 0, 0, 0, 1, 0)
            tables = list(self.catalog.values()) + [meta]
            schemas = list(self.schemas.values()) + [schema]
            self.indexes.setdefault(table_name, {})
            self._write_catalog(tables, schemas, self.indexes)
            self.catalog[table_name] = meta
            self.schemas[table_name] = schema
            pks = [c["name"] for c in columns if c.get("primary_key")]
            if pks:
                idx_name = f"pk_{table_name}"
                self.indexes[table_name][idx_name] = {"name": idx_name, "column": pks[0], "primary_key": True, "map": {}}
                self._write_catalog(list(self.catalog.values()), list(self.schemas.values()), self.indexes)

        self._run_write_op("TABLE_CREATE", _op)

    def create_index(self, index_name: str, table_name: str, column: str) -> None:
        def _op() -> None:
            self._table_meta(table_name)
            schema = self.schemas.get(table_name) or {}
            fields = {c["name"]: c for c in schema.get("columns", [])}
            if column not in fields:
                raise RuntimeMintError(f"Campo inexistente para índice: '{column}'.")
            tbl_indexes = self.indexes.setdefault(table_name, {})
            if index_name in tbl_indexes:
                raise RuntimeMintError(f"Índice duplicado: '{index_name}'.")
            for idx in tbl_indexes.values():
                if idx.get("column") == column:
                    raise RuntimeMintError(f"Campo '{column}' já possui índice na tabela '{table_name}'.")
            tbl_indexes[index_name] = {"name": index_name, "column": column, "primary_key": False, "map": {}}
            self._rebuild_indexes_for_table(table_name)
            self._write_catalog(list(self.catalog.values()), list(self.schemas.values()), self.indexes)

        self._run_write_op("INDEX_CREATE", _op)

    def show_tables(self) -> List[Dict[str, Any]]:
        self._ensure_open()
        return [
            {
                "table": t.name,
                "active_records": t.active_records,
                "removed_records": t.removed_records,
                "version": t.version,
            }
            for t in sorted(self.catalog.values(), key=lambda x: x.name)
        ]

    def describe_table(self, table_name: str) -> Dict[str, Any]:
        meta = self._table_meta(table_name)
        schema = self.schemas.get(table_name, {"columns": []})
        return {
            "table": table_name,
            "table_id": meta.table_id,
            "active_records": meta.active_records,
            "removed_records": meta.removed_records,
            "columns": schema.get("columns", []),
            "indexes": list(self.indexes.get(table_name, {}).values()),
        }

    # query/data -----------------------------------------------------------------
    def append_record(self, table_name: str, record: Dict[str, Any], *, enforce_primary_key: bool = True, operation: str = "APPEND") -> None:
        def _op() -> None:
            meta = self._table_meta(table_name)
            if enforce_primary_key and not record.get("__deleted__", False):
                self._validate_primary_key_on_append(table_name, record, operation)
            rec_bytes = json.dumps(record, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            payload = struct.pack("<I", 1) + struct.pack("<I", len(rec_bytes)) + rec_bytes
            block_offset = self._append_block(meta.table_id, BLOCK_ACTIVE, payload, 1, 0, previous_offset=meta.last_data_block_offset)
            if meta.first_data_block_offset == 0:
                meta.first_data_block_offset = block_offset
            meta.last_data_block_offset = block_offset
            if record.get("__deleted__", False):
                meta.removed_records += 1
            else:
                meta.active_records += 1
            meta.version += 1
            self._persist_table_meta(meta)
            self._apply_indexes_after_append(table_name, record)

        self._run_write_op(operation, _op)

    def select(self, table_name: str) -> List[Dict[str, Any]]:
        return self.select_where_equals(table_name, None, None)

    def select_where_equals(self, table_name: str, column: Optional[str], value: Any) -> List[Dict[str, Any]]:
        meta = self._table_meta(table_name)
        rows: List[Dict[str, Any]] = []
        candidates = self._candidate_keys_by_index(table_name, column, value) if column is not None else None
        current = meta.first_data_block_offset
        while current:
            bh = self._read_block_header(current)
            self._validate_block_header(current, bh)
            if bh["table_id"] != meta.table_id:
                raise RuntimeMintError("Falha de integridade: bloco aponta para tabela inválida.")
            payload = self._read_bytes(current + BLOCK_HEADER_SIZE, bh["payload_size"])
            if hashlib.sha256(payload).digest() != bh["checksum"]:
                raise RuntimeMintError("Falha de integridade: bloco de dados corrompido.")
            decoded = self._decode_payload_rows(payload)
            if candidates is not None:
                decoded = [r for r in decoded if self._candidate_match(table_name, r, candidates)]
            rows.extend(decoded)
            current = bh["next_offset"]

        primary_keys = self._primary_key_columns(table_name)
        if not primary_keys:
            result = [r for r in rows if not r.get("__deleted__", False)]
        else:
            active_by_key: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
            for row in rows:
                key = self._primary_key_tuple(row, primary_keys)
                if row.get("__deleted__", False):
                    active_by_key.pop(key, None)
                else:
                    active_by_key[key] = row
            result = list(active_by_key.values())
        if column is not None:
            result = [r for r in result if r.get(column) == value]
        return result

    def count_records(self, table_name: str, column: Optional[str] = None, value: Any = None) -> int:
        if column is None:
            meta = self._table_meta(table_name)
            return max(meta.active_records - meta.removed_records, 0)
        return len(self.select_where_equals(table_name, column, value))

    def update(self, table_name: str, updater, predicate) -> int:
        rows = self.select(table_name)
        changed = 0
        updates: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        for r in rows:
            if predicate(r):
                nr = dict(r)
                updater(nr)
                nr["__versioned_from__"] = r
                updates.append((r, nr))
                changed += 1
        if not updates:
            return 0
        self._validate_primary_key_on_update(table_name, rows, updates)

        def _op() -> None:
            for original, updated in updates:
                self._append_record_no_tx(table_name, updated)
                self._append_record_no_tx(table_name, {**original, "__deleted__": True})
            self._rebuild_indexes_for_table(table_name)
            self._refresh_header_checksum()

        self._run_write_op("UPDATE", _op)
        return changed

    def delete(self, table_name: str, predicate) -> int:
        rows = self.select(table_name)
        to_remove = [r for r in rows if predicate(r)]
        if not to_remove:
            return 0

        def _op() -> None:
            for r in to_remove:
                self._append_record_no_tx(table_name, {**r, "__deleted__": True})
            self._rebuild_indexes_for_table(table_name)
            self._refresh_header_checksum()

        self._run_write_op("DELETE", _op)
        return len(to_remove)

    def compact(self) -> None:
        self._ensure_open()
        assert self.path is not None

        def _op() -> None:
            rows_by_table = {name: self.select(name) for name in self.catalog.keys()}
            old_path = self.path
            tmp = Path(str(old_path) + ".compact.tmp.mintdb")
            if tmp.exists():
                tmp.unlink()
            new_db = MintDB()
            new_db.create(str(tmp))
            new_db.open(str(tmp))
            for name, schema in self.schemas.items():
                new_db.create_table(name, schema.get("columns", []))
            for tname, idx_map in self.indexes.items():
                for idx in idx_map.values():
                    if idx.get("primary_key"):
                        continue
                    new_db.create_index(idx["name"], tname, idx["column"])
            for tname, rows in rows_by_table.items():
                for row in rows:
                    new_db.append_record(tname, row, operation="COMPACT_REWRITE")
            new_db.close()
            os.replace(tmp, old_path)
            with old_path.open("rb") as f:
                raw = f.read(HEADER_SIZE)
            self.header = self._unpack_header(raw)
            self.path = old_path
            tables, schemas, indexes = self._read_catalog()
            self.catalog = {t.name: t for t in tables}
            self.schemas = {s["name"]: s for s in schemas}
            self.indexes = indexes

        self._run_write_op("DB_COMPACT", _op)

    # integrity/locks/journal -----------------------------------------------------
    def _run_write_op(self, op_name: str, fn) -> None:
        self._ensure_open_or_creating()
        self._ensure_lock_valid()
        self._write_journal({"status": "pending", "op": op_name, "time": int(time.time())})
        try:
            fn()
            self._refresh_header_checksum()
            self._clear_journal()
        except Exception:
            self._write_journal({"status": "failed", "op": op_name, "time": int(time.time())})
            raise

    def _ensure_open_or_creating(self) -> None:
        if self.path is None:
            raise RuntimeMintError("Nenhum banco aberto. Use DB OPEN.")

    def _ensure_lock_valid(self) -> None:
        if self._lock_fd is None or self._lock_path is None or not self._lock_path.exists():
            raise RuntimeMintError("Lock inválido: operação de escrita bloqueada.")

    def _acquire_lock(self, db_path: Path) -> None:
        lock_path = Path(str(db_path) + ".lock")
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("utf-8"))
        except FileExistsError:
            raise RuntimeMintError("Lock já em uso: banco aberto para escrita por outra sessão.")
        self._lock_fd = fd
        self._lock_path = lock_path

    def _journal_path(self, db_path: Optional[Path] = None) -> Path:
        p = db_path or self.path
        assert p is not None
        return Path(str(p) + ".journal")

    def _write_journal(self, obj: Dict[str, Any]) -> None:
        jp = self._journal_path()
        jp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")

    def _clear_journal(self) -> None:
        jp = self._journal_path()
        if jp.exists():
            jp.unlink()

    def _recover_if_needed(self, db_path: Path) -> None:
        jp = self._journal_path(db_path)
        if not jp.exists():
            return
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeMintError("Journal corrompido: recovery impossível.") from exc
        status = data.get("status")
        if status == "failed":
            raise RuntimeMintError("Recovery impossível: operação anterior falhou e exigiu intervenção manual.")
        if status == "pending":
            raise RuntimeMintError("Recovery necessário: operação interrompida detectada no journal.")
        jp.unlink(missing_ok=True)

    def _validate_structure(self) -> None:
        self._ensure_open()
        assert self.path is not None
        size = self.path.stat().st_size
        seen_ranges: List[Tuple[int, int]] = []
        table_ids = {t.table_id for t in self.catalog.values()}
        for table in self.catalog.values():
            if table.first_data_block_offset and table.first_data_block_offset < DATA_START:
                raise RuntimeMintError("Estrutura inconsistente: offset de bloco inicial inválido.")
            current = table.first_data_block_offset
            guard = set()
            while current:
                if current in guard:
                    raise RuntimeMintError("Estrutura inconsistente: encadeamento cíclico de blocos.")
                guard.add(current)
                bh = self._read_block_header(current)
                self._validate_block_header(current, bh)
                if bh["table_id"] not in table_ids:
                    raise RuntimeMintError("Estrutura inconsistente: bloco referencia tabela inexistente.")
                end = current + BLOCK_HEADER_SIZE + bh["payload_size"]
                if end > size:
                    raise RuntimeMintError("Estrutura inconsistente: bloco fora dos limites do arquivo.")
                for start2, end2 in seen_ranges:
                    if not (end <= start2 or current >= end2):
                        raise RuntimeMintError("Estrutura inconsistente: blocos sobrepostos detectados.")
                seen_ranges.append((current, end))
                current = bh["next_offset"]

    def _validate_block_header(self, offset: int, bh: Dict[str, Any]) -> None:
        assert self.path is not None
        size = self.path.stat().st_size
        if bh["version"] != 1:
            raise RuntimeMintError("Estrutura inconsistente: versão de bloco inválida.")
        if bh["payload_size"] <= 0:
            raise RuntimeMintError("Estrutura inconsistente: payload de bloco inválido.")
        if bh["next_offset"] and bh["next_offset"] <= offset:
            raise RuntimeMintError("Estrutura inconsistente: ponteiro next_offset inválido.")
        if bh["next_offset"] and bh["next_offset"] >= size:
            raise RuntimeMintError("Estrutura inconsistente: next_offset fora dos limites do arquivo.")

    def _validate_indexes_consistency(self) -> None:
        for table_name, idx_map in self.indexes.items():
            rows = self.select(table_name)
            for idx in idx_map.values():
                col = idx.get("column")
                if not col:
                    raise RuntimeMintError("Índice inconsistente: coluna ausente.")
                for val_key, pk_list in idx.get("map", {}).items():
                    for pk in pk_list:
                        if not any(self._primary_key_tuple(r, self._primary_key_columns(table_name)) == tuple(pk) for r in rows):
                            raise RuntimeMintError("Índice inconsistente: aponta para registro inválido.")

    # low-level ------------------------------------------------------------------
    def _append_record_no_tx(self, table_name: str, record: Dict[str, Any]) -> None:
        meta = self._table_meta(table_name)
        rec_bytes = json.dumps(record, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        payload = struct.pack("<I", 1) + struct.pack("<I", len(rec_bytes)) + rec_bytes
        block_offset = self._append_block(meta.table_id, BLOCK_ACTIVE, payload, 1, 0, previous_offset=meta.last_data_block_offset)
        if meta.first_data_block_offset == 0:
            meta.first_data_block_offset = block_offset
        meta.last_data_block_offset = block_offset
        if record.get("__deleted__", False):
            meta.removed_records += 1
        else:
            meta.active_records += 1
        meta.version += 1
        self._persist_table_meta(meta)

    def _primary_key_columns(self, table_name: str) -> List[str]:
        schema = self.schemas.get(table_name)
        if schema is None:
            return []
        return [c["name"] for c in schema.get("columns", []) if c.get("primary_key")]

    @staticmethod
    def _primary_key_tuple(record: Dict[str, Any], primary_keys: List[str]) -> Tuple[Any, ...]:
        return tuple(record.get(pk) for pk in primary_keys)

    def _validate_primary_key_on_append(self, table_name: str, record: Dict[str, Any], operation: str) -> None:
        primary_keys = self._primary_key_columns(table_name)
        if not primary_keys:
            return
        key = self._primary_key_tuple(record, primary_keys)
        for pk in primary_keys:
            if pk not in record:
                raise RuntimeMintError(
                    f"Violação de chave primária em {operation} na tabela '{table_name}': campo '{pk}' ausente."
                )
            if record.get(pk) is None:
                raise RuntimeMintError(
                    f"Violação de chave primária em {operation} na tabela '{table_name}': campo '{pk}' não pode ser nulo."
                )
        for row in self.select(table_name):
            if self._primary_key_tuple(row, primary_keys) == key:
                raise RuntimeMintError(
                    f"Violação de chave primária em {operation} na tabela '{table_name}': registro com chave {key} já existe."
                )

    def _validate_primary_key_on_update(
        self,
        table_name: str,
        rows: List[Dict[str, Any]],
        updates: List[Tuple[Dict[str, Any], Dict[str, Any]]],
    ) -> None:
        primary_keys = self._primary_key_columns(table_name)
        if not primary_keys:
            return

        updated_by_id = {id(original): updated for original, updated in updates}
        key_owner: Dict[Tuple[Any, ...], int] = {}
        for row in rows:
            candidate = updated_by_id.get(id(row), row)
            for pk in primary_keys:
                if candidate.get(pk) is None:
                    raise RuntimeMintError(
                        f"Violação de chave primária em UPDATE na tabela '{table_name}': campo '{pk}' não pode ser nulo."
                    )
            key = self._primary_key_tuple(candidate, primary_keys)
            owner = key_owner.get(key)
            if owner is not None and owner != id(row):
                raise RuntimeMintError(
                    f"Violação de chave primária em UPDATE na tabela '{table_name}': chave {key} já existe em outro registro ativo."
                )
            key_owner[key] = id(row)

    def _apply_indexes_after_append(self, table_name: str, record: Dict[str, Any]) -> None:
        if table_name not in self.indexes:
            return
        self._rebuild_indexes_for_table(table_name)
        self._write_catalog(list(self.catalog.values()), list(self.schemas.values()), self.indexes)

    def _rebuild_indexes_for_table(self, table_name: str) -> None:
        idx_map = self.indexes.get(table_name, {})
        if not idx_map:
            return
        rows = self.select(table_name)
        pks = self._primary_key_columns(table_name)
        for idx in idx_map.values():
            col = idx["column"]
            m: Dict[str, List[List[Any]]] = {}
            for row in rows:
                val_key = json.dumps(row.get(col), separators=(",", ":"), ensure_ascii=False)
                m.setdefault(val_key, []).append(list(self._primary_key_tuple(row, pks)))
            idx["map"] = m

    def _candidate_keys_by_index(self, table_name: str, column: str, value: Any) -> Optional[List[Tuple[Any, ...]]]:
        for idx in self.indexes.get(table_name, {}).values():
            if idx.get("column") == column:
                val_key = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
                return [tuple(x) for x in idx.get("map", {}).get(val_key, [])]
        return None

    def _candidate_match(self, table_name: str, row: Dict[str, Any], candidates: List[Tuple[Any, ...]]) -> bool:
        pks = self._primary_key_columns(table_name)
        if not pks:
            return True
        return self._primary_key_tuple(row, pks) in set(candidates)

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

    def _append_block(self, table_id: int, status: int, payload: bytes, record_count: int, next_offset: int, previous_offset: int = 0) -> int:
        self._ensure_open()
        assert self.path is not None
        with self.path.open("r+b") as f:
            f.seek(0, 2)
            offset = f.tell()
            checksum = hashlib.sha256(payload).digest()
            header = struct.pack(BLOCK_HEADER_FMT, 1, table_id, len(payload), record_count, next_offset, status, 0, checksum)
            f.write(header)
            f.write(payload)
            if previous_offset:
                f.seek(previous_offset)
                previous_raw = f.read(BLOCK_HEADER_SIZE)
                if len(previous_raw) != BLOCK_HEADER_SIZE:
                    raise RuntimeMintError("Falha de integridade: header de bloco anterior inválido.")
                ver, tid, psz, rcount, _prev_next, prev_status, prev_flags, prev_checksum = struct.unpack(BLOCK_HEADER_FMT, previous_raw)
                patched = struct.pack(BLOCK_HEADER_FMT, ver, tid, psz, rcount, offset, prev_status, prev_flags, prev_checksum)
                f.seek(previous_offset)
                f.write(patched)
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

    def _read_catalog(self) -> Tuple[List[TableMeta], List[Dict[str, Any]], Dict[str, Dict[str, Dict[str, Any]]]]:
        assert self.path is not None
        assert self.header is not None
        with self.path.open("rb") as f:
            f.seek(self.header["catalog_offset"])
            cat = f.read(CATALOG_RESERVED)
        return self._deserialize_catalog(cat, self.header["version"])

    def _write_catalog(self, tables: List[TableMeta], schemas: List[Dict[str, Any]], indexes: Dict[str, Dict[str, Dict[str, Any]]]) -> None:
        assert self.path is not None
        payload = self._serialize_catalog(tables, schemas, indexes)
        if len(payload) > CATALOG_RESERVED:
            raise RuntimeMintError("Catálogo excedeu limite da beta MintDB.")
        payload += b"\x00" * (CATALOG_RESERVED - len(payload))
        with self.path.open("r+b") as f:
            f.seek(CATALOG_START)
            f.write(payload)

    def _persist_table_meta(self, updated: TableMeta) -> None:
        tables = [updated if t.name == updated.name else t for t in self.catalog.values()]
        self.catalog[updated.name] = updated
        self._write_catalog(tables, list(self.schemas.values()), self.indexes)

    def _serialize_catalog(self, tables: List[TableMeta], schemas: List[Dict[str, Any]], indexes: Dict[str, Dict[str, Dict[str, Any]]]) -> bytes:
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
            "indexes": indexes,
            "free_blocks": [],
        }
        raw = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return struct.pack("<I", len(raw)) + raw

    def _deserialize_catalog(self, data: bytes, version: int) -> Tuple[List[TableMeta], List[Dict[str, Any]], Dict[str, Dict[str, Dict[str, Any]]]]:
        ln = struct.unpack_from("<I", data, 0)[0]
        raw = data[4:4 + ln]
        if not raw:
            return [], [], {}
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
        indexes = obj.get("indexes", {}) if version >= 2 else {}
        return tables, obj.get("schemas", []), indexes

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

    def _pack_header(self, created_at: int, updated_at: int, catalog_offset: int, data_offset: int, free_offset: int, flags: int, checksum: bytes, version: int = VERSION) -> bytes:
        return struct.pack(HEADER_FMT, MAGIC, version, created_at, updated_at, catalog_offset, data_offset, free_offset, 0, flags, checksum)

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
        self.header["version"] = VERSION
        with self.path.open("r+b") as f:
            f.seek(0)
            f.write(self._pack_header(self.header["created_at"], self.header["updated_at"], self.header["catalog_offset"], self.header["data_offset"], self.header["free_offset"], self.header["flags"], self.header["checksum"], version=VERSION))

    def _table_meta(self, name: str) -> TableMeta:
        t = self.catalog.get(name)
        if t is None:
            raise RuntimeMintError(f"Tabela '{name}' não existe.")
        return t

    def _ensure_open(self) -> None:
        if self.path is None:
            raise RuntimeMintError("Nenhum banco aberto. Use DB OPEN.")
