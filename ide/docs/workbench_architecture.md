# Arquitetura do Mint ERP Studio

## Objetivo
Separar a aplicação entre experiência visual ERP e serviços reutilizáveis de backend local.

## Camadas

### UI
- `ui/main_window.py`: composição do workbench.
- `ui/widgets/erp_navigation.py`: árvore principal ERP.
- `ui/panels/table_designer.py`: modelagem de tabelas.
- `ui/panels/module_browser.py`: árvore de módulos.
- `ui/panels/execution_panel.py`: execução e histórico.
- `ui/panels/help_panel.py`: documentação contextual.
- `ui/panels/object_dashboard.py`: visão geral do projeto.

### Serviços
- `services/workbench_service.py`: estrutura base do workspace.
- `services/table_service.py`: persistência e geração Mint de tabelas.
- `services/module_service.py`: bootstrap e criação de módulos/arquivos.
- `services/execution_service.py`: histórico e logs de execução.

### Core reutilizado
- `core/runner.py`: execução via CLI do Mint.
- `core/linter_bridge.py`: integração com lexer/parser/linter reais.
- `core/realtime_validator.py`: diagnósticos em tempo real.
- `editor/`: editor Mint legado preservado.

## Diretórios de workspace

```text
workspace/
  modules/
  programs/
  generated/
    tables/
  .mint_workbench/
    tables/
    metadata/
    logs/
```

## Expansão futura
- metadata de índices/relacionamentos;
- execução de funções isoladas;
- integração visual com MintDB;
- catálogos por módulo funcional do ERP.
