from __future__ import annotations

from pathlib import Path


class FileManager:
    @staticmethod
    def read_text(path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    @staticmethod
    def write_text(path: str, content: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    @staticmethod
    def create_folder(path: str) -> None:
        Path(path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def rename(old_path: str, new_path: str) -> None:
        Path(old_path).rename(new_path)

    @staticmethod
    def delete(path: str) -> None:
        p = Path(path)
        if p.is_dir():
            for child in sorted(p.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink()
                else:
                    child.rmdir()
            p.rmdir()
        elif p.exists():
            p.unlink()
