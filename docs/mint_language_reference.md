# Mint Language Reference (Beta 3)

## 1. Introdução
Mint é uma linguagem interpretada com foco educacional: sintaxe explícita, tipagem estática e runtime previsível.

## 2. Estrutura de programa
```mint
program init.
  var message type string = "Hello".
initialization.
  write(message).
endprogram.
```

## 3. Conceitos base
- `var`: declaração tipada.
- `struct`: tipo composto com campos nomeados.
- `list<T>`: coleção ordenada em memória.
- `table<T>`: coleção semântica de registros (em memória e/ou via MintDB).

## 4. Tipos
Primitivos: `int`, `float`, `string`, `char`, `bool`.
Compostos: `Struct`, `list<T>`, `table<T>`.

## 5. Referência de comandos

## `var`
**Descrição**: declara variável tipada.
**Sintaxe**: `var nome type Tipo (= expr).`
**Parâmetros**: nome, tipo, inicializador opcional.
**Regras**: nome único no escopo; coerção `int -> float` permitida.
**Fluxo interno**: parser gera `VarDeclStmt`; runtime registra tipo e valor default/inicial.
**Exemplo simples**: `var idade type int = 10.`
**Exemplo avançado**: `var rows type table<Client>.`
**Inválidos**: `var x type unknown.`
**Boas práticas**: inicializar quando possível.

## `write`
**Descrição**: escreve valor no stdout.
**Sintaxe**: `write(expr).`
**Regras**: aceita qualquer expressão válida.
**Efeito colateral**: I/O de console.

## `input`
**Descrição**: lê stdin e converte para tipo do destino.
**Sintaxe**: `input(var_ou_campo).`
**Regras**: destino deve ser atribuível; falha se conversão inválida.

## `move`
**Descrição**: atribui resultado de expressão a variável alvo.
**Sintaxe**: `move expr to destino.`

## `if/elseif/else`
**Descrição**: controle condicional.
**Sintaxe**:
```mint
if cond.
  ...
elseif cond2.
  ...
else.
  ...
endif.
```
**Regras**: condições devem resultar em `bool`.

## `while`
**Descrição**: repetição enquanto condição booleana for verdadeira.

## `for`
**Descrição**: itera em coleções.
**Sintaxe**:
```mint
FOR item IN colecao.
  ...
ENDFOR.
```

## `try/catch`
**Descrição**: tratamento de erro de runtime.
**Sintaxe**:
```mint
TRY.
  ...
CATCH.
  ...
ENDTRY.
```

## `func` / `return` / chamada
**Descrição**: funções com parâmetros tipados e retorno opcional.

## `import`
**Descrição**: importa módulos Mint por namespace (`IMPORT pacote.modulo.`).

## `add` e `insert`
- `add(lista, valor).`
- `insert(tabela_memoria, registro).`

## `query`
**Descrição**: filtro em coleção de structs em memória.
**Sintaxe**: `QUERY FROM origem WHERE cond INTO destino.`

## `load/save/export`
- `LOAD "arquivo.csv" INTO colecao.`
- `SAVE colecao TO "arquivo.csv".`
- `EXPORT colecao TO "arquivo.txt".`

Regras:
- formatos suportados: `.csv` e `.txt`;
- sandbox de path: bloqueia traversal fora do diretório atual;
- cabeçalho deve casar com campos da struct.

## Agregações
- `size(colecao)`
- `count(colecao)`
- `sum(expr|colecao)`
- `avg(expr|colecao)`

## 6. MintDB (persistência)

### `DB CREATE`
Cria arquivo `.mintdb`; falha se já existir.

### `DB OPEN`
Abre banco existente com lock exclusivo.

### `TABLE CREATE`
Cria tabela com schema, `PRIMARY KEY` e `AUTO_INCREMENT`.

### `APPEND`
- `APPEND INTO tabela VALUES (col = expr, ...).`
- `APPEND STRUCT variavelStruct INTO tabela.`

### `SELECT`
- `SELECT * FROM tabela INTO destino.`
- `SELECT col1, col2 FROM tabela WHERE cond INTO destino.`
- `SELECT COUNT(*) FROM tabela (WHERE cond) INTO total.`

### `UPDATE`
`UPDATE tabela SET campo = expr [, ...] WHERE cond.`

### `DELETE`
`DELETE FROM tabela WHERE cond.`

### `SHOW TABLES`
`SHOW TABLES.` ou `SHOW TABLES INTO destino.`

### `DESCRIBE`
`DESCRIBE tabela.` ou `DESCRIBE tabela INTO destino.`

### `INDEX CREATE`
`INDEX CREATE nome ON tabela (coluna).`

### `DB COMPACT`
Reescreve arquivo removendo tombstones e mantendo estado ativo.

## 7. Variáveis de sistema
Namespace somente leitura `system.*` com dados de execução (por exemplo data/hora).

## 8. Execução de programas
- `mint -file arquivo.mint`
- `./run.sh -file arquivo.mint`

## 9. Arquitetura (alto nível)
1. Lexer tokeniza.
2. Parser constrói AST.
3. Linter valida semanticamente.
4. Interpreter executa nós e integra MintDB.

## 10. Boas práticas gerais
- sempre validar fluxo idempotente ao semear dados em DB (`TRY/CATCH`);
- preferir exemplos modulares com `import`;
- manter tipos explícitos e condições booleanas claras.
