program init.
initialization.
  TRY.
    DB CREATE "examples/mintdb/safer_seed_with_try_catch.mintdb".
  CATCH.
    write("DB já existe; seguindo com abertura segura.").
  ENDTRY.

  DB OPEN "examples/mintdb/safer_seed_with_try_catch.mintdb".

  TRY.
    TABLE CREATE clients (id int PRIMARY KEY, name string).
  CATCH.
    write("Tabela já existe; ignorando criação.").
  ENDTRY.

  TRY.
    APPEND INTO clients VALUES (id = 1, name = "Seed protegida").
  CATCH.
    write("Seed já aplicada anteriormente.").
  ENDTRY.
endprogram.
