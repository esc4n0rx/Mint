import tempfile
import unittest
from pathlib import Path

from mintlang.ast_nodes import Program
from mintlang.errors import RuntimeMintError
from mintlang.interpreter import Interpreter
from mintlang.lexer import Lexer
from mintlang.linter import Linter
from mintlang.mintdb import MintDB
from mintlang.parser import Parser


def parse_program(source: str) -> Program:
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


class MintDBBeta1IntegrityTests(unittest.TestCase):
    def test_append_blocks_duplicate_primary_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "dup_append.mintdb")
            db = MintDB()
            db.create(db_path)
            db.open(db_path)
            db.create_table("clients", [
                {"name": "id", "type": "int", "primary_key": True, "auto_increment": False},
                {"name": "name", "type": "string", "primary_key": False, "auto_increment": False},
            ])
            db.append_record("clients", {"id": 1, "name": "A"})
            with self.assertRaises(RuntimeMintError):
                db.append_record("clients", {"id": 1, "name": "B"})

    def test_append_struct_blocks_duplicate_primary_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dup_append_struct.mintdb"
            source = f'''STRUCT Client.
  id type int.
  name type string.
ENDSTRUCT.

program init.
  var c type Client.
initialization.
  DB CREATE "{db_path}".
  DB OPEN "{db_path}".
  TABLE CREATE clients (id int PRIMARY KEY, name string).
  c.id = 1.
  c.name = "A".
  APPEND STRUCT c INTO clients.
  APPEND STRUCT c INTO clients.
endprogram.
'''
            program = parse_program(source)
            self.assertTrue(all(i.severity in {"warning", "info"} for i in Linter().lint(program)))
            with self.assertRaises(RuntimeMintError):
                Interpreter().run(program)

    def test_update_blocks_primary_key_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "dup_update.mintdb")
            db = MintDB()
            db.create(db_path)
            db.open(db_path)
            db.create_table("clients", [
                {"name": "id", "type": "int", "primary_key": True, "auto_increment": False},
                {"name": "name", "type": "string", "primary_key": False, "auto_increment": False},
            ])
            db.append_record("clients", {"id": 1, "name": "A"})
            db.append_record("clients", {"id": 2, "name": "B"})
            with self.assertRaises(RuntimeMintError):
                db.update("clients", lambda r: r.update({"id": 2}), lambda r: r["id"] == 1)

    def test_delete_allows_reusing_primary_key_of_deleted_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "reuse_deleted_pk.mintdb")
            db = MintDB()
            db.create(db_path)
            db.open(db_path)
            db.create_table("clients", [
                {"name": "id", "type": "int", "primary_key": True, "auto_increment": False},
            ])
            db.append_record("clients", {"id": 1})
            db.delete("clients", lambda r: r["id"] == 1)
            db.append_record("clients", {"id": 1})
            self.assertEqual(len(db.select("clients")), 1)

    def test_db_create_fails_when_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "exists.mintdb")
            db = MintDB()
            db.create(db_path)
            with self.assertRaises(RuntimeMintError):
                db.create(db_path)

    def test_linter_warns_for_fixed_seed_on_persistent_db(self):
        source = '''program init.
initialization.
  DB OPEN "examples/mintdb/demo.mintdb".
  TABLE CREATE clients (id int PRIMARY KEY, name string).
  APPEND INTO clients VALUES (id = 1, name = "A").
endprogram.
'''
        program = parse_program(source)
        issues = Linter().lint(program)
        warning_messages = [i.message for i in issues if i.severity == "warning"]
        self.assertTrue(any("não idempotente" in m for m in warning_messages))

    def test_linter_warning_is_distinct_from_runtime_integrity_error(self):
        source = '''program init.
initialization.
  DB OPEN "examples/mintdb/demo.mintdb".
  TABLE CREATE clients (id int PRIMARY KEY).
  APPEND INTO clients VALUES (id = 1).
endprogram.
'''
        program = parse_program(source)
        issues = Linter().lint(program)
        self.assertTrue(any(i.severity == "warning" for i in issues))

        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "runtime_violation.mintdb")
            db = MintDB()
            db.create(db_path)
            db.open(db_path)
            db.create_table("clients", [{"name": "id", "type": "int", "primary_key": True, "auto_increment": False}])
            db.append_record("clients", {"id": 1})
            with self.assertRaises(RuntimeMintError):
                db.append_record("clients", {"id": 1})

    def test_reopen_preserves_primary_key_constraint(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "reopen_constraint.mintdb")
            db = MintDB()
            db.create(db_path)
            db.open(db_path)
            db.create_table("clients", [
                {"name": "id", "type": "int", "primary_key": True, "auto_increment": False},
            ])
            db.append_record("clients", {"id": 1})

            db.close()
            db2 = MintDB()
            db2.open(db_path)
            with self.assertRaises(RuntimeMintError):
                db2.append_record("clients", {"id": 1})


if __name__ == "__main__":
    unittest.main()
