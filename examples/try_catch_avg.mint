program init.
  STRUCT Product.
    price type float.
  ENDSTRUCT.

  var products type table<Product>.
initialization.
  TRY.
    write(avg(products.price)).
  CATCH.
    write("cannot calculate average").
  ENDTRY.
endprogram.
