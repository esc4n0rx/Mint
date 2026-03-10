from __future__ import annotations

import subprocess
from typing import Sequence


def run_capture(args: Sequence[str], cwd: str | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr
