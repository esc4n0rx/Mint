program init.
initialization.
  DB OPEN "examples/mintdb_beta2/02_example.mintdb".
  DELETE FROM clients WHERE email == "ana@mint.dev".
endprogram.
