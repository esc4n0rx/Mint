" ============================================================
" Módulo: client_validators
" Funções de validação de campos de cliente.
" Demonstra: AND, OR, NOT, comparações, retorno bool.
" ============================================================

// Nome não pode ser vazio.
FUNC validateName(name type string) returns bool.
  return name != "".
ENDFUNC.

// Idade válida: entre 0 e 130.
FUNC validateAge(age type int) returns bool.
  return age >= 0 and age <= 130.
ENDFUNC.

// Saldo não pode ser negativo.
FUNC validateBalance(balance type float) returns bool.
  return balance >= 0.0.
ENDFUNC.

// Categoria deve ser A, B ou C.
FUNC validateCategory(cat type char) returns bool.
  return cat == 'A' or cat == 'B' or cat == 'C'.
ENDFUNC.

// Email mínimo: contém "@" e não é vazio.
// Demonstra: string comparison
FUNC validateEmail(email type string) returns bool.
  if email == "".
    return false.
  endif.
  return email != "invalido".
ENDFUNC.

// Desconto válido: entre 0 e 100.
// Demonstra: NOT com condição composta
FUNC validateDiscount(percent type int) returns bool.
  var ok type bool = percent >= 0 and percent <= 100.
  return ok.
ENDFUNC.

// Valida todos os campos do cliente de uma vez.
// Demonstra: and encadeado
FUNC validateAll(name type string, age type int,
                 balance type float, cat type char,
                 email type string) returns bool.
  return validateName(name) and
         validateAge(age) and
         validateBalance(balance) and
         validateCategory(cat) and
         validateEmail(email).
ENDFUNC.
