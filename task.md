# Mint Language – Task Log

Registro consolidado das funcionalidades implementadas.

## 2026-03-12 — Ajustes adicionais de robustez (follow-up)
- Linter passou a detectar divisão/módulo por zero com literal (`/ 0` e `% 0`) antes de runtime.
- Runtime numérico endurecido para não tratar `bool` como `int` em operações aritméticas.
- Testes automatizados adicionados para:
  - guard de divisão por zero no linter;
  - não vazamento de escopo de variável declarada dentro de `FOR`;
  - rejeição léxica imediata de char inválido (`'AB'`);
  - bloqueio de path traversal em `LOAD`.

## 2026-03-12 — Correções de robustez (runtime/linter/highlighter)
- Core:
  - Divisão `/` no interpreter passa a retornar `float` também para `int/int`.
  - Operador `%` adicionado no lexer/parser/linter/interpreter com validação `int % int`.
  - Concatenação de strings com `+` suportada em linter e runtime.
  - LOAD/SAVE/EXPORT agora validam caminho com sandbox no diretório atual (bloqueio de path traversal).
  - QUERY evita falha por campo ausente usando leitura segura com fallback de valor padrão.
  - Lexer valida `char` com exatamente 1 caractere já na análise léxica e amplia escapes com `\r` e `\\`.
  - Linter adiciona warning para índice negativo e bloqueia `insert` com alvo que não seja variável.
- MintDB:
  - `AUTO_INCREMENT` implementado no append com preenchimento automático por `max + 1`.
  - `DB COMPACT` ajustado para liberar/reassumir lock durante `os.replace`, melhorando compatibilidade no Windows.
- Organização:
  - Novo `mintlang/utils.py` para utilitários compartilhados (`extract_collection_inner`, `is_struct_collection`, `SYSTEM_MEMBERS`, conversão/serialização).
  - Linter/interpreter delegam para utilitários centralizados.
  - AST remove tipos mortos `ListType` e `TableType`.
- Highlighters:
  - VS Code: operadores incluem `%`, escapes com `\r` e regras case-insensitive com `(?i)`.
  - IDE (PyQt): keywords case-insensitive (`Qt.CaseInsensitive`) e suporte visual ao operador `%`.

## 2026-01-21 — MVP do núcleo
- Lexer, parser, AST, linter e interpreter iniciais.
- Estrutura obrigatória `program init.` / `initialization.` / `endprogram.`
- Tipos iniciais e `write(...)`.
- Extensão VS Code com suporte a `.mint`.

## 2026-01-21 — Tipos `float` e `char`
- Literais de float e char.
- Validação semântica para char com 1 caractere.
- Regras de tipo propagadas no linter/interpreter.

## 2026-01-22 — Controle de fluxo
- `if/elseif/else/endif`.
- `while/endwhile`.
- Operadores lógicos `and/or/not` com short-circuit.

## 2026-03-06 — Regras semânticas
- Comparação encadeada bloqueada no linter.
- Widening seguro `int -> float` em atribuições/inicializações.

## 2026-03-06 — Funções tipadas
- `func/endfunc`, `returns`, `return`.
- Parâmetros tipados, chamada em expressão e como comando.
- Escopo local por chamada e validações de assinatura/retorno.

## 2026-03-06 — Novas features: `input` e `move`
- Novo comando `input(...)`:
  - Linter exige alvo como variável (`VarRef`) e variável declarada.
  - Runtime lê do terminal e converte de acordo com o tipo alvo (`int`, `float`, `bool`, `char`, `string`).
  - Erros claros de conversão (ex.: `Input inválido para variável 'age': esperado int.`).
- Novo comando `move source to target.`:
  - Aceita literal, variável ou expressão no `source`.
  - `target` deve ser variável existente.
  - Compatibilidade de tipos igual à atribuição (`int -> float` permitido, demais incompatíveis).
- Highlighter do VS Code atualizado para `input`, `move`, `to`.
- Novos exemplos em `examples/` cobrindo casos válidos e inválidos.

## 2026-03-06 — CLI de distribuição e instaladores multiplataforma
- CLI agora suporta:
  - `-file/--file` para executar arquivo `.mint`.
  - `-create/--create` para gerar template inicial `.mint`.
  - compatibilidade com modo legado por argumento posicional.
- Instaladores adicionados:
  - `install/install_linux.sh`
  - `install/install_macos.sh`
  - `install/install_windows.bat`
- Scripts de fallback adicionados para execução sem PATH:
  - `run.sh`, `run.command`, `run.bat`
- Exemplo novo: `examples/HelloWorld.mint`.

