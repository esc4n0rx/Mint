program init.
  STRUCT Client.
    id type int.
    name type string.
    age type int.
  ENDSTRUCT.

  var clients type table<Client>.
  var c type Client.
initialization.
  c.id = 1.
  c.name = "Paulo".
  c.age = 25.
  insert(clients, c).

  FOR client IN clients.
    write(client.name).
    write(client.age).
  ENDFOR.
endprogram.
