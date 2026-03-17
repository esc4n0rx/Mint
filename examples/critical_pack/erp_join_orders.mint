program init.
  var result type table<string>.
initialization.
  SELECT c.id, c.name, o.total FROM clients c JOIN orders o ON c.id == o.client_id INTO result.
endprogram.
