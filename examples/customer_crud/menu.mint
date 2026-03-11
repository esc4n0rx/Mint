FUNC run_main_menu(clients type table<Customer>). 
  var option type int = -1.

  while option != 0.
    print_title("Sistema de Cadastro de Clientes - Mint").
    write("1 - Cadastrar novo cliente").
    write("2 - Listar clientes").
    write("3 - Buscar cliente").
    write("4 - Editar cliente").
    write("5 - Remover cliente").
    write("6 - Mostrar estatisticas").
    write("7 - Salvar dados").
    write("0 - Sair").
    input(option).

    if option == 1.
      clients = create_customer(clients).
    elseif option == 2.
      list_customers(clients).
    elseif option == 3.
      search_customers(clients).
    elseif option == 4.
      clients = update_customer(clients).
    elseif option == 5.
      clients = delete_customer(clients).
    elseif option == 6.
      show_statistics(clients).
    elseif option == 7.
      save_storage(clients).
    elseif option == 0.
      write("Encerrando sistema...").
    else.
      write("Opcao invalida. Tente novamente.").
    endif.
  endwhile.
ENDFUNC.
