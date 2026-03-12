# MintDB Beta

MintDB é o formato nativo `.mintdb` do Mint para persistência com integridade.

## Estrutura do arquivo

- **Header fixo**
  - magic bytes (`MINTDB01`)
  - versão
  - timestamps (criação/última modificação)
  - offset do catálogo
  - offset inicial de dados
  - flags
  - checksum global SHA-256
- **Catálogo reservado (64KB)**
  - tabelas registradas
  - ponteiros de schema/blocos
  - contadores de ativos/removidos
  - metadados para evolução (free blocks)
- **Área de dados (append-only)**
  - schemas serializados
  - blocos de dados encadeados por offset

## Integridade

`DB OPEN` valida:

1. assinatura e versão
2. coerência de offsets
3. checksum global do arquivo
4. checksum por bloco durante leitura

Se houver adulteração manual, a abertura falha com erro de integridade.

## Regras de `DB CREATE` e `DB OPEN`

- `DB CREATE "arquivo.mintdb".` **falha** se o arquivo já existir.
  - Isso evita sobrescrever estado anterior sem intenção explícita.
- `DB OPEN "arquivo.mintdb".` abre banco existente e preserva conteúdo.

## PRIMARY KEY (enforcement real)

Campos marcados com `PRIMARY KEY` são tratados como únicos em runtime:

- `APPEND INTO ... VALUES (...)` bloqueia duplicidade.
- `APPEND STRUCT ... INTO ...` bloqueia duplicidade.
- `UPDATE ... SET ... WHERE ...` bloqueia colisão de chave com outro registro ativo.

### Política de registros removidos

A validação de duplicidade considera apenas **registros ativos**.
Registros tombstoned por `DELETE` não bloqueiam reutilização futura da mesma chave.

## Diferença entre linter e runtime

- **Linter (warning/info)**: alerta fluxo potencialmente inseguro, como seed fixa em banco persistente (`DB OPEN` + `APPEND` com PK literal).
- **Runtime (erro)**: aplica integridade real e interrompe execução em conflito de chave primária.

## Mensagens esperadas (exemplos)

- Violação de chave primária em APPEND/APPEND STRUCT.
- Violação de chave primária em UPDATE por colisão.
- Warning de fluxo não idempotente em seed fixa para banco persistente.

## Boas práticas para scripts idempotentes

- separar script de schema e script de seed
- usar `TRY/CATCH` em fluxos que podem ser reexecutados
- evitar seeds fixas sem proteção
- preparar fluxo para futura evolução com `IF NOT EXISTS` / `UPSERT`

## Comandos beta

- `DB CREATE "arquivo.mintdb".`
- `DB OPEN "arquivo.mintdb".`
- `TABLE CREATE clients (id int PRIMARY KEY, name string, age int).`
- `APPEND INTO clients VALUES (id = 1, name = "Ana", age = 30).`
- `APPEND STRUCT cliente INTO clients.`
- `SELECT * FROM clients INTO out.`
- `SELECT name, age FROM clients WHERE age > 18 INTO out.`
- `UPDATE clients SET age = 31 WHERE id == 1.`
- `DELETE FROM clients WHERE id == 1.`

## Exemplos

Veja `examples/mintdb/` para cenários:

1. inserção válida com PK única
2. falha de APPEND com PK duplicada
3. falha de APPEND STRUCT com PK duplicada
4. falha de UPDATE com colisão de PK
5. warning de linter para seed fixa em banco persistido
6. fluxo mais seguro/idempotente com `TRY/CATCH`

## Limitações da beta

- catálogo com tamanho reservado fixo (64KB)
- sem compactação real ainda (somente tombstone + metadados)
- sem lock/transação

## Evolução natural

- free-list ativa/reclaim
- compaction
- índices
- journal/recovery
- locks/transações simples
