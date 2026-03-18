# Mint ERP Studio (PyQt5)

O diretório `ide/` agora hospeda o **Mint ERP Studio**, um workbench visual inspirado em fluxos de ERP/SAP para modelagem de tabelas, organização de módulos Mint, edição técnica e execução operacional.

## Propósito do produto

A aplicação deixou de ser centrada em uma IDE tradicional. O foco atual é:

- navegação por árvore ERP;
- modelagem visual de tabelas internas;
- catálogo técnico de objetos;
- organização de módulos `.mint` em pastas reutilizáveis;
- edição de código Mint com syntax highlight preservado;
- execução de programas com histórico e logs.

## Áreas principais

- **ERP Workbench**: árvore principal com Projeto, Sistema e Ajuda.
- **Catálogo de tabelas**: lista de definições persistidas em `.mint_workbench/tables/*.json`.
- **Designer de tabela**: formulário + grid para campos, tipos, PK, default e observações.
- **Módulos ERP**: árvore de `modules/` com criação de pasta e arquivos `.mint`.
- **Editor Mint**: editor legado reaproveitado com highlight, lint e diagnósticos em tempo real.
- **Centro de execução**: execução de programas `.mint`, output estruturado e histórico local.

## Estrutura interna

- `core/`: runtime, lint, workspace, settings e integrações básicas.
- `services/`: serviços do workbench (`table_service`, `module_service`, `execution_service`, `workbench_service`).
- `models/`: modelos de tabela e execução.
- `ui/panels/`: painéis de workbench (tabelas, módulos, execução, ajuda, dashboard).
- `ui/widgets/`: navegação ERP lateral.
- `editor/`: editor Mint original reaproveitado e adaptado ao novo visual.

## Persistência local

Ao abrir um workspace, o studio cria/usa:

- `.mint_workbench/tables/` → definições JSON das tabelas;
- `.mint_workbench/metadata/execution_history.json` → histórico de execuções;
- `.mint_workbench/logs/` → logs de output;
- `generated/tables/` → artefatos `.mint` gerados a partir do modelador;
- `modules/` → módulos organizados para uso futuro com `IMPORT`.

## Exemplos entregues

- tabela exemplo: `erp_customer`;
- módulos exemplo: `modules/financial/tax_rules.mint`, `modules/inventory/stock_calc.mint`;
- programa exemplo: `programs/daily_close.mint`.

## Como executar

```bash
pip install PyQt5
python -m ide.main
```

## Fluxos principais

### 1. Criar tabela
1. Abra **Projeto → Tabelas**.
2. Vá para a aba **Designer de tabela**.
3. Preencha nome, descrição e módulo.
4. Adicione campos no grid.
5. Salve e, se desejar, clique em **Gerar Mint**.

### 2. Criar módulo
1. Abra **Projeto → Módulos**.
2. Crie uma pasta técnica.
3. Crie um arquivo `.mint` dentro do módulo.
4. Abra em duplo clique para editar no editor integrado.

### 3. Executar programa
1. Abra o arquivo `.mint` no editor ou informe o caminho no **Centro de execução**.
2. Informe parâmetros textuais, se necessário para documentação operacional.
3. Clique em **Executar**.
4. Consulte output, histórico e logs.

## Próximos passos recomendados

- execução real de funções específicas com wrapper automático;
- visualizador de estruturas MintDB e dados reais de tabela;
- relacionamento entre tabelas, índices e constraints;
- restore de sessão de abas abertas;
- inspeção semântica por módulo/objeto ERP.
