" ============================================================
" MINT ERP — CRUD de Clientes com MintDB
" Programa principal: usa 100% da sintaxe da linguagem.
"
" Cobre: IMPORT, STRUCT, FUNC, program/initialization,
"        VAR (todos os tipos), IF/ELSEIF/ELSE, WHILE, FOR,
"        TRY/CATCH, RETURN, WRITE, INPUT, MOVE,
"        ADD, INSERT, SIZE, COUNT, SUM, AVG,
"        QUERY, LOAD, SAVE, EXPORT,
"        DB CREATE/OPEN, TABLE CREATE (PK AUTO_INCREMENT),
"        INDEX CREATE, APPEND INTO VALUES, APPEND STRUCT,
"        SELECT * WHERE, SELECT COUNT(*), UPDATE, DELETE,
"        SHOW TABLES, DESCRIBE,
"        system.datetime, system.date, system.time,
"        system.year, system.month, system.day,
"        operadores: + (string concat), % (módulo),
"        / (divisão float), AND, OR, NOT
" ============================================================

IMPORT examples.mintdb_crud.client_model.
IMPORT examples.mintdb_crud.client_helpers.
IMPORT examples.mintdb_crud.client_validators.
IMPORT examples.mintdb_crud.client_service.
IMPORT examples.mintdb_crud.client_reports.

program init.

  " ── Coleções em memória ─────────────────────────────────
  var clients  type table<Client>.   // tabela principal em memória
  var tempList type table<Client>.   // resultado temporário de buscas
  var auditLog type list<string>.    // log de eventos da sessão (list<T>)

  " ── Controle de fluxo ───────────────────────────────────
  var running    type bool = true.
  var nextId     type int  = 1.
  var option     type int  = 0.

  " ── Buffers de entrada ──────────────────────────────────
  var inputName     type string.
  var inputEmail    type string.
  var inputAge      type int.
  var inputBalance  type float.
  var inputActive   type bool.
  var inputCategory type char.
  var inputId       type int.
  var inputBal      type float.
  var inputDiscount type int.
  var inputConfirm  type bool.
  var inputSearch   type string.

  " ── Auxiliares ──────────────────────────────────────────
  var dbPath   type string = "examples/mintdb_crud/clients.mintdb".
  var csvPath  type string = "examples/mintdb_crud/data/clients.csv".
  var txtPath  type string = "examples/mintdb_crud/data/clients.txt".
  var dbReady  type bool   = false.
  var tmpCount type int.
  var tmpBal   type float.
  var tmpChar  type char.
  var tmpBool  type bool.

