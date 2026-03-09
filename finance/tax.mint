FUNC calculateTax(value type float) RETURNS float.
  RETURN value * 0.15.
ENDFUNC.

FUNC applyDiscount(value type float, percent type float) RETURNS float.
  RETURN value - (value * percent / 100.0).
ENDFUNC.
