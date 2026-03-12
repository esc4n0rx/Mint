STRUCT Client.
  id type int.
  email type string.
  name type string.
  age type int.
ENDSTRUCT.

program init.
  var out type list<Client>.
  var total type int = 0.
initialization.
  DB CREATE "demo.mintdb".
  DB OPEN "demo.mintdb".
  TABLE CREATE clients (id int PRIMARY KEY, email string, name string, age int).
  INDEX CREATE idx_clients_email ON clients (email).
  APPEND INTO clients VALUES (id = 1, email = "ana@mint.dev", name = "Ana", age = 30).
  SHOW TABLES.
  DESCRIBE clients.
  DB COMPACT.
endprogram.