## 2026-03-09 — Feature `STRUCT`
- Core da linguagem atualizado com suporte a:
  - definição de `STRUCT ... ENDSTRUCT` com campos tipados (`campo type tipo.`);
  - declaração de variável com tipo de struct (`var client type Client.`);
  - acesso a campos com dot notation (`client.name`) em expressões, `write`, `if`, `while`, `input` e funções;
  - atribuição em campos (`client.age = 25.`) com validação de tipo e regra existente de widening `int -> float`.
- Linter atualizado para validar:
  - struct duplicada;
  - campo duplicado na mesma struct;
  - tipo inválido de campo;
  - uso de struct não declarada em variáveis/parâmetros;
  - acesso a campo inexistente;
  - atribuição incompatível em campo.
- Interpreter atualizado para:
  - registrar structs antes da execução;
  - instanciar structs com valores padrão por tipo;
  - permitir leitura/escrita de campos e `input` em campos.
- Highlighter do VS Code atualizado em `vscode-mint/syntaxes/mint.tmLanguage.json` para destacar `STRUCT`, `ENDSTRUCT` e acessos com `.`.
- Exemplo adicionado: `examples/struct_ok.mint`.

## 2026-03-09 — Feature: LIST e TABLE
- Resumo: Implementação de coleções tipadas para armazenar múltiplos registros.
- Core da linguagem atualizado com suporte a:
  - tipos genéricos `list<T>` e `table<T>` no parser/linter/interpreter;
  - comandos `add(lista, valor)` e `insert(tabela, registro)`;
  - acesso por índice `colecao[indice]` com validação de tipo e erro de limite;
  - função builtin `size(colecao)` para `list` e `table`;
  - leitura de campos em registros indexados (ex.: `clients[0].name`).
- Highlighter do VS Code atualizado para `list`, `table`, `add`, `insert`, `size` e destaque de `<` `>` `[` `]`.
- Exemplo adicionado: `examples/list_table_ok.mint`.

## 2026-03-09 — Feature: QUERY em memória
- Nome: `QUERY FROM ... WHERE ... INTO ...`.
- Core atualizado com suporte a:
  - novos tokens/keywords `QUERY`, `FROM`, `WHERE`, `INTO`;
  - parser para statement `QUERY FROM <origem> WHERE <expr> INTO <destino>.`;
  - novo nó AST `QueryStmt`.
- Linter atualizado para validar:
  - existência da origem e do destino;
  - origem como `list<Struct>` ou `table<Struct>`;
  - compatibilidade de tipos entre origem e destino;
  - resolução de campos implícitos dentro do `WHERE` com validação contra a struct da origem;
  - resultado booleano obrigatório no `WHERE`.
- Interpreter atualizado para executar QUERY em varredura linear em memória,
  avaliando o `WHERE` no contexto do item atual e inserindo itens aprovados no destino.
- Highlighter do VS Code atualizado para destacar `QUERY`, `FROM`, `WHERE`, `INTO`.
- Exemplo adicionado: `examples/query_ok.mint`.

## 2026-03-09 — Feature: LOAD / SAVE / EXPORT (CSV e TXT)
- Nome: `LOAD`, `SAVE`, `EXPORT` para persistência de coleções estruturadas em memória.
- Core atualizado com suporte a:
  - novos tokens/keywords `LOAD`, `SAVE`, `EXPORT` e reutilização de `TO`/`INTO`;
  - parser para statements:
    - `LOAD "path" INTO colecao.`
    - `SAVE colecao TO "path".`
    - `EXPORT colecao TO "path".`
  - novos nós AST `LoadStmt`, `SaveStmt`, `ExportStmt`;
  - linter para validar existência e compatibilidade da coleção (`table<Struct>` ou `list<Struct>`), com path em string literal;
  - interpreter com leitura/escrita linear de arquivos delimitados:
    - `.csv` com `,`
    - `.txt` com `;`
    - cabeçalho obrigatório e mapeamento por nome de coluna
    - conversão tipada (`int`, `float`, `string`, `char`, `bool`)
    - LOAD substitui o conteúdo da coleção alvo (sem append automático)
    - mensagens claras para erro de cabeçalho e conversão.
- Highlighter do VS Code atualizado para destacar `load`, `save`, `export`, `LOAD`, `SAVE`, `EXPORT` e `TO`.
- Exemplo adicionado: `examples/load_save_export_ok.mint` e arquivos de dados de apoio em `examples/clients.csv` e `examples/clients.txt`.

## 2026-03-09 — Feature: Modularização e Imports
- Nome: `IMPORT` com resolução de módulos `.mint` por caminho pontuado.
- Core atualizado com suporte a:
  - novo token/keyword `IMPORT` no lexer/parser;
  - imports no topo do arquivo (`IMPORT modulo.caminho.`);
  - parser aceitando arquivos de módulo sem `program init` (declarações reutilizáveis);
  - carregador de módulos com resolução `a.b -> a/b.mint`, deduplicação de carga, detecção de circularidade e erro claro para módulo inexistente;
  - merge de funções e structs importadas no escopo global do arquivo consumidor com validação de colisões pós-import.
