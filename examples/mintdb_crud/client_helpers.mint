" ============================================================
" Módulo: client_helpers
" Funções auxiliares de formatação e cálculo.
" ============================================================

IMPORT examples.mintdb_crud.client_model.

// ── Linha separadora ──────────────────────────────────────
FUNC printSeparator().
  write("==================================================").
ENDFUNC.

FUNC printTitle(title type string).
  printSeparator().
  write("  " + title).
  printSeparator().
ENDFUNC.

// ── Conversão de bool para texto ─────────────────────────
FUNC boolToText(val type bool) returns string.
  if val.
    return "Sim".
  else.
    return "Nao".
  endif.
ENDFUNC.

// ── Nome legível da categoria ─────────────────────────────
FUNC categoryName(cat type char) returns string.
  if cat == 'A'.
    return "Premium".
  elseif cat == 'B'.
    return "Standard".
  elseif cat == 'C'.
    return "Basico".
  else.
    return "Indefinido".
  endif.
ENDFUNC.

// ── Desconto percentual sobre o saldo ────────────────────
// Demonstra: / (divisão float), * (multiplicação float)
FUNC applyDiscount(balance type float, percent type int) returns float.
  var rate type float = percent / 100.
  var discount type float = balance * rate.
  return balance - discount.
ENDFUNC.

// ── Verifica se um número é par ───────────────────────────
// Demonstra: % (módulo)
FUNC isEven(num type int) returns bool.
  var remainder type int = num % 2.
  return remainder == 0.
ENDFUNC.

// ── Exibe dados completos de um cliente ──────────────────
// Demonstra: string + int, string + float, string + bool,
//            acesso a campos de struct, chamadas de função.
FUNC printClient(c type Client).
  write("  ID       : " + c.id).
  write("  Nome     : " + c.name).
  write("  Email    : " + c.email).
  write("  Idade    : " + c.age + " anos").
  write("  Saldo    : R$ " + c.balance).
  write("  Ativo    : " + boolToText(c.active)).
  write("  Categoria: " + categoryName(c.category)).
ENDFUNC.