initialization.

  " ── Banner de abertura ──────────────────────────────────
  printSeparator().
  write("   MINT ERP — Sistema de Gestao de Clientes").
  write("   Iniciado em : " + system.datetime).
  write("   Data        : " + system.date).
  write("   Hora        : " + system.time).
  write("   Ano/Mes/Dia : " + system.year + "/" + system.month + "/" + system.day).
  printSeparator().

  " ── Setup do banco de dados nativo MintDB ───────────────
  TRY.
    DB CREATE "examples/mintdb_crud/clients.mintdb".

    " Tabela de clientes com PRIMARY KEY AUTO_INCREMENT
    TABLE CREATE clients_db (
      id       int  PRIMARY KEY AUTO_INCREMENT,
      name     string,
      email    string,
      age      int,
      balance  float,
      active   bool,
      category char
    ).

    " Índice no nome para buscas rápidas
    INDEX CREATE idx_name ON clients_db (name).

    " Tabela de auditoria (demonstra AUTO_INCREMENT isolado)
    TABLE CREATE audit_db (
      event_id  int PRIMARY KEY AUTO_INCREMENT,
      event     string,
      ts        string
    ).

    move true to dbReady.
    write("Banco de dados criado com sucesso.").

  CATCH.
    " Se já existe, apenas abre
    TRY.
      DB OPEN "examples/mintdb_crud/clients.mintdb".
      move true to dbReady.
      write("Banco de dados aberto.").
    CATCH.
      write("AVISO: banco de dados indisponivel. Operando apenas em memoria.").
    ENDTRY.
  ENDTRY.

  " Inspeciona estrutura do banco
  if dbReady.
    SHOW TABLES.
    DESCRIBE clients_db.
    DESCRIBE audit_db.
  endif.

  add(auditLog, "Sistema iniciado em " + system.datetime).

  " ── Loop principal do menu ──────────────────────────────
  while running.

    write("").
    printSeparator().
    write("  MENU PRINCIPAL").
    printSeparator().
    write("  1. Cadastrar cliente").
    write("  2. Listar todos").
    write("  3. Buscar por ID").
    write("  4. Buscar por nome").
    write("  5. Atualizar saldo").
    write("  6. Desativar cliente").
    write("  7. Remover cliente").
    write("  8. Relatorios em memoria").
    write("  9. Consultas no banco (MintDB)").
    write(" 10. Salvar / Exportar CSV").
    write(" 11. Carregar CSV").
    write(" 12. Log da sessao").
    write("  0. Sair").
    printSeparator().
    write("Opcao: ").
    input(option).

    " ════════════════════════════════════════════════════
    " 1. CADASTRAR CLIENTE
    " ════════════════════════════════════════════════════
    if option == 1.
      printTitle("NOVO CLIENTE").

      write("Nome  : ").  input(inputName).
      write("Email : ").  input(inputEmail).
      write("Idade : ").  input(inputAge).
      write("Saldo : ").  input(inputBalance).
      write("Ativo (true/false): ").  input(inputActive).
      write("Categoria (A/B/C) : ").  input(inputCategory).

      // Valida todos os campos
      if not validateAll(inputName, inputAge, inputBalance, inputCategory, inputEmail).
        write("ERRO: dados invalidos. Verifique os campos e tente novamente.").
      else.

        // Cria struct em memória
        var newClient type Client = createClient(
          nextId, inputName, inputEmail, inputAge,
          inputBalance, inputActive, inputCategory
        ).

        // Insere na tabela em memória
        insert(clients, newClient).

        // Persiste no MintDB via APPEND STRUCT (id=nextId, não 0 → não dispara auto-increment)
        if dbReady.
          TRY.
            APPEND STRUCT newClient INTO clients_db.
            // Registra evento na auditoria (AUTO_INCREMENT no event_id)
            APPEND INTO audit_db VALUES (
              event = "CREATE: " + inputName,
              ts    = system.datetime
            ).
            write("Persistido no banco com sucesso.").
          CATCH.
            write("Aviso: salvo em memoria, banco nao sincronizado.").
          ENDTRY.
        endif.

        write("Cliente #" + nextId + " cadastrado: " + inputName).
        nextId = nextId + 1.
        add(auditLog, "Criado cliente: " + inputName + " em " + system.time).
      endif.

    " ════════════════════════════════════════════════════
    " 2. LISTAR TODOS
    " ════════════════════════════════════════════════════
    elseif option == 2.
      printTitle("LISTA DE CLIENTES").
      listAllClients(clients).

    " ════════════════════════════════════════════════════
    " 3. BUSCAR POR ID
    " ════════════════════════════════════════════════════
    elseif option == 3.
      printTitle("BUSCAR POR ID").
      write("ID do cliente: ").
      input(inputId).

      tempList = findById(clients, inputId).
      tmpCount = size(tempList).

      if tmpCount == 0.
        write("Cliente #" + inputId + " nao encontrado.").
      else.
        printSeparator().
        printClient(tempList[0]).
        // Demonstra % (par/impar)
        if isEven(inputId).
          write("  Obs: ID par.").
        else.
          write("  Obs: ID impar.").
        endif.
      endif.

    " ════════════════════════════════════════════════════
    " 4. BUSCAR POR NOME
    " ════════════════════════════════════════════════════
    elseif option == 4.
      printTitle("BUSCAR POR NOME").
      write("Nome exato: ").
      input(inputSearch).
      findByName(clients, inputSearch).

    " ════════════════════════════════════════════════════
    " 5. ATUALIZAR SALDO
    " ════════════════════════════════════════════════════
    elseif option == 5.
      printTitle("ATUALIZAR SALDO").
      write("ID do cliente: ").
      input(inputId).

      tempList = findById(clients, inputId).

      if size(tempList) == 0.
        write("Cliente nao encontrado.").
      else.
        var currentClient type Client = tempList[0].
        write("Saldo atual: R$ " + currentClient.balance).
        write("Novo saldo : ").
        input(inputBal).

        write("Desconto % (0 = sem desconto): ").
        input(inputDiscount).

        if not validateDiscount(inputDiscount).
          write("ERRO: desconto invalido (0–100).").
        elseif not validateBalance(inputBal).
          write("ERRO: saldo nao pode ser negativo.").
        else.
          if inputDiscount > 0.
            inputBal = applyDiscount(inputBal, inputDiscount).
            write("Saldo apos desconto: R$ " + inputBal).
          endif.

          clients = updateBalance(clients, inputId, inputBal).

          if dbReady.
            TRY.
              UPDATE clients_db SET balance = inputBal WHERE id == inputId.
              APPEND INTO audit_db VALUES (
                event = "UPDATE balance: id=" + inputId,
                ts    = system.datetime
              ).
              write("Banco atualizado.").
            CATCH.
              write("Aviso: atualizado em memoria. Banco nao sincronizado.").
            ENDTRY.
          endif.

          write("Saldo de #" + inputId + " atualizado para R$ " + inputBal).
          add(auditLog, "Saldo atualizado: id=" + inputId + " -> R$" + inputBal).
        endif.
      endif.

    " ════════════════════════════════════════════════════
    " 6. DESATIVAR CLIENTE
    " ════════════════════════════════════════════════════
    elseif option == 6.
      printTitle("DESATIVAR CLIENTE").
      write("ID do cliente: ").
      input(inputId).

      tempList = findById(clients, inputId).

      if size(tempList) == 0.
        write("Cliente nao encontrado.").
      else.
        var clientToDeact type Client = tempList[0].
        if not clientToDeact.active.
          write("Cliente ja esta inativo.").
        else.
          write("Desativar '" + clientToDeact.name + "'? (true/false): ").
          input(inputConfirm).

          if inputConfirm.
            clients = deactivate(clients, inputId).

            if dbReady.
              TRY.
                UPDATE clients_db SET active = false WHERE id == inputId.
                APPEND INTO audit_db VALUES (
                  event = "DEACTIVATE: id=" + inputId,
                  ts    = system.datetime
                ).
                write("Banco atualizado.").
              CATCH.
                write("Aviso: operacao em memoria apenas.").
              ENDTRY.
            endif.

            write("Cliente #" + inputId + " desativado.").
            add(auditLog, "Desativado: id=" + inputId).
          else.
            write("Operacao cancelada.").
          endif.
        endif.
      endif.

    " ════════════════════════════════════════════════════
    " 7. REMOVER CLIENTE
    " ════════════════════════════════════════════════════
    elseif option == 7.
      printTitle("REMOVER CLIENTE").
      write("ID do cliente: ").
      input(inputId).

      tempList = findById(clients, inputId).

      if size(tempList) == 0.
        write("Cliente nao encontrado.").
      else.
        var clientToRemove type Client = tempList[0].
        write("Remover '" + clientToRemove.name + "'? (true/false): ").
        input(inputConfirm).

        if inputConfirm.
          // Remove da memória usando QUERY para reconstruir sem o item
          clients = removeById(clients, inputId).

          if dbReady.
            TRY.
              DELETE FROM clients_db WHERE id == inputId.
              APPEND INTO audit_db VALUES (
                event = "DELETE: id=" + inputId,
                ts    = system.datetime
              ).
              write("Removido do banco.").
            CATCH.
              write("Aviso: removido da memoria. Banco nao sincronizado.").
            ENDTRY.
          endif.

          write("Cliente #" + inputId + " removido.").
          add(auditLog, "Removido: id=" + inputId + " (" + clientToRemove.name + ")").
        else.
          write("Operacao cancelada.").
        endif.
      endif.

    " ════════════════════════════════════════════════════
    " 8. RELATÓRIOS EM MEMÓRIA
    " ════════════════════════════════════════════════════
    elseif option == 8.
      if count(clients) == 0.
        write("Nenhum cliente em memoria para gerar relatorio.").
      else.
        showFullReport(clients).
      endif.

    " ════════════════════════════════════════════════════
    " 9. CONSULTAS NO BANCO (MintDB)
    " ════════════════════════════════════════════════════
    elseif option == 9.
      printTitle("CONSULTAS MINTDB").

      if not dbReady.
        write("Banco nao disponivel.").
      else.
        // SELECT COUNT(*)
        var totalDb type int.
        TRY.
          SELECT COUNT(*) FROM clients_db INTO totalDb.
          write("Total de clientes no banco : " + totalDb).
        CATCH.
          write("Erro ao contar registros.").
        ENDTRY.

        // SELECT COUNT(*) com WHERE
        var activeDb type int.
        TRY.
          SELECT COUNT(*) FROM clients_db WHERE active == true INTO activeDb.
          write("Clientes ativos no banco   : " + activeDb).
        CATCH.
          write("Erro ao contar ativos.").
        ENDTRY.

        // SELECT * com resultado em list (escrito como raw)
        var dbResult type list<Client>.
        TRY.
          SELECT * FROM clients_db INTO dbResult.
          var dbSize type int = size(dbResult).
          write("Registros retornados       : " + dbSize).
          // Itera e imprime cada registro bruto
          var ri type int = 0.
          while ri < dbSize.
            write("  [" + ri + "] " + dbResult[ri]).
            ri = ri + 1.
          endwhile.
        CATCH.
          write("Erro ao consultar banco.").
        ENDTRY.

        // Auditoria: mostra eventos registrados
        var auditResult type list<Client>.
        TRY.
          SELECT * FROM audit_db INTO auditResult.
          var auditSize type int = size(auditResult).
          printTitle("LOG DE AUDITORIA (" + auditSize + " eventos)").
          var ai type int = 0.
          while ai < auditSize.
            write("  " + auditResult[ai]).
            ai = ai + 1.
          endwhile.
        CATCH.
          write("Tabela de auditoria indisponivel.").
        ENDTRY.
      endif.

    " ════════════════════════════════════════════════════
    " 10. SALVAR / EXPORTAR CSV
    " ════════════════════════════════════════════════════
    elseif option == 10.
      printTitle("SALVAR E EXPORTAR").

      if count(clients) == 0.
        write("Nenhum dado em memoria para salvar.").
      else.
        TRY.
          // SAVE: salva em CSV
          SAVE clients TO "examples/mintdb_crud/data/clients.csv".
          write("Dados salvos em: " + csvPath).

          // EXPORT: exporta em TXT (separado por ;)
          EXPORT clients TO "examples/mintdb_crud/data/clients.txt".
          write("Dados exportados em: " + txtPath).

          add(auditLog, "CSV/TXT exportado em " + system.time).
        CATCH.
          write("Erro ao salvar arquivos.").
        ENDTRY.
      endif.

    " ════════════════════════════════════════════════════
    " 11. CARREGAR CSV
    " ════════════════════════════════════════════════════
    elseif option == 11.
      printTitle("CARREGAR CSV").
      TRY.
        LOAD "examples/mintdb_crud/data/clients.csv" INTO clients.
        tmpCount = count(clients).
        write("Carregados " + tmpCount + " clientes do arquivo: " + csvPath).
        // Ajusta nextId para evitar colisão de IDs
        nextId = tmpCount + 1.
        add(auditLog, "CSV carregado: " + tmpCount + " registros em " + system.time).
      CATCH.
        write("Erro ao carregar CSV. Verifique se o arquivo existe (opcao 10).").
      ENDTRY.

    " ════════════════════════════════════════════════════
    " 12. LOG DA SESSÃO
    " ════════════════════════════════════════════════════
    elseif option == 12.
      printTitle("LOG DA SESSAO").
      var logSize type int = size(auditLog).
      write("Total de eventos: " + logSize).
      // Demonstra FOR sobre list<string>
      for entry in auditLog.
        write("  > " + entry).
      endfor.
      printSeparator().

    " ════════════════════════════════════════════════════
    " 0. SAIR
    " ════════════════════════════════════════════════════
    elseif option == 0.
      add(auditLog, "Sistema encerrado em " + system.datetime).
      move false to running.

    else.
      write("Opcao invalida. Digite um numero entre 0 e 12.").
    endif.

  endwhile.

  " ── Encerramento ────────────────────────────────────────
  printSeparator().
  write("   Sistema encerrado.").
  write("   " + system.date + " as " + system.time).
  write("   Semana: dia " + system.weekday + " (1=Seg, 7=Dom)").
  printSeparator().

  " Resumo final dos clientes em memória
  var finalTotal type int = count(clients).
  write("Clientes em memoria: " + finalTotal).

  if finalTotal > 0.
    tmpBal = sum(clients.balance).
    write("Soma dos saldos    : R$ " + tmpBal).
  endif.

  // Exibe log completo no encerramento
  write("Eventos na sessao  : " + size(auditLog)).
  for entry in auditLog.
    write("[LOG] " + entry).
  endfor.

  printSeparator().

endprogram.