- Linter/validação de carga atualizado para bloquear `IMPORT` fora do topo com mensagem clara.
- Highlighter do VS Code atualizado para destacar `import/IMPORT`.
- Exemplos/módulos adicionados para validação real da feature:
  - `utils/math.mint`, `finance/tax.mint`, `health/imc.mint`, `sales/customer.mint`, `examples/imports_test.mint`.

## 2026-03-09 — Feature: FOR + Aggregations + TRY/CATCH
- Nome: `FOR/ENDFOR`, agregações `count/sum/avg` e tratamento de erro `TRY/CATCH/ENDTRY`.
- Core atualizado com suporte a:
  - novo loop `FOR item IN collection. ... ENDFOR.` para `list<T>` e `table<T>`, com escopo local da variável de iteração;
  - novas expressões de agregação `count(collection)`, `sum(collection.field)` e `avg(collection.field)` (com suporte adicional a coleção numérica direta);
  - novo bloco `TRY. ... CATCH. ... ENDTRY.` para capturar erros de runtime e continuar o fluxo.
- Linter atualizado para validar coleção iterável no `FOR`, escopo do item de iteração, regras de campo numérico para `sum/avg` e estrutura semântica dos novos blocos.
- Interpreter atualizado para executar `FOR`, calcular agregações em varredura linear e capturar `RuntimeMintError` em `TRY/CATCH`.
- Highlighter do VS Code atualizado para destacar `FOR`, `IN`, `ENDFOR`, `TRY`, `CATCH`, `ENDTRY`, `count`, `sum`, `avg`.
- Exemplos adicionados: `examples/for_numbers.mint`, `examples/for_structs.mint`, `examples/aggregations.mint`, `examples/try_catch_load.mint`, `examples/try_catch_avg.mint`.

## 2026-03-10 — Feature: Variáveis Sistêmicas (`system` namespace)
- Nome: Namespace reservado `system` para valores sistêmicos nativos.
- Core atualizado com suporte a:
  - resolução de `system.date`, `system.time`, `system.datetime`, `system.timestamp`, `system.year`, `system.month`, `system.day`, `system.weekday`;
  - suporte adicional a `system.hour`, `system.minute`, `system.second`;
  - avaliação em runtime a cada acesso, com `weekday` normalizado para `1=Monday ... 7=Sunday`.
- Linter atualizado para validar:
  - `system` como namespace reservado (bloqueando declarações de variável/struct/função/parâmetro e uso como variável comum);
  - membros válidos do namespace `system`;
  - tipagem estática conhecida para cada membro;
  - bloqueio de escrita em `system.*` (namespace somente leitura).
- Interpreter atualizado para resolver valores sistêmicos a partir do ambiente de execução no momento da leitura.
- Highlighter do VS Code atualizado em `vscode-mint/syntaxes/mint.tmLanguage.json` para destacar `system` e membros sistêmicos.
- Exemplos adicionados em `examples/system_datetime.mint`, `examples/system_conditions.mint` e `examples/system_assignment.mint`.

## 2026-03-10 — Feature: Mint IDE Desktop (PyQt5)
- Nome: `Mint IDE` oficial em `/ide`.
- Implementado app desktop com PyQt5 e arquitetura modular (`core`, `ui`, `editor`, `models`, `utils`).
- Entregues: janela principal completa, explorer de arquivos/workspace, editor com abas múltiplas, syntax highlight Mint, terminal/output integrado, execução assíncrona do runtime Mint, integração de linter com painel de problemas, status bar e atalhos principais.
- Incluídos fluxos de abrir/salvar/salvar como/salvar todos, confirmação para alterações não salvas e settings persistentes (`QSettings`).
- Documentação adicionada em `ide/README.md`.

## 2026-03-11 — Feature: Evolução visual da Mint IDE + Validação em Tempo Real + Aprenda Mint
- Nome: modernização da IDE oficial em `/ide` com foco em experiência de uso.
- UI/tema:
  - dark mode definido como padrão com infraestrutura de tema em `ide/core/theme_manager.py` e assets em `ide/assets/themes/dark.qss`;
  - aplicação do tema no bootstrap da IDE e suporte preparado para novos temas futuros;
  - refinamentos visuais para menus, toolbar, tabs, explorer, tabelas, painéis e status bar via QSS centralizado.
- Validação em tempo real:
  - novo módulo `ide/core/realtime_validator.py` com debounce e validação assíncrona (thread);
  - diagnósticos com severidade, posição e sugestão (`ide/models/diagnostics.py`);
  - detecção incremental de typos de keywords/comandos, import malformado e blocos não fechados;
  - integração com lexer/parser/linter do Mint para diagnósticos sintáticos/semânticos durante edição.
