program init.
  var price type decimal = 19.90.
  var birthDate type date = "1990-01-01".
  var createdAt type datetime = "2026-03-17T10:00:00".
  var startTime type time = "09:00:00".
  var notes type text = "observação longa".
  var documentNumber type long = 123456789.
  var latitude type double = -23.55052.
  var raw type bytes.
  var id type uuid.
  var meta type json = "{\"env\":\"prod\"}".
initialization.
  write(id).
endprogram.
