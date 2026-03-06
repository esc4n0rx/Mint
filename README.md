![Mint](./logo.png)

# Mint Language

## Visão geral
Mint é uma linguagem interpretada em Python com foco educacional, tipagem forte e sintaxe explícita.

## Recursos atuais
- Estrutura de programa: `program init.` / `initialization.` / `endprogram.`
- Tipos primitivos: `int`, `float`, `string`, `char`, `bool`
- Declaração de variável tipada com inicialização opcional
- Atribuição com validação de tipo (`int -> float` permitido)
- Comando `move source to target.`
- Comando `input(var).` com conversão por tipo da variável
- `write(...)`
- `if / elseif / else / endif`
- `while / endwhile`
- Operadores aritméticos, comparação e lógicos (`and/or/not`)
- Funções com parâmetros tipados e retorno (`func`, `returns`, `return`)
- Linter semântico antes da execução
- Extensão VS Code com syntax highlighting

## Estrutura do repositório
- `mintlang/`: lexer, parser, AST, linter e interpreter
- `examples/`: programas de exemplo
- `vscode-mint/`: extensão de highlight para VS Code
- `task.md`: histórico das features implementadas

## Executar
```bash
python -m mintlang.cli examples/hello.mint
```

## Novos exemplos
- `examples/full_features.mint` (programa completo com funções, input, move, loop, if e tipos)
- `examples/input_move_ok.mint`
- `examples/input_invalid_target_expression.mint`
- `examples/input_unknown_var.mint`
- `examples/move_type_error.mint`
