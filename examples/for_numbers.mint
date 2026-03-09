program init.
  var numbers type list<int>.
initialization.
  add(numbers, 10).
  add(numbers, 20).
  add(numbers, 30).

  FOR n IN numbers.
    write(n).
  ENDFOR.
endprogram.
