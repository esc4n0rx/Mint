FUNC create_customer(clients type table<Customer>) RETURNS table<Customer>.
  var candidate type Customer.

  candidate.id = generate_next_id(clients).
  candidate.created_at = now_datetime().
  candidate.updated_at = now_datetime().

  write("Nome:").
  input(candidate.name).
  write("Email:").
  input(candidate.email).
  write("Telefone:").
  input(candidate.phone).
  write("Cidade:").
  input(candidate.city).
  write("Ativo? (true/false):").
  input(candidate.status).
  write("Observacao:").
  input(candidate.notes).

  if (not validate_required(candidate.name)).
    write("Nome e obrigatorio.").
  elseif (not validate_email(candidate.email)).
    write("Email invalido.").
  elseif (not validate_phone(candidate.phone)).
    write("Telefone obrigatorio.").
  elseif (not validate_required(candidate.city)).
    write("Cidade e obrigatoria.").
  elseif (email_already_exists(clients, candidate.email, 0)).
    write("Email ja cadastrado.").
  else.
    insert(clients, candidate).
    save_storage(clients).
    write("Cliente cadastrado com sucesso.").
  endif.

  return clients.
ENDFUNC.

FUNC list_customers(clients type table<Customer>).
  print_title("Lista de clientes").
  if (size(clients) == 0).
    write("Nenhum cliente cadastrado.").
  else.
    FOR customer IN clients.
      write("Cliente:").
      print_customer(customer).
    ENDFOR.
    write("Total listado:").
    write(count(clients)).
  endif.
ENDFUNC.

FUNC search_customers(clients type table<Customer>).
  var option type int.
  var term type string.
  var results type table<Customer>.

  print_title("Busca de clientes").
  write("1 - Buscar por nome exato").
  write("2 - Buscar por email exato").
  write("3 - Listar apenas clientes ativos").
  write("4 - Listar apenas clientes inativos").
  input(option).

  if (option == 1).
    write("Digite o nome:").
    input(term).
    FOR customer IN clients.
      if (customer.name == term).
        insert(results, customer).
      endif.
    ENDFOR.
  elseif (option == 2).
    write("Digite o email:").
    input(term).
    FOR customer IN clients.
      if (customer.email == term).
        insert(results, customer).
      endif.
    ENDFOR.
  elseif (option == 3).
    QUERY FROM clients WHERE status == true INTO results.
  elseif (option == 4).
    QUERY FROM clients WHERE status == false INTO results.
  else.
    write("Opcao invalida.").
  endif.

  if (size(results) == 0).
    write("Nenhum cliente encontrado.").
  else.
    FOR customer IN results.
      write("Resultado:").
      print_customer(customer).
    ENDFOR.
  endif.
ENDFUNC.

FUNC update_customer(clients type table<Customer>) RETURNS table<Customer>.
  var target_id type int.
  var updated type table<Customer>.
  var answer type string.
  var edited type Customer.
  var found type bool = false.

  write("Digite o ID do cliente para editar:").
  input(target_id).

  FOR customer IN clients.
    if (customer.id == target_id).
      found = true.
      edited = customer.
    endif.
  ENDFOR.

  if (found == false).
    write("Cliente nao encontrado.").
    return clients.
  endif.

  write("Dados atuais do cliente:").
  print_customer(edited).

  write("Novo nome:").
  input(answer).
  if (answer != "").
    edited.name = answer.
  endif.

  write("Novo email:").
  input(answer).
  if (answer != "").
    if (email_already_exists(clients, answer, edited.id)).
      write("Email ja em uso por outro cliente.").
      return clients.
    endif.
    edited.email = answer.
  endif.

  write("Novo telefone:").
  input(answer).
  if (answer != "").
    edited.phone = answer.
  endif.

  write("Nova cidade:").
  input(answer).
  if (answer != "").
    edited.city = answer.
  endif.

  write("Alterar status? Digite true, false ou vazio para manter:").
  input(answer).
  if (answer == "true").
    edited.status = true.
  elseif (answer == "false").
    edited.status = false.
  endif.

  write("Nova observacao:").
  input(answer).
  if (answer != "").
    edited.notes = answer.
  endif.

  edited.updated_at = now_datetime().

  FOR customer IN clients.
    if (customer.id == target_id).
      insert(updated, edited).
    else.
      insert(updated, customer).
    endif.
  ENDFOR.

  save_storage(updated).
  write("Cliente atualizado com sucesso.").
  return updated.
ENDFUNC.

FUNC delete_customer(clients type table<Customer>) RETURNS table<Customer>.
  var target_id type int.
  var confirmation type string.
  var filtered type table<Customer>.
  var found type bool = false.

  write("Digite o ID do cliente para remover:").
  input(target_id).

  FOR customer IN clients.
    if (customer.id == target_id).
      found = true.
      write("Cliente localizado:").
      print_customer(customer).
    endif.
  ENDFOR.

  if (found == false).
    write("Cliente nao encontrado.").
    return clients.
  endif.

  write("Confirma remocao? (yes/no)").
  input(confirmation).
  if (confirmation != "yes").
    write("Remocao cancelada.").
    return clients.
  endif.

  FOR customer IN clients.
    if (customer.id != target_id).
      insert(filtered, customer).
    endif.
  ENDFOR.

  save_storage(filtered).
  write("Cliente removido com sucesso.").
  return filtered.
ENDFUNC.

FUNC show_statistics(clients type table<Customer>).
  var active_clients type table<Customer>.
  var inactive_clients type table<Customer>.
  var city_name type string.
  var city_total type int = 0.
  var newest_id type int = 0.
  var newest type table<Customer>.

  print_title("Estatisticas").
  write("Total de clientes:").
  write(count(clients)).

  QUERY FROM clients WHERE status == true INTO active_clients.
  QUERY FROM clients WHERE status == false INTO inactive_clients.

  write("Clientes ativos:").
  write(count(active_clients)).
  write("Clientes inativos:").
  write(count(inactive_clients)).

  if (count(clients) > 0).
    write("Soma dos IDs (sum):").
    write(sum(clients.id)).
    write("Media dos IDs (avg):").
    write(avg(clients.id)).
  endif.

  write("Filtrar clientes por cidade para contagem:").
  input(city_name).
  FOR customer IN clients.
    if (customer.city == city_name).
      city_total = city_total + 1.
    endif.
    if (customer.id > newest_id).
      newest_id = customer.id.
    endif.
  ENDFOR.

  write("Total na cidade informada:").
  write(city_total).

  FOR customer IN clients.
    if (customer.id == newest_id).
      insert(newest, customer).
    endif.
  ENDFOR.

  if (size(newest) > 0).
    write("Cliente mais recente (por ID):").
    print_customer(newest[0]).
  endif.
ENDFUNC.
