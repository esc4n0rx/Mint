# Mint Clipper IDE (PyQt5)

Interface em estilo **Clipper** (fundo preto + texto branco grande) para edição e execução da linguagem Mint integrada ao core (`lexer/parser/linter/interpreter`).

## Requisitos

- Python 3.10+
- PyQt5

Instalação de dependência:

```bash
pip install PyQt5
```

## Executar

Na raiz do projeto:

```bash
python ui/clipper_ide.py
```

## Comandos no terminal da IDE

- `help`
- `new <arquivo.mint>`
- `open <arquivo.mint>`
- `save [arquivo.mint]`
- `run [arquivo.mint]`
- `lint [arquivo.mint]`
- `compile [arquivo.mint]` (alias para `lint`)
- `check`
- `pwd`, `cd <dir>`, `ls [dir]`
- `clear`, `exit`

## Integração com o core

- `run`: usa `ModuleLoader` + `Linter` + `Interpreter`.
- `lint/compile`: usa `ModuleLoader` + `Linter`.

Sem subprocess para execução da linguagem: a execução ocorre diretamente no runtime do Mint.

Alternativas úteis:

```bash
# executando da raiz do projeto
python -m ui.clipper_ide

# executando por caminho absoluto (o script ajusta o sys.path automaticamente)
python C:/Users/paulo/Mint/ui/clipper_ide.py
```

## Erro comum

Se aparecer `ModuleNotFoundError: No module named 'mintlang'`, atualize para esta versão do arquivo `ui/clipper_ide.py` (ela injeta a raiz do repositório no `sys.path` automaticamente).
