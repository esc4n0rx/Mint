program init.
initialization.
  DB CREATE "examples/mintdb/valid_unique_pk.mintdb".
  DB OPEN "examples/mintdb/valid_unique_pk.mintdb".
  TABLE CREATE clients (id int PRIMARY KEY, name string).
  APPEND INTO clients VALUES (id = 1, name = "Ana").
  APPEND INTO clients VALUES (id = 2, name = "Lia").
endprogram.
