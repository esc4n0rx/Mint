import tempfile
import unittest
from pathlib import Path

from mintlang.errors import LexerError, RuntimeMintError
from mintlang.interpreter import Interpreter
from mintlang.lexer import Lexer
from mintlang.linter import Linter
from mintlang.parser import Parser


def parse_program(source: str):
    return Parser(Lexer(source).tokenize()).parse()


class RuntimeAndLinterGuardsTests(unittest.TestCase):
    def test_linter_detects_division_by_zero_literal(self):
        source = '''program init.
  var x type int.
initialization.
  x = 10 / 0.
endprogram.
'''
        issues = Linter().lint(parse_program(source))
        self.assertTrue(any("zero" in i.message.lower() for i in issues))

    def test_for_scope_does_not_leak_declared_variables(self):
        source = '''program init.
  var numbers type list<int>.
initialization.
  add(numbers, 1).
  for i in numbers.
    var temp type int = 0.
  endfor.
  write(temp).
endprogram.
'''
        with self.assertRaises(RuntimeMintError):
            Interpreter().run(parse_program(source))

    def test_lexer_rejects_invalid_char_literal_early(self):
        source = "program init. initialization. write('AB'). endprogram."
        with self.assertRaises(LexerError):
            Lexer(source).tokenize()

    def test_path_traversal_is_blocked_on_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root.parent / "outside.csv"
            outside.write_text("id;name\n1;x\n", encoding="utf-8")
            source = f'''STRUCT C.
  id type int.
  name type string.
ENDSTRUCT.

program init.
  var data type list<C>.
initialization.
  load "../{outside.name}" into data.
endprogram.
'''
            old = Path.cwd()
            try:
                import os
                os.chdir(root)
                with self.assertRaises(RuntimeMintError):
                    Interpreter().run(parse_program(source))
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main()
