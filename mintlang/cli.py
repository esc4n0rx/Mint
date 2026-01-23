import sys
from pathlib import Path
from .lexer import Lexer
from .parser import Parser
from .linter import Linter
from .interpreter import Interpreter
from .errors import MintError

def run_file(path: str) -> int:
    p = Path(path)
    if p.suffix != ".mint":
        print("Erro: arquivo de entrada precisa ser .mint")
        return 2

    source = p.read_text(encoding="utf-8")
    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()

        issues = Linter().lint(program)
        if issues:
            print("LintError: encontrei problemas antes de executar:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue.message}")
            return 1

        Interpreter().run(program)
        return 0

    except MintError as e:
        print(f"MintError: {e}")
        return 1

def main():
    if len(sys.argv) != 2:
        print("Uso: python -m mintlang.cli arquivo.mint")
        raise SystemExit(2)
    raise SystemExit(run_file(sys.argv[1]))

if __name__ == "__main__":
    main()
