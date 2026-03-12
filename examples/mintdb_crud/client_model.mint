" ============================================================
" Módulo: client_model
" Define a struct Client e a função factory createClient.
" ============================================================

STRUCT Client.
  id       type int.
  name     type string.
  email    type string.
  age      type int.
  balance  type float.
  active   type bool.
  category type char.
ENDSTRUCT.

// Cria uma instância de Client preenchendo todos os campos.
FUNC createClient(cid type int, cname type string, cemail type string,
                  cage type int, cbalance type float,
                  cactive type bool, ccategory type char) returns Client.
  var c type Client.
  c.id       = cid.
  c.name     = cname.
  c.email    = cemail.
  c.age      = cage.
  c.balance  = cbalance.
  c.active   = cactive.
  c.category = ccategory.
  return c.
ENDFUNC.
