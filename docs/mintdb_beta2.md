# MintDB Beta 2

## Visão geral
Beta 2 adiciona índices nativos, `SHOW TABLES`, `DESCRIBE`, `SELECT COUNT(*)`, `DB COMPACT`, file lock, journal/recovery, e validação estrutural aprofundada.

## Novidades
- Índices persistidos por tabela/coluna (incluindo índice automático de PK).
- Executor usa índice em filtros de igualdade (`select_where_equals`) quando compatível.
- `SHOW TABLES` com metadados básicos.
- `DESCRIBE <table>` com colunas, flags e índices.
- `SELECT COUNT(*) FROM ... INTO ...`.
- `DB COMPACT` com rewrite seguro para arquivo temporário + `os.replace` atômico.
- Lock exclusivo por arquivo `<db>.lock` para escrita.
- Journal `<db>.journal` com estados `pending/failed` e bloqueio de abertura insegura.
- Recovery no `DB OPEN` validando journal pendente/corrompido.
- Validação estrutural de offsets, ponteiros, sobreposição de blocos, checksums e consistência de índice.

## Compatibilidade Beta 1
- `DB OPEN` aceita versão 1 e 2.
- Ao escrever em Beta 2, header é atualizado para versão 2.
- Catálogo da versão 1 continua legível (sem índices).

## Limitações
- Índices secundários cobrem igualdade.
- Recovery atual prioriza segurança: bloqueia abertura em journal `pending`/`failed`.

## Roadmap Beta 3
- Índices compostos.
- Planner de query com seleção de custo.
- Recovery com replay/rollback completo por operação.
