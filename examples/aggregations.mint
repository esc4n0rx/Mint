program init.
  STRUCT Product.
    code type string.
    price type float.
  ENDSTRUCT.

  var products type table<Product>.
  var p type Product.
  var total type int.
  var amount type float.
  var average type float.
initialization.
  p.code = "A".
  p.price = 10.0.
  insert(products, p).

  p.code = "B".
  p.price = 20.0.
  insert(products, p).

  total = count(products).
  amount = sum(products.price).
  average = avg(products.price).

  write(total).
  write(amount).
  write(average).
endprogram.
