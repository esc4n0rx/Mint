program init.
initialization.
  DB OPEN "examples/mintdb_beta2/02_example.mintdb".
  UPDATE clients SET name = "Beatriz" WHERE email == "bia@mint.dev".
endprogram.
