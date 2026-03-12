program init.
initialization.
  DB CREATE "examples/mintdb/update_pk_collision_error.mintdb".
  DB OPEN "examples/mintdb/update_pk_collision_error.mintdb".
  TABLE CREATE clients (id int PRIMARY KEY, name string).
  APPEND INTO clients VALUES (id = 1, name = "Ana").
  APPEND INTO clients VALUES (id = 2, name = "Lia").
  UPDATE clients SET id = 2 WHERE id == 1.
endprogram.
