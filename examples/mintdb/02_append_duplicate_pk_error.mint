program init.
initialization.
  DB CREATE "examples/mintdb/append_duplicate_pk_error.mintdb".
  DB OPEN "examples/mintdb/append_duplicate_pk_error.mintdb".
  TABLE CREATE clients (id int PRIMARY KEY, name string).
  APPEND INTO clients VALUES (id = 1, name = "Ana").
  APPEND INTO clients VALUES (id = 1, name = "Duplicado").
endprogram.
