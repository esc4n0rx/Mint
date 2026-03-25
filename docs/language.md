# Especificação da Linguagem Mint

## 1) Estrutura de programa

```mint
program init.
  " declarações
initialization.
  " comandos executáveis
endprogram.
```

Também são aceitos, no topo do arquivo, `IMPORT`, `STRUCT` e `FUNC`.

## 2) Tipos

### Primitivos
| Tipo | Default | Observações |
|---|---|---|
| `int` | `0` | inteiro |
| `long` | `0` | inteiro longo |
| `float` | `0.0` | `int -> float` permitido |
| `double` | `0.0` | semelhante a float |
| `decimal` | `0` | usa `Decimal` no runtime |
| `string` | `""` | texto curto |
| `text` | `""` | texto longo |
| `char` | `\0` | exatamente 1 caractere |
| `bool` | `false` | `true/false` |
| `date` | `1970-01-01` | string ISO |
| `time` | `00:00:00` | string ISO |
| `datetime` | `1970-01-01T00:00:00` | string ISO |
| `bytes` | vazio | aceita `bytes` ou `string` |
| `uuid` | gerado no runtime | valida UUID |
| `json` | `{}` | aceita JSON válido |

### Compostos
- `STRUCT Nome. ... ENDSTRUCT.`
- `list<T>`
- `table<T>`

## 3) Comandos da linguagem

> Formato: **Comando**, descrição, sintaxe, retorno/comportamento, erros comuns, exemplo.

### `var`
- **Descrição**: declara variável tipada.
- **Sintaxe**: `var nome type Tipo (= expr).`
- **Retorno/comportamento**: cria símbolo no escopo atual.
- **Erros comuns**: variável duplicada, tipo inexistente.
- **Exemplo**:
```mint
var idade type int = 20.
```

### `write`
- **Descrição**: imprime expressão no stdout.
- **Sintaxe**: `write(expr).`
- **Erros comuns**: expressão inválida.

### `input`
- **Descrição**: lê stdin para variável/campo.
- **Sintaxe**: `input(variavel_ou_campo).`
- **Parâmetros**: `VarRef` ou `FieldAccessExpr`.
- **Erros comuns**: conversão inválida (ex.: string para int).

### `move`
- **Descrição**: move valor de expressão para variável.
- **Sintaxe**: `move expr to destino.`
- **Erros comuns**: destino não declarado/incompatível.

### `add`
- **Descrição**: adiciona item em `list<T>`.
- **Sintaxe**: `add(lista, valor).`

### `insert`
- **Descrição**: adiciona registro em `table<T>` em memória.
- **Sintaxe**: `insert(tabela, registro).`

### `if/elseif/else/endif`
```mint
if cond.
  ...
elseif outra.
  ...
else.
  ...
endif.
```
Condição deve ser `bool`.

### `switch/case/default/endswitch`
```mint
switch expr.
case 1.
  ...
default.
  ...
endswitch.
```
Sem fallthrough.

### `while/endwhile`
```mint
while cond.
  ...
endwhile.
```

### `for/endfor`
```mint
for item in colecao.
  ...
endfor.
```
A coleção deve ser `list<T>` ou `table<T>`.

### `break` / `continue`
- Só dentro de `for`/`while`.

### `try/catch/endtry`
```mint
try.
  ...
catch.
  ...
endtry.
```
Captura erros de runtime Mint.

### Funções
```mint
func soma(a type int, b type int) returns int.
  return a + b.
endfunc.
```
- Chamada em expressão: `var x type int = soma(1,2).`
- Chamada como comando: `soma(1,2).` (se não retornar valor)

### `import`
```mint
import packages.utils.math.
```
- Deve ficar no topo do arquivo.
- Detecta ciclo de import.

### `query`
```mint
query from origem where cond into destino.
```
- Origem/destino devem ter mesmo tipo de coleção de struct.
- `where` deve resultar em `bool`.

### `load/save/export`
```mint
load "dados.csv" into clientes.
save clientes to "out.csv".
export clientes to "out.txt".
```
- Apenas `.csv` (`,`) e `.txt` (`;`).
- Bloqueia path traversal fora do diretório atual.

### Agregações
- `size(colecao)`
- `count(colecao)`
- `sum(colecao)` ou `sum(colecao.campo)`
- `avg(colecao)` ou `avg(colecao.campo)`

## 4) Operadores

- Aritméticos: `+ - * / %`
- Comparação: `== != < > <= >=`
- Lógicos: `and or not`

Regras:
- `/` retorna `float`.
- `%` exige `int`.
- `+` também concatena `string + string`.
- Comparação encadeada é bloqueada no linter.

## 5) Structs, listas e tabelas

```mint
struct Client.
  id type int.
  name type string.
endstruct.

var clients type table<Client>.
var c type Client.
insert(clients, c).
write(clients[0].name).
```

## 6) Namespace `system`

Somente leitura:
- `system.date`, `system.time`, `system.datetime`
- `system.timestamp`, `system.year`, `system.month`, `system.day`
- `system.weekday`, `system.hour`, `system.minute`, `system.second`

## 7) Regras de casting e compatibilidade

- Compatível: `int -> float`.
- Incompatibilidades geram erro de lint/runtime.
- `char` exige tamanho 1.
- `date/time/datetime` exigem ISO.

## 8) Regras do linter (principais)

- variável/função/struct duplicada;
- tipo inexistente;
- atribuição incompatível;
- `break/continue` fora de loop;
- `return` fora de função;
- comparação encadeada;
- divisão/módulo por zero literal;
- warning para seed persistente não idempotente em MintDB.

## 9) Fluxo de execução

```text
Fonte .mint
  -> Lexer (tokens)
  -> Parser (AST)
  -> ModuleLoader (imports)
  -> Linter (issues)
  -> Interpreter (runtime)
```

## 10) Inconsistências relevantes detectadas

1. `decimal` existe em parser/linter/runtime, mas literal `19.90` nasce como `float`; não há coerção implícita `float -> decimal`.
2. `input` no runtime só converte `string/int/float/bool/char`; outros tipos aceitos pela linguagem não têm parser de input dedicado.
3. `datetime` do `system` usa formato com espaço (`YYYY-MM-DD HH:MM:SS`), diferente do default ISO com `T`.
