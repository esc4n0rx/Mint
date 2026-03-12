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
