" ============================================================
" Módulo: client_reports
" Relatórios e agregações sobre a coleção de clientes.
" Demonstra: QUERY (com literais), sum(), avg(), count(),
"            size(), FOR, string concatenation.
" ============================================================

IMPORT examples.mintdb_crud.client_model.
IMPORT examples.mintdb_crud.client_helpers.

// ── Relatório geral ───────────────────────────────────────
// Demonstra: count(), sum(collection.field), avg(collection.field)
FUNC showGeneralReport(clients type table<Client>).
  var total type int       = count(clients).
  var totalBal type float  = sum(clients.balance).
  var avgAge type float    = avg(clients.age).

  printTitle("RELATORIO GERAL").
  write("  Total de clientes : " + total).
  write("  Soma dos saldos   : R$ " + totalBal).
  write("  Media de idades   : " + avgAge + " anos").
  printSeparator().
ENDFUNC.

// ── Clientes ativos ───────────────────────────────────────
// Demonstra: QUERY FROM ... WHERE <literal bool> INTO
FUNC reportActives(clients type table<Client>).
  var actives type table<Client>.
  QUERY FROM clients WHERE active == true INTO actives.

  var total type int = size(actives).
  printTitle("CLIENTES ATIVOS (" + total + ")").

  for c in actives.
    write("  " + c.id + " | " + c.name + " | R$ " + c.balance).
  endfor.
  printSeparator().
ENDFUNC.

// ── Clientes inativos ─────────────────────────────────────
// Demonstra: QUERY FROM ... WHERE <literal bool> INTO
FUNC reportInactives(clients type table<Client>).
  var inactives type table<Client>.
  QUERY FROM clients WHERE active == false INTO inactives.

  var total type int = size(inactives).
  printTitle("CLIENTES INATIVOS (" + total + ")").

  for c in inactives.
    write("  " + c.id + " | " + c.name).
  endfor.
  printSeparator().
ENDFUNC.

// ── Clientes Premium (categoria A) ───────────────────────
// Demonstra: QUERY FROM ... WHERE category == 'A' (CharLit)
FUNC reportPremium(clients type table<Client>).
  var premium type table<Client>.
  QUERY FROM clients WHERE category == 'A' INTO premium.

  var total type int = size(premium).
  printTitle("CLIENTES PREMIUM - Cat. A (" + total + ")").

  for c in premium.
    printClient(c).
    printSeparator().
  endfor.
ENDFUNC.

// ── Clientes com alto saldo ───────────────────────────────
// Demonstra: QUERY FROM ... WHERE balance > 1000.0 (FloatLit)
FUNC reportHighBalance(clients type table<Client>).
  var rich type table<Client>.
  QUERY FROM clients WHERE balance > 1000.0 INTO rich.

  var total type int = size(rich).
  printTitle("CLIENTES COM SALDO > R$ 1000 (" + total + ")").

  if total == 0.
    write("  Nenhum cliente encontrado.").
  else.
    var totalBal type float = sum(rich.balance).
    write("  Soma dos saldos: R$ " + totalBal).
    for c in rich.
      write("  " + c.name + " -> R$ " + c.balance).
    endfor.
  endif.
  printSeparator().
ENDFUNC.

// ── Clientes maiores de 30 anos ───────────────────────────
// Demonstra: QUERY FROM ... WHERE age > 30 (IntLit)
FUNC reportOver30(clients type table<Client>).
  var over30 type table<Client>.
  QUERY FROM clients WHERE age > 30 INTO over30.

  var total type int = size(over30).
  printTitle("CLIENTES COM MAIS DE 30 ANOS (" + total + ")").

  for c in over30.
    write("  " + c.name + " (" + c.age + " anos)").
  endfor.
  printSeparator().
ENDFUNC.

// ── Relatório completo (todos os relatórios juntos) ──────
FUNC showFullReport(clients type table<Client>).
  showGeneralReport(clients).
  reportActives(clients).
  reportInactives(clients).
  reportPremium(clients).
  reportHighBalance(clients).
  reportOver30(clients).
ENDFUNC.
