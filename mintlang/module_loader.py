from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple

from .ast_nodes import FuncDecl, Program, StructDecl
from .lexer import Lexer
from .linter import LintIssue
from .parser import Parser
from .tokens import Token, TokenType
from .errors import MintError


@dataclass
class LoadedModule:
    name: str
    path: Path
    program: Program


class ModuleLoader:
    def __init__(self, root_file: Path):
        self.root_file = root_file.resolve()
        self.root_dir = Path.cwd().resolve()
        self.modules: Dict[str, LoadedModule] = {}
        self.issues: List[LintIssue] = []

    def load(self) -> Tuple[Program, List[LintIssue]]:
        main_program = self._parse_file(self.root_file)
        if main_program is None:
            return Program(imports=[], structs=[], decls=[], body=[], funcs=[]), self.issues

        loading_stack: List[str] = []
        ordered_modules: List[LoadedModule] = []
        for imp in main_program.imports:
            self._load_module(imp.module_path, loading_stack, ordered_modules)

        imported_structs: List[StructDecl] = []
        imported_funcs: List[FuncDecl] = []
        seen_structs: Set[str] = set()
        seen_funcs: Set[str] = set()

        for module in ordered_modules:
            for struct in module.program.structs:
                if struct.name in seen_structs:
                    self.issues.append(LintIssue(f"Struct '{struct.name}' já existe no escopo após imports."))
                    continue
                seen_structs.add(struct.name)
                imported_structs.append(struct)
            for func in module.program.funcs:
                if func.name in seen_funcs:
                    self.issues.append(LintIssue(f"Função '{func.name}' já existe no escopo após imports."))
                    continue
                seen_funcs.add(func.name)
                imported_funcs.append(func)

        for struct in main_program.structs:
            if struct.name in seen_structs:
                self.issues.append(LintIssue(f"Struct '{struct.name}' já existe no escopo após imports."))

        for func in main_program.funcs:
            if func.name in seen_funcs:
                self.issues.append(LintIssue(f"Função '{func.name}' já existe no escopo após imports."))

        merged = Program(
            imports=main_program.imports,
            structs=imported_structs + main_program.structs,
            decls=main_program.decls,
            body=main_program.body,
            funcs=imported_funcs + main_program.funcs,
        )
        return merged, self.issues

    def _load_module(self, module_name: str, loading_stack: List[str], ordered_modules: List[LoadedModule]) -> None:
        if module_name in self.modules:
            return

        if module_name in loading_stack:
            cycle = " -> ".join(loading_stack + [module_name])
            self.issues.append(LintIssue(f"Import circular detectado: {cycle}"))
            return

        path = self.root_dir / Path(*module_name.split("."))
        path = path.with_suffix(".mint")
        if not path.exists():
            self.issues.append(LintIssue(f"Módulo '{module_name}' não encontrado."))
            return

        loading_stack.append(module_name)
        program = self._parse_file(path)
        if program is not None:
            for imp in program.imports:
                self._load_module(imp.module_path, loading_stack, ordered_modules)
            loaded = LoadedModule(name=module_name, path=path, program=program)
            self.modules[module_name] = loaded
            ordered_modules.append(loaded)
        loading_stack.pop()

    def _parse_file(self, path: Path) -> Program | None:
        try:
            source = path.read_text(encoding="utf-8")
            tokens = Lexer(source).tokenize()
            self._validate_import_position(tokens)
            return Parser(tokens).parse()
        except MintError as e:
            self.issues.append(LintIssue(f"{path}: {e}"))
            return None

    def _validate_import_position(self, tokens: List[Token]) -> None:
        locked = False
        for token in tokens:
            if token.type == TokenType.EOF:
                break
            if token.type == TokenType.IMPORT:
                if locked:
                    self.issues.append(LintIssue("IMPORT deve aparecer apenas no topo do arquivo."))
                continue
            if token.type in (TokenType.PROGRAM, TokenType.STRUCT, TokenType.FUNC):
                locked = True
