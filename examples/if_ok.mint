program init.
  var num type int = 8.
  var ok type bool = true.
  var letter type char = 'A'.
initialization.
  if num > 10.
    write("maior que 10").
  elseif num == 10.
    write("igual a 10").
  else.
    write("menor que 10").
  endif.

  if ok == true.
    write("ativo").
  endif.

  if letter < "B".
    write("antes de B").
  endif.
endprogram.
