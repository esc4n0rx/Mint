program init.
  STRUCT Client.
    id type int.
    name type string.
  ENDSTRUCT.

  var clients type table<Client>.
initialization.
  TRY.
    LOAD "missing_clients.csv" INTO clients.
  CATCH.
    write("error loading clients").
  ENDTRY.
endprogram.
