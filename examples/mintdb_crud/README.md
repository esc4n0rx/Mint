# MINT ERP — CRUD de Clientes com MintDB

Programa completo em Mint demonstrando **100% da sintaxe da linguagem** num CRUD
de clientes com persistência nativa via **MintDB**.

## Execução

```bash
# A partir da raiz do projeto Mint:
mint -file examples/mintdb_crud/main.mint
```

## Estrutura modular

| Arquivo | Responsabilidade |
|---|---|
| `client_model.mint` | `STRUCT Client` + factory `createClient()` |
| `client_helpers.mint` | Formatação, cálculo de desconto, `%` módulo |
| `client_validators.mint` | Validações com `AND`, `OR`, `NOT` |
| `client_service.mint` | CRUD em memória com `FOR`, `INSERT`, `IF` |
| `client_reports.mint` | Relatórios com `QUERY`, `sum()`, `avg()`, `count()` |
| `main.mint` | Programa principal com menu completo |

## Funcionalidades do menu

| Opção | Função |
|---|---|
| 1 | Cadastrar cliente (valida todos os campos) |
| 2 | Listar todos os clientes |
| 3 | Buscar por ID |
| 4 | Buscar por nome |
| 5 | Atualizar saldo (com desconto opcional) |
| 6 | Desativar cliente |
| 7 | Remover cliente |
| 8 | Relatórios completos em memória |
| 9 | Consultas no banco MintDB |
| 10 | Salvar/Exportar CSV e TXT |
| 11 | Carregar CSV |
| 12 | Log de eventos da sessão |
| 0 | Sair |

## Sintaxe coberta

### Estrutura
- `IMPORT` — 4 módulos importados em cascata
- `STRUCT / ENDSTRUCT` — struct `Client` com 7 campos
- `FUNC / ENDFUNC / RETURNS / RETURN` — 20+ funções tipadas
- `program init / initialization / endprogram`

### Tipos
- `int`, `float`, `string`, `char`, `bool` — todos os primitivos
- `list<string>` — log de auditoria da sessão
- `table<Client>` — coleção principal em memória

### Controle de fluxo
- `IF / ELSEIF / ELSE / ENDIF`
- `WHILE / ENDWHILE` — loop do menu
- `FOR ... IN ... ENDFOR` — iteração sobre coleções
- `TRY / CATCH / ENDTRY` — tratamento de erros de DB e I/O

### Comandos
- `write()`, `input()`, `move ... to`
- `add()` — `list<string>` de audit log
- `insert()` — `table<Client>` em memória
- `size()`, `count()`, `sum()`, `avg()`
- `QUERY FROM ... WHERE ... INTO` — filtragem em memória
- `SAVE ... TO`, `EXPORT ... TO`, `LOAD ... INTO`

### MintDB
- `DB CREATE` / `DB OPEN`
- `TABLE CREATE` com `PRIMARY KEY AUTO_INCREMENT`
- `INDEX CREATE`
- `SHOW TABLES` / `DESCRIBE`
- `APPEND STRUCT ... INTO` / `APPEND INTO ... VALUES (...)`
- `SELECT * FROM ... INTO` / `SELECT COUNT(*) FROM ... INTO`
- `UPDATE ... SET ... WHERE`
- `DELETE FROM ... WHERE`

### Operadores
- `+` (aritmético e concatenação de string)
- `- * /` (float: `5 / 2 = 2.5`)
- `%` (módulo: `id % 2` para par/ímpar)
- `== != < > <= >=`
- `AND OR NOT`

### Namespace system
- `system.datetime`, `system.date`, `system.time`
- `system.year`, `system.month`, `system.day`, `system.weekday`

## Arquitetura em memória vs banco

```
[Memória (table<Client>)]   [MintDB (clients_db)]
        ↕ sincronizados na criação/atualização/remoção
        ↕ SAVE/LOAD para CSV como backup portátil

Memória: FOR, QUERY, sum, avg — acesso a campos da struct
MintDB : SELECT COUNT, UPDATE, DELETE — consultas estruturadas
```
