# Guia dos exemplos do repositório

Este documento resume os exemplos reais disponíveis e o objetivo de aprendizado de cada grupo.

## 1) Básicos (`examples/*.mint`)

| Arquivo | Demonstra | Objetivo |
|---|---|---|
| `hello.mint`, `HelloWorld.mint` | estrutura mínima | primeiro contato |
| `assignment_ok.mint`, `assignment_type_error.mint` | atribuição tipada | compatibilidade de tipos |
| `if_ok.mint`, `if_error.mint` | condicionais | validar booleanos |
| `while_ok.mint` | laço while | repetição com condição |
| `logic_ok.mint`, `logic_error.mint` | `and/or/not` | regras lógicas |
| `input_move_ok.mint`, `input_*error.mint`, `move_type_error.mint` | input e move | conversão e erros |
| `struct_ok.mint` | structs e campos | modelagem de dados |
| `list_table_ok.mint` | `list<T>` e `table<T>` | coleções tipadas |
| `query_ok.mint` | `QUERY FROM ... WHERE ... INTO` | filtro em memória |
| `for_numbers.mint`, `for_structs.mint` | `for` | iteração em coleção |
| `aggregations.mint` | `size/count/sum/avg` | agregações |
| `try_catch_load.mint`, `try_catch_avg.mint` | tratamento de erro | resiliência de runtime |
| `load_save_export_ok.mint`, `load_txt_ok.mint` | CSV/TXT | persistência de coleções |
| `system_datetime.mint`, `system_conditions.mint`, `system_assignment.mint` | `system.*` | variáveis sistêmicas |

## 2) Imports e pacotes

| Arquivo | Demonstra |
|---|---|
| `imports_test.mint` | import modular válido |
| `import_duplicate_ok.mint` | deduplicação de carga |
| `import_missing_error.mint` | módulo inexistente |
| `import_cycle_error.mint` | detecção de ciclo |
| `import_position_error.mint` | regra de import no topo |
| `packages/*` | módulos reutilizáveis reais |

## 3) MintDB Beta 1 (`examples/mintdb/`)

| Arquivo | Demonstra |
|---|---|
| `01_valid_unique_pk.mint` | PK válida |
| `02_append_duplicate_pk_error.mint` | erro de PK duplicada |
| `03_append_struct_duplicate_pk_error.mint` | erro com APPEND STRUCT |
| `04_update_pk_collision_error.mint` | colisão de PK no update |
| `05_persistent_seed_linter_warning.mint` | warning de idempotência |
| `06_safer_seed_with_try_catch.mint` | seed mais seguro |
| `mintdb_beta_demo.mint` | fluxo CRUD completo |
| `corruption_detect.mint` | validação de integridade |

## 4) MintDB Beta 2 (`examples/mintdb_beta2/`)

Exemplos `01` a `11` cobrem: índices, `SHOW TABLES`, `DESCRIBE`, `SELECT COUNT(*)`, lock/journal e `DB COMPACT`.

## 5) Pacote crítico (`examples/critical_pack/`)

Demonstra recursos avançados:
- `switch_menu.mint`: `SWITCH/CASE/DEFAULT`
- `control_flow_break_continue.mint`: `BREAK/CONTINUE`
- `transaction_safety.mint`: `BEGIN/COMMIT/ROLLBACK`
- `upsert_products.mint`: `UPSERT`
- `erp_join_orders.mint`: `JOIN`
- `alter_table_migration.mint`: `ALTER TABLE`
- `types_demo.mint`: tipos avançados
- `mini_erp_demo.mint`: fluxo integrado

## 6) Exemplos completos de CRUD

### `examples/customer_crud/`
CRUD modular com CSV, query, agregações e `system.datetime`.

### `examples/mintdb_crud/`
CRUD ERP completo usando praticamente toda a linguagem e MintDB.

## 7) Saída esperada

- Exemplos `*_ok` devem executar sem erros de lint/runtime.
- Exemplos `*_error` devem falhar com mensagem explícita.
- Exemplos de CRUD são interativos e exigem entrada do usuário.
