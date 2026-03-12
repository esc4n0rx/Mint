import tempfile
import unittest
from pathlib import Path

from mintlang.errors import RuntimeMintError
from mintlang.mintdb import MintDB


class MintDBBeta2Tests(unittest.TestCase):
    def test_show_tables_describe_and_index_create(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "beta2_show.mintdb")
            db = MintDB()
            db.create(db_path)
            db.open(db_path)
            db.create_table("clients", [
                {"name": "id", "type": "int", "primary_key": True, "auto_increment": False},
                {"name": "email", "type": "string", "primary_key": False, "auto_increment": False},
            ])
            db.create_index("idx_clients_email", "clients", "email")
            tables = db.show_tables()
            self.assertEqual(tables[0]["table"], "clients")
            desc = db.describe_table("clients")
            self.assertTrue(any(i["name"] == "idx_clients_email" for i in desc["indexes"]))

    def test_count_and_where_indexed_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "beta2_count.mintdb")
            db = MintDB()
            db.create(db_path)
            db.open(db_path)
            db.create_table("clients", [
                {"name": "id", "type": "int", "primary_key": True, "auto_increment": False},
                {"name": "email", "type": "string", "primary_key": False, "auto_increment": False},
            ])
            db.create_index("idx_clients_email", "clients", "email")
            db.append_record("clients", {"id": 1, "email": "a@mint.dev"})
            db.append_record("clients", {"id": 2, "email": "b@mint.dev"})
            self.assertEqual(db.count_records("clients"), 2)
            rows = db.select_where_equals("clients", "email", "b@mint.dev")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["id"], 2)

    def test_lock_blocks_second_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "beta2_lock.mintdb")
            db1 = MintDB()
            db1.create(db_path)
            db1.open(db_path)
            db2 = MintDB()
            with self.assertRaises(RuntimeMintError):
                db2.open(db_path)
            db1.close()
            db2.open(db_path)
            db2.close()

    def test_journal_recovery_pending_blocks_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "beta2_journal.mintdb"
            db = MintDB()
            db.create(str(db_path))
            db.open(str(db_path))
            journal = Path(str(db_path) + ".journal")
            journal.write_text('{"status":"pending","op":"APPEND"}', encoding="utf-8")
            db.close()
            db2 = MintDB()
            with self.assertRaises(RuntimeMintError):
                db2.open(str(db_path))

    def test_compact_preserves_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "beta2_compact.mintdb")
            db = MintDB()
            db.create(db_path)
            db.open(db_path)
            db.create_table("clients", [
                {"name": "id", "type": "int", "primary_key": True, "auto_increment": False},
                {"name": "name", "type": "string", "primary_key": False, "auto_increment": False},
            ])
            db.append_record("clients", {"id": 1, "name": "A"})
            db.append_record("clients", {"id": 2, "name": "B"})
            db.delete("clients", lambda r: r["id"] == 1)
            db.compact()
            rows = db.select("clients")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["id"], 2)


if __name__ == "__main__":
    unittest.main()
