# Mint Language – Project Context

## Visão Geral

O **Mint** é uma linguagem de programação **interpretada**, criada para fins **educacionais**, com foco em sintaxe clara, regras explícitas e arquitetura simples, porém organizada para crescimento futuro.

O projeto é dividido em duas frentes principais:

* **Core da linguagem (Python)**: lexer, parser, AST, linter e interpreter
* **Ferramentas de desenvolvimento**: extensão do VS Code (`/vscode-mint`) para syntax highlighting e suporte básico ao editor

O objetivo do MVP é **ensinar como uma linguagem funciona internamente**, não competir com linguagens de produção.

---

## Estado Atual da Linguagem (Contexto Vivo)

### Execução

* Linguagem interpretada
* Implementação em Python
* Arquivo de entrada: `.mint`

### Estrutura obrigatória do programa

```mint
program init.
  var nome type string = "Mint".
initialization.
  write("Hello").
endprogram.
```

### Blocos

* `program init.` → início do programa
* Declarações de variáveis (tipadas)
* `initialization.` → bloco de execução
* `endprogram.` → fim do programa

### Tipos suportados

* `int`
* `float`
* `string`
* `char`
* `bool`

### Variáveis

```mint
var texto type string.
var num type int = 10.
var ok type bool = true.
```

* Tipagem obrigatória
* Inicialização opcional
* Valores padrão:

  * int → 0
  * string → ""
  * bool → false

### Comandos

#### write

```mint
write("texto").
write(variavel).
write((num + 2) * 5).
```

### Expressões

* Operadores: `+ - * /`
* Parênteses suportados
* Aritmética com `int` e `float` (promoção para `float` quando necessário)
* Comparações para `string`/`char` usam ordem lexicográfica por Unicode code point (sem locale)

### Comentários

* Linha inteira iniciada com aspas (`"`) → comentário
* Comentário inline com `//`

---

## Arquitetura do Projeto

### Core da linguagem

```
mintlang/
  lexer.py
  parser.py
  ast_nodes.py
  linter.py
  interpreter.py
  tokens.py
  errors.py
```

Responsabilidades claras:

* `lexer.py` → análise léxica
* `parser.py` → análise sintática
* `ast_nodes.py` → nós da AST
* `linter.py` → validação estática (pré-execução)
* `interpreter.py` → execução

### Extensão VS Code

```
vscode-mint/
  package.json
  language-configuration.json
  syntaxes/
    mint.tmLanguage.json
```

* Responsável apenas por **syntax highlighting e UX de editor**
* Toda nova keyword, tipo ou comando **deve ser refletido aqui**

---

## Regras de Desenvolvimento (IMPORTANTE)

### Papel da IA

* A IA **sempre atua como assistente**, nunca como decisor final
* A IA **não deve implementar nada fora do escopo da feature atual**

### Escopo

* Se o pedido do usuário for **vago, ambíguo ou abrir brechas de design**, a IA deve:

  * Parar
  * Conversar
  * Refinar a ideia junto com o usuário

### Modificação de código

* ❌ Evitar refatorações completas
* ✅ Preferir ajustes pontuais nas funções necessárias
* 🔁 Refatoração ampla **somente se o usuário pedir explicitamente**

### Novos comandos da linguagem

* Qualquer novo comando, keyword ou tipo:

  * Deve ser implementado no **core (Python)**
  * Deve atualizar o **highlighter em `/vscode-mint`**

### Organização de tarefas

* Existe um arquivo **`task.md` na raiz do projeto**
* Toda feature finalizada deve ser registrada com:

  * Nome da feature
  * Resumo do que foi feito
  * Data

---

## Filosofia do Mint

* Sintaxe explícita
* Nada implícito ou mágico
* Preferir verbos claros (`write`, `var`, etc.)
* Linguagem legível para iniciantes
* Erros claros e educativos

---

## Direção futura (não implementar sem pedido explícito)

* Atribuição (`x = x + 1.`)
* Condicionais (`if / else`)
* Comparações
* Strings avançadas
* Formatter
* Diagnósticos no VS Code integrados ao linter

---

Este arquivo **define o contrato de colaboração entre o usuário e a IA**.
Qualquer mudança estrutural deve respeitar este contexto.

