# Mint IDE (PyQt5)

IDE desktop oficial do projeto Mint, com foco em produtividade para desenvolvimento de arquivos `.mint`.

## Estrutura

- `main.py`, `app.py`: bootstrap da aplicação.
- `core/`: integração com runtime/linter, settings, workspace e arquivos.
- `ui/`: main window, explorer, tabs, terminal e diálogos.
- `editor/`: editor Mint customizado, line numbers, auto-indent e syntax highlight.
- `models/`: modelos de diagnóstico e estado.
- `utils/`: utilitários auxiliares.

## Dependências

```bash
pip install PyQt5
```

## Como executar

No root do repositório:

```bash
python -m ide.main
```

## Configuração de runtime/linter

A IDE utiliza integração nativa com os módulos do próprio Mint:
- execução via `python -m mintlang.cli -file <arquivo.mint>`
- lint via `mintlang.module_loader.ModuleLoader` + `mintlang.linter.Linter`

Também há campos de configuração para caminhos de runtime/linter no diálogo de configurações para futuras evoluções.

## Funcionalidades implementadas

- Workspace com explorer de arquivos e ações de criação/renomeação/exclusão.
- Editor com abas múltiplas, line numbers, highlight de linha atual, auto-indent e sintaxe Mint.
- Highlight atualizado para comandos MintDB Beta 2 (`DB COMPACT`, `SHOW TABLES`, `DESCRIBE`, `INDEX CREATE`, `SELECT COUNT(*)`, além dos comandos Beta 1).
- Fluxos de abrir/salvar/salvar como/salvar todos.
- Execução do arquivo atual com output assíncrono.
- Lint do arquivo atual com painel de problemas e navegação por clique.
- Terminal integrado com execução de comandos shell.
- Status bar com arquivo atual, cursor e workspace.
- Atalhos principais (`Ctrl+N`, `Ctrl+O`, `Ctrl+Shift+O`, `Ctrl+S`, `Ctrl+Shift+S`, `F5`, `F8`).
- Settings persistentes via `QSettings`.
- Explorer otimizado para workspaces grandes (apenas coluna de nome, menor custo de render e root path consistente).
- Abertura de arquivo evita recarregar conteúdo quando o arquivo já está aberto em aba.
- Correção no menu de contexto: criar novo arquivo/pasta agora respeita corretamente a pasta selecionada.


## Próximos passos sugeridos

- autocomplete e navegação semântica;
- parser incremental para diagnósticos em tempo real;
- painel de busca global e replace;
- restaurar sessão completa de abas e posição de cursor;
- temas avançados e customização visual.

## Novidades (2026-03-11)

- Tema dark padrão com `ThemeManager` e stylesheet central em `assets/themes/dark.qss`.
- Validação de sintaxe em tempo real com debounce + thread, sugestões de typo e integração com parser/linter.
- Destaque visual de diagnósticos no editor (sublinhado ondulado + tooltip).
- Painel de problemas ampliado com coluna de sugestão e navegação por linha/coluna.
- Área educativa **Aprender Mint** com tópicos, explicações e botão para inserir exemplo no editor.


## Novidades (2026-03-12)

- IDE atualizada para suportar fluxos MintDB Beta 2 no syntax highlight e no guia **Aprender Mint**.
- Snippet educacional atualizado com `INDEX CREATE`, `SHOW TABLES`, `DESCRIBE`, `SELECT COUNT(*)` e `DB COMPACT`.
- Correções de performance no explorer e abertura de arquivos em projetos grandes.
- Correção de UX: criação por clique direito respeitando a pasta alvo selecionada.
