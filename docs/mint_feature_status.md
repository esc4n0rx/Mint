# Mint — Matriz de Suporte de Features (Beta 3)

Legenda de status: `OK` | `Parcial` | `Quebrado` | `Mockado` | `Não usado`

| Comando/Feature | Documentado | Parseado | Executa | Persiste | Teste | Exemplo | Status |
|---|---|---:|---:|---:|---:|---:|---|
| `program/init/initialization/endprogram` | Sim | Sim | Sim | N/A | Sim | Sim | OK |
| `var ... type ... (= expr)` | Sim | Sim | Sim | Memória | Sim | Sim | OK |
| `write(expr)` | Sim | Sim | Sim | N/A | Sim | Sim | OK |
| Atribuição (`x = expr`, `obj.campo = expr`) | Sim | Sim | Sim | Memória | Sim | Sim | OK |
| `move expr to var` | Sim | Sim | Sim | Memória | Sim | Sim | OK |
| `input(target)` | Sim | Sim | Sim | Memória | Parcial | Sim | Parcial |
| `if/elseif/else/endif` | Sim | Sim | Sim | N/A | Sim | Sim | OK |
| `while/endwhile` | Sim | Sim | Sim | N/A | Sim | Sim | OK |
| `for ... in ... endfor` | Sim | Sim | Sim | N/A | Sim | Sim | OK |
| `try/catch/endtry` | Sim | Sim | Sim | N/A | Sim | Sim | OK |
| `func ... returns ... / return` | Sim | Sim | Sim | N/A | Parcial | Sim | Parcial |
| `import` modular | Sim | Sim | Sim | N/A | Parcial | Sim | Parcial |
| `add(list, item)` | Sim | Sim | Sim | Memória | Parcial | Sim | Parcial |
| `insert(table, item)` | Sim | Sim | Sim | Memória | Parcial | Sim | Parcial |
| `query from ... where ... into ...` | Sim | Sim | Sim | Memória | Parcial | Sim | Parcial |
| `load/save/export` CSV/TXT | Sim | Sim | Sim | Disco | Sim | Sim | OK |
| Agregações `size/count/sum/avg` | Sim | Sim | Sim | N/A | Sim | Sim | OK |
| `DB CREATE` | Sim | Sim | Sim | Disco | Sim | Sim | OK |
| `DB OPEN` | Sim | Sim | Sim | Disco | Sim | Sim | OK |
| `TABLE CREATE` | Sim | Sim | Sim | Disco | Sim | Sim | OK |
| `APPEND INTO ... VALUES` | Sim | Sim | Sim | Disco | Sim | Sim | OK |
| `APPEND STRUCT ... INTO ...` | Sim | Sim | Sim | Disco | Sim | Sim | OK |
| `SELECT ... FROM ... (WHERE ...) INTO ...` | Sim | Sim | Sim | Disco→Memória | Sim | Sim | OK |
| `SELECT COUNT(*) ... INTO ...` | Sim | Sim | Sim | Disco→Memória | Sim | Sim | OK |
| `UPDATE ... SET ... WHERE ...` | Sim | Sim | Sim | Disco | Sim | Sim | OK |
| `DELETE FROM ... WHERE ...` | Sim | Sim | Sim | Disco | Sim | Sim | OK |
| `SHOW TABLES (INTO ...)` | Sim | Sim | Sim | Disco→Memória | Sim | Sim | OK |
| `DESCRIBE table (INTO ...)` | Sim | Sim | Sim | Disco→Memória | Sim | Sim | OK |
| `INDEX CREATE ... ON ...` | Sim | Sim | Sim | Disco | Sim | Sim | OK |
| `DB COMPACT` | Sim | Sim | Sim | Disco | Sim | Sim | OK |
| Variáveis `system.*` (read-only) | Sim | Sim | Sim | Runtime | Sim | Sim | OK |

## Observações rápidas
- Situações `Parcial` indicam implementação funcional, porém com cobertura de testes ainda incompleta para variantes e edge-cases.
- Nesta auditoria foram removidos placeholders de exemplos Beta 2 para eliminar status `Mockado` na trilha de banco.
