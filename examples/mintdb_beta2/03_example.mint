program init.
initialization.
  DB OPEN "examples/mintdb_beta2/02_example.mintdb".
  TRY.
    INDEX CREATE idx_clients_email ON clients (email).
  CATCH.
    write("Índice já existe ou tabela inválida.").
  ENDTRY.
endprogram.
