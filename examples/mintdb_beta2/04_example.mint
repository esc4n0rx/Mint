program init.
initialization.
  DB OPEN "examples/mintdb_beta2/02_example.mintdb".
  TRY.
    APPEND INTO clients VALUES (id = 1, email = "ana@mint.dev", name = "Ana").
  CATCH.
    write("Seed da Ana já inserida.").
  ENDTRY.

  TRY.
    APPEND INTO clients VALUES (id = 2, email = "bia@mint.dev", name = "Bia").
  CATCH.
    write("Seed da Bia já inserida.").
  ENDTRY.
endprogram.