- Integração na UI:
  - sublinhado ondulado no editor + tooltip contextual de erro/aviso;
  - sincronização com painel de problemas (incluindo coluna de sugestão) e navegação para linha/coluna;
  - atualização automática ao trocar de aba ou editar arquivo.
- Área educativa:
  - novo diálogo `Aprender Mint` com tópicos navegáveis e conteúdo introdutório da linguagem;
  - exemplos práticos embutidos e ação para inserir snippet diretamente no editor.
- Configurações:
  - diálogo de settings atualizado com seleção de tema (estrutura extensível, dark ativo atualmente).

## 2026-03-11 — Exemplo oficial: Customer CRUD modular em Mint
- Nova pasta `examples/customer_crud` com programa completo de cadastro de clientes no terminal.
- Arquitetura modular com imports entre múltiplos arquivos (`main`, `menu`, `service`, `repository`, `validators`, `helpers`, `model`).
- CRUD completo com persistência CSV em `examples/customer_crud/data/clients.csv`.
- Demonstrações práticas de `QUERY`, `FOR`, agregações (`count/sum/avg`), `TRY/CATCH` e variáveis sistêmicas (`system.datetime`).
- README do exemplo com instruções de execução, estrutura e objetivos didáticos.

## 2026-03-12 — Feature: MintDB Beta (storage nativo .mintdb)
- Implementado núcleo MintDB nativo em `mintlang/mintdb.py` com:
  - header binário fixo, assinatura/magic e versão;
  - catálogo persistido com metadados de tabelas e schemas;
  - blocos de dados append-only com checksums por bloco;
  - checksum global do arquivo para detectar adulteração manual/corrupção;
  - CRUD beta com tombstone lógico para update/delete.
- Parser/AST/linter/interpreter integrados com comandos:
  - `DB CREATE`, `DB OPEN`, `TABLE CREATE`, `APPEND`, `SELECT ... WHERE ... INTO`, `UPDATE`, `DELETE`.
- Runtime integrado para persistir/cararregar dados via MintDB sem banco externo.
- Highlighter VS Code atualizado com novas keywords de banco.
- Documentação técnica criada em `docs/mintdb_beta.md`.
- Exemplos adicionados em `examples/mintdb/` cobrindo fluxo de criação, append, select, update, delete e validação de abertura.

## 2026-03-12 — Correção de integridade MintDB Beta 1 (PRIMARY KEY + linter)
- Enforcement de `PRIMARY KEY` em runtime para `APPEND`, `APPEND STRUCT` e `UPDATE` com bloqueio de colisões em registros ativos.
- `DELETE` mantém política de tombstone e permite reutilizar chave de registros removidos logicamente.
- `DB CREATE` agora falha quando o arquivo `.mintdb` já existe (comportamento seguro e previsível).
- Linter ganhou severidade (`error`/`warning`/`info`) e regra de warning para fluxo persistido não idempotente (`DB OPEN` + seed fixa com PK literal).
- IDE atualizada para respeitar severidade real do linter nos diagnósticos.
- Documentação MintDB atualizada e novos exemplos em `examples/mintdb/` para casos válidos, erros de integridade e fluxo mais seguro.
- Testes automatizados adicionados em `tests/test_mintdb_beta1_integrity.py` cobrindo constraints, reabertura e warnings estáticos.

## 2026-03-12 — Feature: MintDB Beta 2
- Índices nativos persistidos (PK + `INDEX CREATE`) com uso real em lookup de igualdade.
- Comandos de inspeção `SHOW TABLES` e `DESCRIBE`.
- Suporte a `SELECT COUNT(*) ... INTO`.
- `DB COMPACT` com reescrita segura em arquivo temporário e troca atômica.
- File lock exclusivo de escrita (`.lock`) e liberação no encerramento.
- Journal (`.journal`) para operações críticas e bloqueio seguro no recovery.
- Validação estrutural aprofundada de blocos, offsets, encadeamento e consistência de índices.
- Documentação Beta 2 em `docs/mintdb_beta2.md` e exemplos em `examples/mintdb_beta2/`.
- Testes automatizados Beta 2 em `tests/test_mintdb_beta2.py`.

## 2026-03-17 — Auditoria técnica Beta 3 (estabilização e documentação oficial)
- Corrigida a execução padrão de testes com `pytest.ini` (`pythonpath = .`), eliminando falha de coleta por import do pacote `mintlang`.
- Substituídos placeholders em `examples/mintdb_beta2/02..11` por exemplos funcionais cobrindo fluxo real da Beta 2.
- Criados documentos oficiais:
  - `docs/beta3_audit_report.md` (achados, riscos, correções e recomendações);
  - `docs/mint_feature_status.md` (matriz real de suporte por comando);
  - `docs/mint_language_reference.md` (referência oficial da linguagem para desenvolvedores).
