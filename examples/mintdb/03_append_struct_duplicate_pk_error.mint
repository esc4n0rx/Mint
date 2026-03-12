STRUCT Client.
  id type int.
  name type string.
ENDSTRUCT.

program init.
  var c type Client.
initialization.
  DB CREATE "examples/mintdb/append_struct_duplicate_pk_error.mintdb".
  DB OPEN "examples/mintdb/append_struct_duplicate_pk_error.mintdb".
  TABLE CREATE clients (id int PRIMARY KEY, name string).
  c.id = 1.
  c.name = "Ana".
  APPEND STRUCT c INTO clients.
  APPEND STRUCT c INTO clients.
endprogram.
