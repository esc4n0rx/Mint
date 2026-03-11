# Customer CRUD (exemplo oficial Mint)

Este exemplo demonstra um programa completo em Mint para cadastro de clientes no terminal, com persistência em CSV.

## Objetivo

Mostrar, em um único projeto didático, o uso combinado de:
- imports entre múltiplos arquivos
- organização modular por responsabilidade
- CRUD completo
- leitura/escrita de CSV
- `QUERY`
- agregações (`count`, `sum`, `avg`)
- `TRY/CATCH`
- variáveis sistêmicas (`system.datetime`)
- loops com menu interativo

## Estrutura

```text
examples/customer_crud/
  main.mint
  menu.mint
  customer_model.mint
  customer_service.mint
  customer_repository.mint
  customer_validators.mint
  helpers.mint
  data/
    clients.csv
```

## Como executar

A partir da raiz do projeto:

```bash
./run.sh -file examples/customer_crud/main.mint
```

## Fluxos implementados

1. Cadastrar cliente
2. Listar clientes
3. Buscar cliente (nome/email/status)
4. Editar cliente
5. Remover cliente com confirmação
6. Mostrar estatísticas
7. Salvar dados manualmente
8. Sair

## Persistência

- Arquivo utilizado: `examples/customer_crud/data/clients.csv`
- Se o arquivo não existir, o exemplo tenta criar automaticamente.
- Após create/update/delete, os dados são salvos em CSV.

## Observações didáticas

- O schema do CSV segue os campos da `STRUCT Customer`:
  - `id,name,email,phone,city,status,created_at,updated_at,notes`
- IDs são gerados de forma incremental (`generate_next_id`).
- A validação cobre obrigatoriedade básica e duplicidade de email.

## Melhorias futuras sugeridas

- validação mais robusta de email/telefone
- paginação de listagem
- relatórios adicionais por período (`system.date`)
- exportação para `.txt` de relatórios
