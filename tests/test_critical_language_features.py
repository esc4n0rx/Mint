import tempfile
import unittest

from mintlang.lexer import Lexer
from mintlang.parser import Parser
from mintlang.interpreter import Interpreter
from mintlang.linter import Linter


def parse_program(source: str):
    return Parser(Lexer(source).tokenize()).parse()


class CriticalLanguageFeaturesTests(unittest.TestCase):
    def test_break_continue_and_switch_parser(self):
        source = """
program init.
  var items type list<int>.
  var out type int = 0.
initialization.
  FOR item IN items.
    CONTINUE.
    BREAK.
  ENDFOR.
  SWITCH out.
  CASE 1.
    write("a").
  DEFAULT.
    write("b").
  ENDSWITCH.
endprogram.
"""
        program = parse_program(source)
        self.assertEqual(len(program.body), 2)

    def test_linter_rejects_break_outside_loop(self):
        source = """
program init.
initialization.
  BREAK.
endprogram.
"""
        issues = Linter().lint(parse_program(source))
        self.assertTrue(any("BREAK" in i.message for i in issues))

    def test_mintdb_join_transaction_upsert_and_alter(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = f"{tmp}/erp.mintdb"
            source = f'''
program init.
  var result type table<string>.
  var txErr type bool = false.
initialization.
  DB CREATE "{db_path}".
  DB OPEN "{db_path}".
  TABLE CREATE clients (id int PRIMARY KEY, name string).
  TABLE CREATE orders (id int PRIMARY KEY, client_id int, total decimal).
  DB BEGIN.
  UPSERT INTO clients VALUES (id = 1, name = "Paulo").
  UPSERT INTO orders VALUES (id = 10, client_id = 1, total = 19.90).
  DB COMMIT.
  ALTER TABLE clients ADD COLUMN email string.
  SELECT c.id, c.name, o.total FROM clients c JOIN orders o ON c.id == o.client_id INTO result.
endprogram.
'''
            program = parse_program(source)
            Interpreter().run(program)


if __name__ == "__main__":
    unittest.main()
