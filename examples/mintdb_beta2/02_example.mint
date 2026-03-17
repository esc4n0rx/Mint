STRUCT Client.
  id type int.
  email type string.
  name type string.
ENDSTRUCT.

program init.
initialization.
  TRY.
    DB CREATE "examples/mintdb_beta2/02_example.mintdb".
  CATCH.
    write("DB já existe, seguindo.").
  ENDTRY.

  DB OPEN "examples/mintdb_beta2/02_example.mintdb".

  TRY.
    TABLE CREATE clients (id int PRIMARY KEY, email string, name string).
  CATCH.
    write("Tabela clients já existe.").
  ENDTRY.
endprogram.
