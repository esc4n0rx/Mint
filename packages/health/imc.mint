FUNC calculateImc(weight type float, height type float) RETURNS float.
  RETURN weight / (height * height).
ENDFUNC.

FUNC isObese(imc type float) RETURNS bool.
  RETURN imc >= 30.0.
ENDFUNC.
