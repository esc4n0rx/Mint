from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


TOPICS = {
    "O que é Mint": """# O que é o Mint
Mint é uma linguagem interpretada educacional com foco em **clareza sintática**,
**legibilidade** e arquitetura simples para aprendizado de compiladores/interpreters.

Ela prioriza regras explícitas, mensagens de erro didáticas e uma sintaxe previsível.
""",
    "Estrutura básica": """# Estrutura básica
```mint
program init.
  var nome type string = "Mint".
initialization.
  write("Hello").
endprogram.
```

- `program init.` inicia o programa
- declarações de `var` ficam no topo
- `initialization.` contém o fluxo principal
- `endprogram.` fecha o arquivo executável
""",
    "Sintaxe essencial": """# Sintaxe essencial
## Variáveis
```mint
var idade type int = 10.
var nome type string.
```

## Imports
```mint
import finance.tax.
```

## Loops e condições
```mint
if idade > 18.
  write("maior").
endif.

for item in clientes.
  write(item.nome).
endfor.
```
""",
    "Exemplos práticos": """# Exemplos práticos
```mint
STRUCT Client.
  id type int.
  name type string.
  age type int.
ENDSTRUCT.

program init.
  var adults type list<Client>.
initialization.
  query from clients where age >= 18 into adults.
  write(count(adults)).
endprogram.
```
""",
    "MintDB Beta 2": """# MintDB Beta 2
```mint
program init.
  var results type list<Client>.
  var total type int = 0.
initialization.
  DB CREATE "clientes.mintdb".
  DB OPEN "clientes.mintdb".

  TABLE CREATE clients (id int PRIMARY KEY, email string, name string, age int).
  INDEX CREATE idx_clients_email ON clients (email).

  APPEND INTO clients VALUES (id = 1, email = "ana@mint.dev", name = "Ana", age = 30).
  SHOW TABLES.
  DESCRIBE clients.
  SELECT COUNT(*) FROM clients INTO total.
  SELECT * FROM clients WHERE email == "ana@mint.dev" INTO results.
  DB COMPACT.
endprogram.
```
""",
    "Dicas e erros comuns": """# Dicas e erros comuns
- `MOVER` é inválido, use `move`.
- `imprt` é inválido, use `import`.
- `SELEC` é inválido, use `SELECT`.
- `APEND` é inválido, use `APPEND`.
- Blocos devem fechar: `if` com `endif`, `for` com `endfor`, etc.
- Sempre finalize statements com `.` na sintaxe Mint atual.
""",
    "Estrutura de projeto": """# Estrutura de projeto
- Arquivos `.mint` ficam organizados por domínio (`finance/`, `sales/`, etc.).
- Módulos importáveis usam caminho pontuado (`import sales.customer.`).
- Exemplos oficiais estão em `examples/`.
- Execute scripts com: `python -m mintlang.cli -file arquivo.mint`
""",
}

EXAMPLE_SNIPPET = """STRUCT Client.
  id type int.
  email type string.
  name type string.
  age type int.
ENDSTRUCT.

program init.
  var out type list<Client>.
  var total type int = 0.
initialization.
  DB CREATE "demo.mintdb".
  DB OPEN "demo.mintdb".
  TABLE CREATE clients (id int PRIMARY KEY, email string, name string, age int).
  INDEX CREATE idx_clients_email ON clients (email).
  APPEND INTO clients VALUES (id = 1, email = "ana@mint.dev", name = "Ana", age = 30).
  SHOW TABLES.
  DESCRIBE clients.
  SELECT COUNT(*) FROM clients INTO total.
  SELECT * FROM clients WHERE email == "ana@mint.dev" INTO out.
  DB COMPACT.
endprogram.
"""


class LearnMintDialog(QDialog):
    insert_example_requested = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Aprender Mint")
        self.resize(980, 640)

        self.topics = QListWidget()
        self.content = QTextEdit()
        self.content.setReadOnly(True)
        self.content.setMarkdown(TOPICS["O que é Mint"])

        for topic in TOPICS:
            QListWidgetItem(topic, self.topics)
        self.topics.setCurrentRow(0)
        self.topics.currentTextChanged.connect(self._on_topic_changed)

        title = QLabel("Guia rápido da linguagem Mint")
        title.setStyleSheet("font-size:18px;font-weight:700;")

        self.insert_btn = QPushButton("Inserir exemplo no editor")
        self.insert_btn.clicked.connect(lambda: self.insert_example_requested.emit(EXAMPLE_SNIPPET))

        left = QVBoxLayout()
        left.addWidget(title)
        left.addWidget(self.topics)
        left.addWidget(self.insert_btn)

        right = QVBoxLayout()
        right.addWidget(self.content)

        body = QHBoxLayout()
        body.addLayout(left, 1)
        body.addLayout(right, 3)

        root = QVBoxLayout(self)
        root.addLayout(body)

    def _on_topic_changed(self, topic: str) -> None:
        self.content.setMarkdown(TOPICS.get(topic, ""))
