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

## 2026-03-06 — CLI de distribuição e instaladores multiplataforma
- CLI agora suporta:
  - `-file/--file` para executar arquivo `.mint`.
  - `-create/--create` para gerar template inicial `.mint`.
  - compatibilidade com modo legado por argumento posicional.
- Instaladores adicionados:
  - `install/install_linux.sh`
  - `install/install_macos.sh`
  - `install/install_windows.bat`
- Scripts de fallback adicionados para execução sem PATH:
  - `run.sh`, `run.command`, `run.bat`
- Exemplo novo: `examples/HelloWorld.mint`.

## 2026-03-09 — Feature `STRUCT`
- Core da linguagem atualizado com suporte a:
  - definição de `STRUCT ... ENDSTRUCT` com campos tipados (`campo type tipo.`);
  - declaração de variável com tipo de struct (`var client type Client.`);
  - acesso a campos com dot notation (`client.name`) em expressões, `write`, `if`, `while`, `input` e funções;
  - atribuição em campos (`client.age = 25.`) com validação de tipo e regra existente de widening `int -> float`.
- Linter atualizado para validar:
  - struct duplicada;
  - campo duplicado na mesma struct;
  - tipo inválido de campo;
  - uso de struct não declarada em variáveis/parâmetros;
  - acesso a campo inexistente;
  - atribuição incompatível em campo.
- Interpreter atualizado para:
  - registrar structs antes da execução;
  - instanciar structs com valores padrão por tipo;
  - permitir leitura/escrita de campos e `input` em campos.
- Highlighter do VS Code atualizado em `vscode-mint/syntaxes/mint.tmLanguage.json` para destacar `STRUCT`, `ENDSTRUCT` e acessos com `.`.
- Exemplo adicionado: `examples/struct_ok.mint`.

## 2026-03-09 — Feature: LIST e TABLE
- Resumo: Implementação de coleções tipadas para armazenar múltiplos registros.
- Core da linguagem atualizado com suporte a:
  - tipos genéricos `list<T>` e `table<T>` no parser/linter/interpreter;
  - comandos `add(lista, valor)` e `insert(tabela, registro)`;
  - acesso por índice `colecao[indice]` com validação de tipo e erro de limite;
  - função builtin `size(colecao)` para `list` e `table`;
  - leitura de campos em registros indexados (ex.: `clients[0].name`).
- Highlighter do VS Code atualizado para `list`, `table`, `add`, `insert`, `size` e destaque de `<` `>` `[` `]`.
- Exemplo adicionado: `examples/list_table_ok.mint`.
