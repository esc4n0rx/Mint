# MintDB: documentação técnica

## 1) Visão geral

MintDB é o mecanismo nativo de persistência do Mint com arquivo binário `.mintdb`, catálogo embutido, blocos append-only e validações de integridade.

## 2) Estrutura do arquivo

```text
[HEADER FIXO]
[CATÁLOGO RESERVADO (64KB)]
[BLOCOS DE DADOS ENCADEADOS]
```

- Header com `magic`, versão, offsets e checksum global.
- Catálogo serializado em JSON (tabelas, schemas, índices).
- Blocos com header próprio + checksum por bloco.

## 3) Comandos suportados

### `DB CREATE "arquivo.mintdb".`
Cria banco novo. Falha se arquivo já existir.

### `DB OPEN "arquivo.mintdb".`
Abre banco existente, aplica lock exclusivo e valida integridade.

### `DB COMPACT.`
Reescreve o banco em arquivo temporário contendo apenas estado ativo (sem tombstones antigos) e faz troca atômica.

### `DB BEGIN.` / `DB COMMIT.` / `DB ROLLBACK.`
Transação simples por backup (`.txbak`) e restauração.

### `TABLE CREATE nome (col tipo [PRIMARY KEY] [AUTO_INCREMENT], ...).`
Cria tabela com schema persistido no catálogo.

### `INDEX CREATE idx ON tabela (coluna).`
Cria índice persistido para lookup de igualdade.

### `APPEND INTO tabela VALUES (col = expr, ...).`
Insere registro.

### `APPEND STRUCT varStruct INTO tabela.`
Insere registro a partir de struct em memória.

### `UPSERT INTO tabela VALUES (...).`
Atualiza por chave primária existente ou insere novo.

### `SELECT ... FROM ... [JOIN ...] [WHERE ...] INTO destino.`
Consulta dados para memória.

### `SELECT COUNT(*) FROM tabela [WHERE ...] INTO total.`
Conta registros.

### `UPDATE tabela SET col = expr [, ...] WHERE cond.`
Update versionado: grava novo + tombstone do antigo.

### `DELETE FROM tabela WHERE cond.`
Delete lógico com tombstone.

### `SHOW TABLES [INTO destino].`
Lista tabelas e métricas de registros ativos/removidos.

### `DESCRIBE tabela [INTO destino].`
Retorna schema e índices.

### `ALTER TABLE`
- `ADD COLUMN`
- `DROP COLUMN` (bloqueia remoção de PK)
- `RENAME COLUMN`
- `RENAME TO`

## 4) Modelo de armazenamento

- Escrita append-only em blocos.
- Cada bloco carrega payload de registros JSON.
- `UPDATE`/`DELETE` usam marcação lógica (`__deleted__`).
- Leitura recompõe estado ativo por chave primária.

## 5) Índices

- Índice de PK automático quando tabela possui `PRIMARY KEY`.
- Índices secundários criados por `INDEX CREATE`.
- Lookup por igualdade (`col == valor`) usa mapa persistido no catálogo.

## 6) Reuso de blocos

- Campo `free_blocks` existe no catálogo, mas atualmente não há reuso ativo.
- Estratégia vigente: append + compactação para limpeza.

## 7) Segurança de dados

- Lock por arquivo `.lock` impede dois escritores.
- Journal `.journal` marca operação pendente/falha.
- Checksum global detecta adulteração/corrupção.
- Checksum por bloco detecta bloco corrompido.
- Recovery bloqueia abertura quando journal indica estado inseguro.

## 8) Performance

- `SELECT` geral percorre cadeia de blocos.
- Filtros por coluna indexada reduzem candidatos.
- `JOIN` atual usa nested loop (custo cresce com tamanho dos conjuntos).
- `DB COMPACT` é operação mais pesada, porém melhora leitura futura.

## 9) Limitações conhecidas

1. Sem transações aninhadas.
2. Sem free-list operacional de blocos.
3. Índices voltados para igualdade; sem range scan.
4. `JOIN` sem otimizador (nested loop puro).

## 10) Roadmap técnico sugerido

- Ativar reuso de blocos livres.
- Índices compostos e estratégias de range.
- Planejador simples para `JOIN`.
- Journal com recuperação automática controlada.

## 11) Exemplo real

```mint
program init.
  var rows type table<string>.
initialization.
  db create "data/app.mintdb".
  db open "data/app.mintdb".
  table create clients (id int primary key auto_increment, name string, email string).
  index create idx_clients_email on clients (email).
  append into clients values (name = "Ana", email = "ana@mint.dev").
  select * from clients into rows.
  show tables.
endprogram.
```
