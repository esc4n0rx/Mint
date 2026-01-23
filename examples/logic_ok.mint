program init.
  var num type int = 15.
  var ok type bool = true.
  var enabled type bool = false.
  var role type string = "admin".
initialization.
  if ok and not enabled.
    write("go").
  endif.

  if (num > 10) and (num < 20).
    write("intervalo").
  endif.

  if (role == "admin") or (role == "mod").
    write("acesso").
  endif.
endprogram.
