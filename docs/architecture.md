# Arquitetura técnica do Mint

## 1) Pipeline de execução

```text
Arquivo .mint
   │
   ├─ Lexer (mintlang/lexer.py)
   │    gera tokens com linha/coluna
   │
   ├─ Parser (mintlang/parser.py)
   │    constrói Program + AST de statements/expressions
   │
   ├─ ModuleLoader (mintlang/module_loader.py)
   │    resolve IMPORT, deduplica, detecta ciclo
   │
   ├─ Linter (mintlang/linter.py)
   │    valida semântica/tipos antes de executar
   │
   └─ Interpreter (mintlang/interpreter.py)
        executa memória + integração MintDB
```

## 2) Modelo de tokens

- Enum `TokenType` define operadores, keywords, tipos e controle de fluxo.
- Lexer é case-insensitive para keywords (`text.lower()` no mapa).
- Comentários aceitos:
  - linha iniciada por `"` (quando é primeiro código da linha)
  - `//` inline

## 3) Modelo AST

### Expressões
- Literais (`IntLit`, `FloatLit`, `StringLit`, `CharLit`, `BoolLit`)
- Referências (`VarRef`, `FieldAccessExpr`, `IndexAccessExpr`)
- Operações (`Unary`, `Binary`)
- Chamada (`CallExpr`)
- Builtins (`SizeCall`, `CountExpr`, `SumExpr`, `AvgExpr`)

### Statements
- controle de fluxo, I/O, coleção, função, erro
- comandos MintDB
- comandos de schema e índice

## 4) Execução e memória

- Runtime usa pilha de escopos (`Scope(types, env)`).
- `globals` + escopos locais para funções e laços.
- `for` cria variável de iteração em escopo local por item.
- Struct em runtime é representada por:
```python
{"__struct__": "Nome", "fields": {...}}
```

## 5) Sistema de tipos

- Linter faz inferência estática e compatibilidade.
- Runtime reforça com `_ensure_type`.
- Coleções:
  - `list<T>`: array tipado
  - `table<T>`: array tipado com semântica de tabela em memória

## 6) Integração com MintDB

Interpreter despacha comandos DB para `MintDB`:
- criação/abertura/compactação
- CRUD
- índice
- transação
- introspecção de schema

## 7) MintDB internamente

```text
Header (assinatura + versão + checksum)
Catálogo (tabelas, schemas, índices)
Blocos append-only encadeados
```

- Lock por `.lock`.
- Journal por `.journal`.
- Tombstones para update/delete.
- Rebuild de índices após mutações relevantes.

## 8) Linter e regras arquiteturais

O linter atua como gate obrigatório:
- invalida execução quando há `error`
- também emite `warning/info` (ex.: seed não idempotente)

## 9) Sistema de pacotes/imports

- `IMPORT a.b.c.` resolve `a/b/c.mint` relativo ao diretório atual.
- Loader mantém ordem topológica de dependências.
- colisões de função/struct após merge viram issue.

## 10) Ferramentas de ecossistema

- CLI em `mintlang/cli.py` (`-file`, `-create`, modo legado).
- VS Code extension em `vscode-mint/` (highlight/syntax).
- Pasta `ide/` não está presente no snapshot atual (apesar de menções em documentos históricos).
