program init.
  var menu type int = 1.
  var report type table<string>.
initialization.
  DB BEGIN.
  UPSERT INTO clients VALUES (id = 1, name = "Paulo").
  UPSERT INTO orders VALUES (id = 1, client_id = 1, total = 100.00).
  DB COMMIT.

  SWITCH menu.
  CASE 1.
    SELECT c.id, c.name, o.total FROM clients c JOIN orders o ON c.id == o.client_id INTO report.
  DEFAULT.
    write("Sem ação").
  ENDSWITCH.
endprogram.
