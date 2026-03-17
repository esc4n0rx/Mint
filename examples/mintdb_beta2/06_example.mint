program init.
  var total type int.
initialization.
  DB OPEN "examples/mintdb_beta2/02_example.mintdb".
  SELECT COUNT(*) FROM clients INTO total.
  write(total).
endprogram.
