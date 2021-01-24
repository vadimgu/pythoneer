import ast
from typing import Iterator, TextIO, Dict, Any, List
from types import CodeType

import astor

from pythoneer.function import Function


class ModuleError(Exception):
    pass


class NameNotFound(ModuleError):
    pass


class Module:
    def __init__(self, module_ast: ast.Module, filename: str, globals: dict):
        self.module_ast = module_ast
        self.filename = filename
        self.globals = globals

    def to_source(self) -> str:
        """
        Transform the Module instance back into source code.

        >>> m = Module(ast.parse("a=1"), '<test>', {})
        >>> bool(ast.parse(m.to_source()))
        True
        """
        return astor.to_source(self.module_ast)

    @classmethod
    def from_string(cls, source: str, filename: str):
        """
        Make a Module instance from a source string.

        >>> Module.from_string('', '<test>') # doctest: +ELLIPSIS
        <....Module ...>
        """
        globals = {}  # type: Dict[str, Any]
        source_ast = ast.parse(source, type_comments=True)
        code = compile(source_ast, filename, mode="exec")
        exec(code, globals)
        return cls(source_ast, filename, globals)

    @classmethod
    def from_stream(cls, stream: TextIO, filename: str):
        """
        Make a Module instance from a source string.

        >>> from io import StringIO
        >>> Module.from_stream(StringIO(''), '<test>') # doctest: +ELLIPSIS
        <....Module ...>
        """
        return cls.from_string(stream.read(), filename)

    def functions(self) -> Iterator[ast.FunctionDef]:
        """
        Yields all fisrt level FunctionDef statements.

        >>> m = Module.from_string('''
        ... def x():
        ...     pass
        ... def y():
        ...     pass
        ... ''', '<test>')
        >>> functions = list(m.functions())
        >>> len(functions)
        2
        """
        for stmt in self.module_ast.body:
            if isinstance(stmt, ast.FunctionDef):
                yield stmt

    def find_function(self, name: str) -> ast.FunctionDef:
        """
        >>> m = Module.from_string('''
        ... def x():
        ...     pass
        ... def y():
        ...     pass
        ... ''', '<test>')
        >>> m.find_function('x').name
        'x'

        It's also possible to locate a class method.

        >>> m = Module.from_string('''
        ... class A:
        ...     def x() -> int:
        ...         pass
        ... def y() -> int:
        ...     pass
        ... ''', '<test>')
        >>> m.find_function('A.x').name
        'x'

        If the `name` cannot be found raise `NameNotFound`.

        >>> m = Module.from_string('', '<test>')
        >>> m.find_function('x')  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        module.NameNotFound: ... x ... <test>...
        """
        parts = name.split(".")
        if len(parts) == 1:
            for funcdef in self.functions():
                if funcdef.name == name:
                    return funcdef
        elif len(parts) == 2:
            class_name, method_name = parts
            for module_stmt in self.module_ast.body:
                if (
                    isinstance(module_stmt, ast.ClassDef)
                    and module_stmt.name == class_name
                ):
                    for class_def_stmt in module_stmt.body:
                        if (
                            isinstance(class_def_stmt, ast.FunctionDef)
                            and class_def_stmt.name == method_name
                        ):
                            return class_def_stmt
        raise NameNotFound(f"The name {name} was not found in {self.filename}.")

    def replace_stmts(self, name: str, stmts: List[ast.stmt]) -> ast.Module:
        """
        Modify the module's AST. Set the body of function referenced by
        `name` to a new seatements list `stmts`.

        >>> m = Module.from_string('def x() -> int: pass', '<test>')
        >>> new_stmts = [ast.Return(value=ast.Name(id='a', ctx=ast.Load()))]
        >>> mod = m.replace_stmts('x', new_stmts)
        >>> ast.dump(mod.body[0])  # doctest: +ELLIPSIS
        "FunctionDef(name='x',... body=[Return(value=Name(id='a', ctx=Load()))]...)"

        The same can be done with a class method.

        >>> m = Module.from_string('''
        ... class A:
        ...     def x(self) -> int:
        ...         pass
        ... ''', '<test>')
        >>> new_stmts = [ast.Return(value=ast.Name(id='a', ctx=ast.Load()))]
        >>> mod = m.replace_stmts('A.x', new_stmts)
        >>> ast.dump(mod.body[0])  # doctest: +ELLIPSIS
        "ClassDef(name='A',... body=[FunctionDef(name='x',... body=[Return(value=Name(id='a', ctx=Load()))]...)]...)"

        """
        parts = name.split(".")

        if len(parts) == 1:
            for i, stmt in enumerate(self.module_ast.body):
                if isinstance(stmt, ast.FunctionDef) and stmt.name == name:
                    stmt.body = stmts
                    return self.module_ast
        elif len(parts) == 2:
            class_name, method_name = parts
            for stmt in self.module_ast.body:
                if isinstance(stmt, ast.ClassDef) and stmt.name == class_name:
                    for i, cls_stmt in enumerate(stmt.body):
                        if (
                            isinstance(cls_stmt, ast.FunctionDef)
                            and cls_stmt.name == method_name
                        ):
                            cls_stmt.body = stmts
                            return self.module_ast
        raise NameNotFound(f"The name {name} was not found in {self.filename}.")

    def compile(self) -> CodeType:
        mod = self.module_ast
        ast.fix_missing_locations(mod)
        return compile(mod, self.filename, "exec")
