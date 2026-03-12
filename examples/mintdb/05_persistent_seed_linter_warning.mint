program init.
initialization.
  DB OPEN "examples/mintdb/demo.mintdb".
  TABLE CREATE clients (id int PRIMARY KEY, name string).
  APPEND INTO clients VALUES (id = 1, name = "Seed fixa 1").
  APPEND INTO clients VALUES (id = 2, name = "Seed fixa 2").
endprogram.
