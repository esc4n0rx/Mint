program init.
  var nums type list<int>.
initialization.
  FOR n IN nums.
    IF n == 5.
      CONTINUE.
    ENDIF.
    IF n == 10.
      BREAK.
    ENDIF.
    write(n).
  ENDFOR.
endprogram.
