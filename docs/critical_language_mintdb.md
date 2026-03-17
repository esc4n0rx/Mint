# Mint — Pacote Crítico de Evolução (Linguagem + MintDB)

## Visão geral
Este pacote adiciona controle de fluxo avançado (`BREAK`, `CONTINUE`, `SWITCH/CASE/DEFAULT`), evolução de persistência (`JOIN`, transações, `ALTER TABLE`, `UPSERT`) e novos tipos primitivos para cenários ERP.

## Novos comandos
- `BREAK.`: interrompe o loop atual (`FOR`/`WHILE`).
- `CONTINUE.`: pula para a próxima iteração do loop atual.
- `SWITCH <expr>. ... ENDSWITCH.`: seleção por igualdade, sem fallthrough.
- `DB BEGIN.` / `DB COMMIT.` / `DB ROLLBACK.`: transação explícita.
- `ALTER TABLE ...`: `ADD COLUMN`, `DROP COLUMN`, `RENAME COLUMN`, `RENAME TO`.
- `UPSERT INTO ... VALUES (...)`: insere ou atualiza por chave primária.

## JOIN (MintDB)
Sintaxe suportada:
```mint
SELECT c.id, c.name, o.total
FROM clients c
JOIN orders o ON c.id == o.client_id
INTO result.
```
- Escopo atual: `INNER JOIN`.
- Suporta múltiplos `JOIN` encadeados.
- Colunas com prefixo por alias (`c.id`, `o.total`).

## Novos tipos
| Tipo | Uso principal | Exemplo |
|---|---|---|
| decimal | financeiro com precisão | `var price type decimal = 19.90.` |
| date | data sem horário | `var d type date = "2026-03-17".` |
| datetime | data + hora | `var dt type datetime = "2026-03-17T10:00:00".` |
| time | horário | `var t type time = "10:00:00".` |
| text | texto longo | `var notes type text.` |
| long | inteiro grande | `var doc type long.` |
| double | ponto flutuante técnico | `var lat type double.` |
| bytes | binário simples | `var raw type bytes.` |
| uuid | identificador universal | `var id type uuid.` |
| json | payload flexível | `var meta type json.` |

## Defaults por tipo
- `int/long`: `0`
- `float/double`: `0.0`
- `decimal`: `0`
- `string/text`: `""`
- `bool`: `false`
- `char`: `\0`
- `date`: `1970-01-01`
- `time`: `00:00:00`
- `datetime`: `1970-01-01T00:00:00`
- `bytes`: vazio
- `uuid`: auto-gerado na validação de tipo
- `json`: `{}`

## Compatibilidade e coerção
- `decimal` não aceita coerção silenciosa de `float`.
- `date/time/datetime` exigem formato ISO.
- `uuid` é validado por formato.
- `json` aceita texto JSON válido e estrutura nativa.

## Integração interna
- **Lexer**: novos tokens para controle de fluxo, SQL-like e tipos.
- **Parser/AST**: nós dedicados para `BreakStmt`, `ContinueStmt`, `SwitchStmt`, `JoinClause`, transações, `ALTER`, `UPSERT`.
- **Linter**: guarda semântica para uso de `BREAK/CONTINUE` e validações básicas de `SWITCH`.
- **Interpreter/Runtime**: sinais de fluxo de loop, execução de `SWITCH`, comandos transacionais/DB novos.
- **MintDB**: implementação de `JOIN` interno por nested loop, `UPSERT`, transações simples por backup e rollback, evolução de schema.

## Exemplos ERP
Veja `examples/critical_pack/` para fluxos completos: menu com `SWITCH`, cadastro com `UPSERT`, segurança com transação, e relatório com `JOIN`.

## Limitações conhecidas (v1)
- `JOIN` inicial com foco em `INNER JOIN`.
- Transações sem nested transactions.
- `ALTER TABLE` atualiza schema de forma conservadora; regras avançadas de constraint ficam para evolução futura.
