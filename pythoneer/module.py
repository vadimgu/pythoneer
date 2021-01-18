import ast
from typing import Iterator, TextIO
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

        >>> import ast
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
        <module.Module ...>
        """
        globals = {}
        source_ast = ast.parse(source)
        code = compile(source_ast, filename, mode="exec")
        exec(code, globals)
        return cls(source_ast, filename, globals)

    @classmethod
    def from_stream(cls, stream: TextIO, filename: str):
        """
        Make a Module instance from a source string.

        >>> from io import StringIO
        >>> Module.from_stream(StringIO(''), '<test>') # doctest: +ELLIPSIS
        <module.Module ...>
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
            if type(stmt) == ast.FunctionDef:
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
        >>> m.find_function('x')  # doctest: +ELLIPSIS
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
                if type(module_stmt) == ast.ClassDef and module_stmt.name == class_name:
                    for class_def_stmt in module_stmt.body:
                        if (
                            type(class_def_stmt) == ast.FunctionDef
                            and class_def_stmt.name == method_name
                        ):
                            return class_def_stmt
        raise NameNotFound(f"The name {name} was not found in {self.filename}.")

    def replace_node(self, name: str, function: Function) -> ast.Module:
        """
        Return a module where the node referenced by `path` is set to `ast_node`.

        >>> import ast
        >>> m = Module.from_string('def x() -> int: pass', '<test>')
        >>> new_f = ast.parse('def y() -> int: pass').body[0]
        >>> mod = m.replace_node('x', new_f)
        >>> mod.body[0].name
        'y'

        The same can be done with a class method.

        >>> m = Module.from_string('''
        ... class A:
        ...     def x() -> int:
        ...         pass
        ... ''', '<test>')
        >>> new_f = ast.parse('def y() -> int: pass').body[0]
        >>> mod = m.replace_node('A.x', new_f)
        >>> mod.body[0].body[0].name
        'y'
        """
        parts = name.split(".")

        if len(parts) == 1:
            for i, stmt in enumerate(self.module_ast.body):
                if isinstance(stmt, ast.FunctionDef) and stmt.name == name:
                    self.module_ast.body[i] = function.function
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
                            stmt.body[i] = function.function
                            return self.module_ast
        raise NameNotFound(f"The name {name} was not found in {self.filename}.")

    def compile(self) -> CodeType:
        mod = self.module_ast
        # print(astor.dump_tree(mod))
        ast.fix_missing_locations(mod)
        return compile(mod, self.filename, "exec")
