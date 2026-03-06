import argparse
from pathlib import Path

from .errors import MintError
from .interpreter import Interpreter
from .lexer import Lexer
from .linter import Linter
from .parser import Parser

DEFAULT_TEMPLATE = """program init.
  var message type string = \"Hello, Mint!\".
initialization.
  write(message).
endprogram.
"""


def run_file(path: str) -> int:
    p = Path(path)
    if p.suffix.lower() != ".mint":
        print("Erro: arquivo de entrada precisa ser .mint")
        return 2

    if not p.exists():
        print(f"Erro: arquivo não encontrado: {p}")
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


def create_file(path: str) -> int:
    p = Path(path)
    if p.suffix.lower() != ".mint":
        print("Erro: o arquivo criado precisa ter extensão .mint")
        return 2

    if p.exists():
        print(f"Erro: arquivo já existe: {p}")
        return 2

    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(DEFAULT_TEMPLATE, encoding="utf-8")
    print(f"Arquivo criado: {p}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mint",
        description="Executa ou cria arquivos da linguagem Mint.",
    )
    parser.add_argument(
        "legacy_file",
        nargs="?",
        help="Compatibilidade: caminho de arquivo .mint para executar.",
    )
    parser.add_argument(
        "-file",
        "--file",
        dest="file",
        help="Caminho do arquivo .mint para executar.",
    )
    parser.add_argument(
        "-create",
        "--create",
        dest="create",
        help="Cria um arquivo .mint com template inicial.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.file and args.create:
        print("Erro: use apenas um modo por vez (-file ou -create).")
        raise SystemExit(2)

    if args.create:
        raise SystemExit(create_file(args.create))

    file_path = args.file or args.legacy_file
    if file_path:
        raise SystemExit(run_file(file_path))

    print("Uso: mint -file arquivo.mint | mint -create novo_arquivo.mint")
    raise SystemExit(2)


if __name__ == "__main__":
    main()
