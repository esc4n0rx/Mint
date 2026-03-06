# Mint Language – Task Log

Registro consolidado das funcionalidades implementadas.

## 2026-01-21 — MVP do núcleo
- Lexer, parser, AST, linter e interpreter iniciais.
- Estrutura obrigatória `program init.` / `initialization.` / `endprogram.`
- Tipos iniciais e `write(...)`.
- Extensão VS Code com suporte a `.mint`.

## 2026-01-21 — Tipos `float` e `char`
- Literais de float e char.
- Validação semântica para char com 1 caractere.
- Regras de tipo propagadas no linter/interpreter.

## 2026-01-22 — Controle de fluxo
- `if/elseif/else/endif`.
- `while/endwhile`.
- Operadores lógicos `and/or/not` com short-circuit.

## 2026-03-06 — Regras semânticas
- Comparação encadeada bloqueada no linter.
- Widening seguro `int -> float` em atribuições/inicializações.

## 2026-03-06 — Funções tipadas
- `func/endfunc`, `returns`, `return`.
- Parâmetros tipados, chamada em expressão e como comando.
- Escopo local por chamada e validações de assinatura/retorno.

## 2026-03-06 — Novas features: `input` e `move`
- Novo comando `input(...)`:
  - Linter exige alvo como variável (`VarRef`) e variável declarada.
  - Runtime lê do terminal e converte de acordo com o tipo alvo (`int`, `float`, `bool`, `char`, `string`).
  - Erros claros de conversão (ex.: `Input inválido para variável 'age': esperado int.`).
- Novo comando `move source to target.`:
  - Aceita literal, variável ou expressão no `source`.
  - `target` deve ser variável existente.
  - Compatibilidade de tipos igual à atribuição (`int -> float` permitido, demais incompatíveis).
- Highlighter do VS Code atualizado para `input`, `move`, `to`.
- Novos exemplos em `examples/` cobrindo casos válidos e inválidos.
