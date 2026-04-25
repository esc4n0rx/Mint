![Mint](./logo.png)

# Mint

Mint é uma linguagem interpretada, tipada e orientada a aprendizado de compiladores/interpretação. O projeto combina um runtime em Python, um linter semântico, um parser completo com AST e um mecanismo de persistência próprio (`.mintdb`).

## Visão geral

### O que é o Mint
Mint é uma linguagem didática com sintaxe explícita (blocos terminados por `.`), tipagem declarativa (`var x type int.`) e execução em pipeline:

1. **Lexer** (tokenização)
2. **Parser** (AST)
3. **Linter** (validação estática)
4. **Interpreter** (execução)

### Por que o Mint existe
- Ensinar arquitetura real de linguagem.
- Expor regras de tipos e erros de forma previsível.
- Demonstrar integração linguagem + banco de dados nativo.

## Conceitos centrais

- **Estrutura de programa** com `program init.` / `initialization.` / `endprogram.`
- **Tipos primitivos e avançados** (`int`, `float`, `decimal`, `uuid`, `json` etc.)
- **Coleções** `list<T>` e `table<T>`
- **Structs** para modelagem de dados
- **MintDB** para persistência nativa com integridade, lock e journal
- **Linter obrigatório** antes da execução

## Filosofia de linguagem

- Sintaxe clara e uniforme.
- Regras explícitas de tipo e conversão.
- Erros semânticos/execução com mensagens diretas.
- Recursos modernos sem “mágica” oculta.

## Recursos implementados

### Linguagem
- Variáveis tipadas, atribuição e `move`
- `input`, `write`
- `if/elseif/else`, `while`, `for`, `switch/case/default`
- `break`, `continue`, `try/catch`
- Funções tipadas (`func`, `returns`, `return`)
- `import` modular com detecção de ciclo
- Structs, listas e tabelas em memória
- `query from ... where ... into ...`
- `size`, `count`, `sum`, `avg`
- `load/save/export` (`.csv` e `.txt`)
- Namespace `system.*` (somente leitura)

### MintDB
- `DB CREATE`, `DB OPEN`, `DB COMPACT`
- `DB BEGIN`, `DB COMMIT`, `DB ROLLBACK`
- `TABLE CREATE`, `INDEX CREATE`
- `APPEND`, `APPEND STRUCT`, `UPSERT`
- `SELECT`, `SELECT COUNT(*)`, `JOIN`
- `UPDATE`, `DELETE`
- `SHOW TABLES`, `DESCRIBE`

## Instalação

Pré-requisito: Python 3.10+.

### Linux
```bash
./install/install_linux.sh
```

### macOS
```bash
./install/install_macos.sh
```

### Windows
```bat
install\install_windows.bat
```

## Como executar

### Executar arquivo Mint
```bash
mint -file examples/hello.mint
```

### Fallback sem launcher no PATH
```bash
./run.sh -file examples/hello.mint
```

### Criar template de arquivo
```bash
mint -create MeuPrograma.mint
```

## Exemplo mínimo

```mint
program init.
  var nome type string = "Mint".
initialization.
  write("Olá, " + nome).
endprogram.
```

## Estrutura do repositório

- `mintlang/`: núcleo da linguagem (lexer, parser, AST, linter, interpreter, MintDB)
- `examples/`: exemplos da linguagem, CRUDs e cenários MintDB
- `packages/`: módulos reutilizáveis para `import`
- `docs/`: documentação técnica e de referência
- `tests/`: testes de linguagem e MintDB
- `vscode-mint/`: gramática e configuração da extensão VS Code
- `install/`: instaladores e launchers

## Visão do engine MintDB

- Arquivo binário com header + catálogo + blocos de dados.
- Operações de escrita protegidas por lock exclusivo.
- Journal para detectar operações interrompidas.
- Integridade via checksum global e checksum por bloco.

## IDE e tooling

- **Presente no repositório**: extensão VS Code (`vscode-mint`) para highlight.
- **Disponível**: pasta `ui/` com IDE PyQt5 em estilo Clipper (`python ui/clipper_ide.py`).

## Roadmap técnico sugerido

- Cobertura de testes de smoke para **todos** os exemplos.
- Documentação gerada automaticamente a partir do parser/tokens.
- Evolução de transações e otimização de `JOIN`/queries.
- Integração de diagnósticos em editor além de highlight.

## Contribuição

1. Abra issue com contexto técnico e exemplo mínimo.
2. Proponha alteração incremental (evitar refatorações amplas sem necessidade).
3. Inclua testes e atualização de docs para cada feature.
4. Registre a evolução em `task.md`.
