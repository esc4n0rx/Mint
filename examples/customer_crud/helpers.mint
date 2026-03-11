FUNC print_title(title type string).
  write("========================================").
  write(title).
  write("========================================").
ENDFUNC.

FUNC now_datetime() RETURNS string.
  return system.datetime.
ENDFUNC.

FUNC print_customer(item type Customer).
  write("ID:").
  write(item.id).
  write("Nome:").
  write(item.name).
  write("Email:").
  write(item.email).
  write("Telefone:").
  write(item.phone).
  write("Cidade:").
  write(item.city).
  if (item.status == true).
    write("Status: ATIVO").
  else.
    write("Status: INATIVO").
  endif.
  write("Criado em:").
  write(item.created_at).
  write("Atualizado em:").
  write(item.updated_at).
  write("Observacao:").
  write(item.notes).
  write("----------------------------------------").
ENDFUNC.

FUNC generate_next_id(clients type table<Customer>) RETURNS int.
  var max_id type int = 0.
  FOR customer IN clients.
    if (customer.id > max_id).
      max_id = customer.id.
    endif.
  ENDFOR.
  return max_id + 1.
ENDFUNC.
