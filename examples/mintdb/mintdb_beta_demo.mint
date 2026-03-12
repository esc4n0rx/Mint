STRUCT Client.
  id type int.
  name type string.
  age type int.
ENDSTRUCT.

program init.
  var cliente type Client.
  var adultos type list<Client>.
initialization.
  TRY.
    DB CREATE "examples/mintdb/demo.mintdb".
  CATCH.
    write("Banco já existe; reutilizando arquivo.").
  ENDTRY.
  DB OPEN "examples/mintdb/demo.mintdb".

  TRY.
    TABLE CREATE clients (id int PRIMARY KEY, name string, age int).
  CATCH.
    write("Tabela clients já existe.").
  ENDTRY.

  TRY.
    APPEND INTO clients VALUES (id = 1, name = "Paulo", age = 27).
    APPEND INTO clients VALUES (id = 2, name = "Ana", age = 17).
  CATCH.
    write("Seeds fixos já aplicados.").
  ENDTRY.

  cliente.id = 3.
  cliente.name = "Lia".
  cliente.age = 21.
  TRY.
    APPEND STRUCT cliente INTO clients.
  CATCH.
    write("Registro da struct já existe.").
  ENDTRY.

  SELECT * FROM clients WHERE age > 18 INTO adultos.
  write(count(adultos)).

  UPDATE clients SET age = 28 WHERE id == 1.
  DELETE FROM clients WHERE id == 2.
endprogram.
