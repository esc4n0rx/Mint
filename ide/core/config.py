from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IdeConfig:
    theme: str = "dark"
    font_size: int = 12
    tab_size: int = 2
    use_spaces: bool = True
