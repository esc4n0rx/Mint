from __future__ import annotations

from pathlib import Path

from ide.services.workbench_service import WorkbenchService


class ModuleService:
    def __init__(self, workbench: WorkbenchService) -> None:
        self.workbench = workbench

    @property
    def root(self) -> Path:
        return self.workbench.modules_dir

    def ensure_examples(self) -> None:
        financial = self.root / 'financial'
        inventory = self.root / 'inventory'
        financial.mkdir(parents=True, exist_ok=True)
        inventory.mkdir(parents=True, exist_ok=True)
        tax_rules = financial / 'tax_rules.mint'
        if not tax_rules.exists():
            tax_rules.write_text(
                'func calculate_tax(amount type decimal) returns decimal.\n'
                '  return amount.\n'
                'endfunc.\n',
                encoding='utf-8',
            )
        stock_calc = inventory / 'stock_calc.mint'
        if not stock_calc.exists():
            stock_calc.write_text(
                'program init.\n'
                '  var message type string = "Inventory routine".\n'
                'initialization.\n'
                '  write(message).\n'
                'endprogram.\n',
                encoding='utf-8',
            )

    def create_module(self, name: str, parent: str | None = None) -> Path:
        base = Path(parent) if parent else self.root
        target = base / name
        target.mkdir(parents=True, exist_ok=True)
        return target

    def create_mint_file(self, folder: str, name: str) -> Path:
        folder_path = Path(folder)
        file_path = folder_path / (name if name.endswith('.mint') else f'{name}.mint')
        if not file_path.exists():
            file_path.write_text(
                'program init.\ninitialization.\n  write("New Mint module").\nendprogram.\n',
                encoding='utf-8',
            )
        return file_path
