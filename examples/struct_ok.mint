program init.
  STRUCT Client.
    id type int.
    name type string.
    age type int.
    active type bool.
  ENDSTRUCT.

  var client type Client.
initialization.
  client.id = 1.
  client.name = "Paulo".
  client.age = 25.
  client.active = true.

  write(client.name).

  if isAdult(client).
    write("adult").
  endif.
endprogram.

FUNC isAdult(c type Client) RETURNS bool.
  RETURN c.age >= 18.
ENDFUNC.
