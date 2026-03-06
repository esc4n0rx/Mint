# Mint Language – Task Log

Este arquivo registra **todas as features implementadas no projeto Mint**, servindo como histórico técnico e referência de evolução.

Cada entrada deve conter:

* Nome da feature
* Resumo do que foi implementado
* Data de conclusão

---

## Feature: MVP – Core da Linguagem Interpretada

**Data:** 2026-01-21

### Resumo

Implementação do núcleo inicial da linguagem Mint em Python, incluindo:

* Estrutura base do projeto (`mintlang/`)
* Lexer com suporte a:

  * Identificadores e keywords
  * Números inteiros
  * Strings com escape
  * Comentários (`//` e aspas no início da linha)
* Parser com gramática estruturada em blocos:

  * `program init.`
  * Declaração de variáveis tipadas
  * `initialization.`
  * `endprogram.`
* AST organizada e extensível
* Interpreter com:

  * Tipos primitivos (`int`, `string`, `bool`)
  * Valores padrão por tipo
  * Execução do comando `write(...)`
  * Aritmética básica com `int`
* Linter pré-execução com validações:

  * Variáveis duplicadas
  * Uso de variável não declarada
  * Compatibilidade de tipos

---

## Feature: Estrutura Formal do Programa

**Data:** 2026-01-21

### Resumo

Definição da estrutura obrigatória de um programa Mint, separando claramente:

* Fase de declaração (`program init.`)
* Fase de execução (`initialization.`)
* Encerramento explícito (`endprogram.`)

Objetivo:

* Tornar o fluxo do programa claro para fins educacionais
* Evitar efeitos colaterais e execução implícita

---

## Feature: VS Code Syntax Highlighting (.mint)

**Data:** 2026-01-21

### Resumo

Criação da extensão do VS Code para a linguagem Mint, incluindo:

* Reconhecimento de arquivos `.mint`
* Syntax highlighting via TextMate Grammar
* Destaque para:

  * Keywords (`program`, `var`, `write`, etc.)
  * Tipos (`int`, `string`, `bool`)
  * Strings
  * Números
  * Operadores
  * Comentários (`//` e aspas no início da linha)
* Empacotamento em `.vsix` para instalação local

Local:

* `/vscode-mint`

---

## Observações

* Todas as features acima fazem parte do MVP inicial
* Nenhuma funcionalidade fora de escopo foi implementada
* A arquitetura foi mantida simples e organiz

---

## Feature: Tipos float e char

**Data:** 2026-01-21

### Resumo

Adicionados novos tipos e literais:

* Tipo `float` com suporte a literais decimais e aritmética com `int`/`float`
* Tipo `char` com literal em aspas simples e validação de 1 caractere no linter
* Lexer, parser, AST, linter e interpreter atualizados
* Syntax highlighting ajustado na extensão do VS Code

---

## Feature: Estruturas condicionais (IF/ELSEIF/ELSE/ENDIF)

**Data:** 2026-01-22

### Resumo

Adicionadas estruturas condicionais ao Mint com:

* Novas keywords e parsing de blocos `if/elseif/else/endif`
* Operadores de comparação e regras de precedência
* Linter validando tipo booleano da condição e compatibilidade de tipos
* Interpreter executando apenas o primeiro bloco verdadeiro
* Syntax highlighting atualizado na extensão do VS Code

---

## Feature: Operadores lógicos AND/OR/NOT

**Data:** 2026-01-22

### Resumo

Adicionados operadores lógicos com precedência e short-circuit:

* Tokens e parsing para `and`, `or`, `not` com precedência correta
* Linter validando uso estrito de bool e mensagens educativas
* Interpreter com avaliação curta (short-circuit) em `and`/`or`
* Syntax highlighting e exemplos `.mint` atualizados

## Feature: Regras de comparação e widening int->float

**Data:** 2026-03-06

### Resumo

Aprimoramentos pontuais de semântica e documentação:

* Linter agora bloqueia comparações encadeadas implícitas (ex.: `a < b < c`) com mensagem orientando uso de parênteses e `AND`/`OR`
* Inicialização de variáveis `float` agora aceita `int` com conversão implícita segura (`int -> float`)
* Docstring do linter atualizada para refletir suporte real a aritmética com `int`/`float`
* `context.md` atualizado com os tipos atuais e regra de comparação lexicográfica Unicode para `string`/`char`


## Feature: Funções tipadas com parâmetros e retorno

**Data:** 2026-03-06

### Resumo

Implementado suporte a funções reutilizáveis no Mint com foco em escopo e tipagem:

* Novas keywords/tokens: `FUNC`, `ENDFUNC`, `RETURN`, `RETURNS`
* Parser e AST com declaração de função, parâmetros tipados, `RETURN`, chamada de função em expressão e chamada como comando para funções sem retorno
* Linter com validação de assinatura, duplicidade de função/parâmetro, tipos de argumentos e retorno, além de `RETURN` fora de função
* Interpreter com registro prévio de funções, frame local por chamada, binding de parâmetros, retorno imediato e uso de escopo local com precedência sobre globais
* Highlighter do VS Code atualizado para novas keywords e melhor legibilidade de chamadas de função
