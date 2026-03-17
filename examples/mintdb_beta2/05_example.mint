STRUCT Client.
  id type int.
  email type string.
  name type string.
ENDSTRUCT.

program init.
  var rows type table<Client>.
initialization.
  DB OPEN "examples/mintdb_beta2/02_example.mintdb".
  SELECT * FROM clients WHERE email == "bia@mint.dev" INTO rows.
  write(size(rows)).
endprogram.
