FUNC data_path() RETURNS string.
  return "examples/customer_crud/data/clients.csv".
ENDFUNC.

FUNC ensure_storage(clients type table<Customer>) RETURNS table<Customer>.
  TRY.
    LOAD "examples/customer_crud/data/clients.csv" INTO clients.
  CATCH.
    write("Arquivo CSV nao encontrado. Criando base inicial...").
    TRY.
      SAVE clients TO "examples/customer_crud/data/clients.csv".
    CATCH.
      write("Falha ao criar arquivo inicial de clientes.").
    ENDTRY.
  ENDTRY.
  return clients.
ENDFUNC.

FUNC save_storage(clients type table<Customer>).
  TRY.
    SAVE clients TO "examples/customer_crud/data/clients.csv".
    write("Dados persistidos em CSV com sucesso.").
  CATCH.
    write("Falha ao salvar CSV de clientes.").
  ENDTRY.
ENDFUNC.
