from __future__ import annotations


def next_line_indent(previous_line: str, tab_unit: str) -> str:
    stripped = previous_line.rstrip()
    base = previous_line[: len(previous_line) - len(previous_line.lstrip())]
    if stripped.endswith((".", "then")):
        return base
    if stripped.endswith(("if", "while", "for", "try", "func", "struct")):
        return base + tab_unit
    return base
