program init.
  STRUCT Client.
    id type int.
    name type string.
    age type int.
    active type bool.
  ENDSTRUCT.

  var clients type list<Client>.
initialization.
  LOAD "examples/clients.txt" INTO clients.
  write(size(clients)).
  EXPORT clients TO "examples/out_clients.txt".
endprogram.
