IMPORT finance.tax.

FUNC calculateTax(value type float) RETURNS float.
  RETURN value.
ENDFUNC.

program init.
  var v type float = 10.0.
initialization.
  write(calculateTax(v)).
endprogram.
