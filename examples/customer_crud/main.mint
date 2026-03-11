IMPORT examples.customer_crud.customer_model.
IMPORT examples.customer_crud.helpers.
IMPORT examples.customer_crud.customer_validators.
IMPORT examples.customer_crud.customer_repository.
IMPORT examples.customer_crud.customer_service.
IMPORT examples.customer_crud.menu.

program init.
  var clients type table<Customer>.
initialization.
  print_title("Inicializando base de clientes").
  clients = ensure_storage(clients).
  run_main_menu(clients).
endprogram.
