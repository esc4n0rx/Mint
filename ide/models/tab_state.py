from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TabState:
    file_path: str
    is_modified: bool = False
