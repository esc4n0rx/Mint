#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/mint"

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return
  fi
  echo ""
}

PYTHON_CMD="$(find_python)"
if [[ -z "$PYTHON_CMD" ]]; then
  echo "Erro: Python não encontrado. Instale Python 3.10+ e rode novamente."
  exit 1
fi

"$PYTHON_CMD" - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Erro: é necessário Python 3.10 ou superior.")
print(f"Python OK: {sys.version.split()[0]}")
PY

mkdir -p "$BIN_DIR"
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
REPO_DIR="$REPO_DIR"
PYTHON_CMD="$PYTHON_CMD"
export PYTHONPATH="\$REPO_DIR\${PYTHONPATH:+:\$PYTHONPATH}"
exec "\$PYTHON_CMD" -m mintlang.cli "\$@"
EOF
chmod +x "$LAUNCHER"

echo "Launcher criado em: $LAUNCHER"

for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
  if [[ -f "$RC" ]] && ! grep -Fq 'export PATH="$HOME/.local/bin:$PATH"' "$RC"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC"
    echo "PATH atualizado em $RC"
  fi
done

echo "Instalação concluída. Rode: mint -file examples/hello.mint"
echo "Se o comando não abrir no terminal atual, execute: source ~/.bashrc (ou ~/.zshrc)."
