program init.
  STRUCT Client.
    id type int.
    name type string.
    age type int.
    active type bool.
  ENDSTRUCT.

  var clients type table<Client>.
  var adults type table<Client>.
initialization.
  LOAD "examples/clients.csv" INTO clients.
  QUERY FROM clients WHERE age >= 18 INTO adults.
  SAVE clients TO "examples/out_clients.csv".
  EXPORT adults TO "examples/out_adults.txt".
  write(size(clients)).
  write(size(adults)).
endprogram.
