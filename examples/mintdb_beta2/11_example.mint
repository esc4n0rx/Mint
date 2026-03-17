program init.
initialization.
  DB OPEN "examples/mintdb_beta2/02_example.mintdb".
  DB COMPACT.
  write("Compactação concluída.").
endprogram.
