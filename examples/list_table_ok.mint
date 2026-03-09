program init.
  STRUCT Client.
    id type int.
    name type string.
  ENDSTRUCT.

  var numbers type list<int>.
  var clients type table<Client>.
  var c type Client.
  var i type int = 0.
initialization.
  add(numbers, 10).
  add(numbers, 20).

  c.id = 1.
  c.name = "Paulo".
  insert(clients, c).

  write(numbers[1]).
  write(clients[0].name).

  while i < size(clients).
    write(clients[i].name).
    i = i + 1.
  endwhile.
endprogram.
