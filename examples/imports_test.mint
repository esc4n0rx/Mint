IMPORT utils.math.
IMPORT finance.tax.
IMPORT health.imc.
IMPORT sales.customer.

program init.
  var total type float = 100.0.
  var discounted type float.
  var tax type float.
  var imc type float.
  var customer type Customer.
initialization.
  discounted = applyDiscount(total, 10.0).
  tax = calculateTax(discounted).
  imc = calculateImc(80.0, 1.80).

  customer.id = 1.
  customer.name = "Paulo".
  customer.age = 25.
  customer.active = true.

  write(discounted).
  write(tax).
  write(imc).
  write(square(imc)).
  write(customer.name).

  if isObese(imc).
    write("obese").
  else.
    write("ok").
  endif.
endprogram.
