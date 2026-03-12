" ============================================================
" Módulo: client_service
" Operações CRUD sobre a coleção em memória table<Client>.
" Demonstra: FOR, INSERT, IF/ELSE, RETURN, table<T>.
" NOTA: QUERY com variável externa não é permitido no WHERE
"       (apenas literais e campos da struct). Por isso,
"       filtragens por parâmetro usam FOR + IF.
" ============================================================

IMPORT examples.mintdb_crud.client_model.
IMPORT examples.mintdb_crud.client_helpers.

// ── Busca clientes por ID ─────────────────────────────────
FUNC findById(clients type table<Client>, targetId type int) returns table<Client>.
  var found type table<Client>.
  for c in clients.
    if c.id == targetId.
      insert(found, c).
    endif.
  endfor.
  return found.
ENDFUNC.

// ── Remove cliente por ID ─────────────────────────────────
FUNC removeById(clients type table<Client>, targetId type int) returns table<Client>.
  var remaining type table<Client>.
  for c in clients.
    if c.id != targetId.
      insert(remaining, c).
    endif.
  endfor.
  return remaining.
ENDFUNC.

// ── Atualiza saldo de um cliente ──────────────────────────
// Demonstra: atribuição de campo em struct dentro de FOR.
FUNC updateBalance(clients type table<Client>, targetId type int, newBal type float) returns table<Client>.
  var updated type table<Client>.
  for c in clients.
    if c.id == targetId.
      c.balance = newBal.
    endif.
    insert(updated, c).
  endfor.
  return updated.
ENDFUNC.

// ── Desativa um cliente ───────────────────────────────────
FUNC deactivate(clients type table<Client>, targetId type int) returns table<Client>.
  var updated type table<Client>.
  for c in clients.
    if c.id == targetId.
      c.active = false.
    endif.
    insert(updated, c).
  endfor.
  return updated.
ENDFUNC.

// ── Lista todos os clientes na tela ──────────────────────
// Demonstra: FOR sobre table<Client>, size(), count(), % (par/impar)
FUNC listAllClients(clients type table<Client>).
  var total type int = size(clients).
  if total == 0.
    write("Nenhum cliente cadastrado.").
    return 0.
  endif.
  write("Total de clientes: " + total).
  var idx type int = 0.
  for c in clients.
    idx = idx + 1.
    printSeparator().
    write("  [" + idx + "/" + total + "]").
    printClient(c).
    // Demonstra % (módulo): destaca IDs pares
    if isEven(c.id).
      write("  (ID par)").
    endif.
  endfor.
  printSeparator().
ENDFUNC.

// ── Busca e exibe cliente por nome (busca parcial exata) ──
// Demonstra: FOR + string comparison
FUNC findByName(clients type table<Client>, searchName type string).
  var found type bool = false.
  for c in clients.
    if c.name == searchName.
      printSeparator().
      printClient(c).
      found = true.
    endif.
  endfor.
  if not found.
    write("Nenhum cliente encontrado com nome: " + searchName).
  endif.
ENDFUNC.
