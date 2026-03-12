STRUCT Client.
  id type int.
  name type string.
  age type int.
ENDSTRUCT.

program init.
  var cliente type Client.
  var adultos type list<Client>.
initialization.
  DB CREATE "examples/mintdb/demo.mintdb".
  DB OPEN "examples/mintdb/demo.mintdb".

  TABLE CREATE clients (id int PRIMARY KEY, name string, age int).

  APPEND INTO clients VALUES (id = 1, name = "Paulo", age = 27).
  APPEND INTO clients VALUES (id = 2, name = "Ana", age = 17).

  cliente.id = 3.
  cliente.name = "Lia".
  cliente.age = 21.
  APPEND STRUCT cliente INTO clients.

  SELECT * FROM clients WHERE age > 18 INTO adultos.
  write(count(adultos)).

  UPDATE clients SET age = 28 WHERE id == 1.
  DELETE FROM clients WHERE id == 2.
endprogram.
