# Sistema de Query no Mint

## 1) Filosofia

O Mint possui duas trilhas de consulta:

1. **QUERY em memória** (`query from ... where ... into ...`) para `list/table` de structs.
2. **SELECT do MintDB** para dados persistidos em `.mintdb`.

A ideia é manter uma sintaxe declarativa simples, com execução previsível.

## 2) QUERY em memória

## Sintaxe
```mint
query from origem where condicao into destino.
```

## Modelo de execução
- Resolve coleção de origem.
- Para cada item, cria escopo temporário com campos da struct.
- Avalia `where` como booleano.
- Se verdadeiro, anexa item no destino.

## Regras
- origem e destino devem ter **mesmo tipo** (`list<Struct>` ou `table<Struct>`).
- `where` deve retornar `bool`.

## Limitações
- Sem índices: varredura linear.
- Sem projeção de colunas; move item completo.

## 3) SELECT no MintDB

## Sintaxe base
```mint
select * from tabela into destino.
select c.id, c.name from clients c into destino.
select count(*) from clients where id > 0 into total.
```

## JOIN
```mint
select c.id, o.total
from clients c
join orders o on c.id == o.client_id
into destino.
```

## Modelo de performance
- `SELECT` normal: leitura de blocos + reconstrução de estado ativo.
- Lookup por igualdade pode usar índices.
- `JOIN`: nested loop entre conjuntos intermediários.

## 4) Atribuição de resultados

- `QUERY` escreve em coleção destino em memória.
- `SELECT` escreve lista de dicionários no destino.
- `SELECT COUNT(*)` exige destino `int`.

## 5) Filtros

- `WHERE` aceita expressões Mint (`and`, `or`, `not`, comparadores etc.).
- Em `SELECT`, cada linha é avaliada em escopo local de colunas.

## 6) Limitações gerais

1. Sem `ORDER BY`, `GROUP BY`, `LIMIT`.
2. Sem projeção/transformação no `QUERY` em memória.
3. JOIN sem otimizador de plano.
