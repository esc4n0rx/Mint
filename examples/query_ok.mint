program init.
  STRUCT Client.
    id type int.
    name type string.
    age type int.
    active type bool.
  ENDSTRUCT.

  var clients type table<Client>.
  var adults type table<Client>.
  var c type Client.
initialization.
  c.id = 1.
  c.name = "Ana".
  c.age = 17.
  c.active = true.
  insert(clients, c).

  c.id = 2.
  c.name = "Bruno".
  c.age = 22.
  c.active = true.
  insert(clients, c).

  QUERY FROM clients WHERE (age >= 18) AND (active == true) INTO adults.
  write(size(adults)).
  write(adults[0].name).
endprogram.
