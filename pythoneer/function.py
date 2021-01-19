import ast
from collections import deque
from typing import Iterator, List, TypeVar

import astor

from pythoneer.path import ASTPath


F = TypeVar("F", bound="Function")


class Function:
    """
    A Function holds a function AST with additional information on its path.
    On top of that it maintains metrics such as complexity and nesting_level.
    """

    def __init__(
        self, function: ast.FunctionDef, nesting: int = 0, complexity: int = 0
    ):
        self.function = function
        self.nesting = nesting
        self.complexity = complexity
        self.function.path = ASTPath()

    def ellipsis_nodes(self) -> ast.stmt:
        """
        Traversing the program AST in breadth-first order and yielding all
        Ellipsis statements.

        >>> f = ast.parse('''
        ... def x():
        ...    if a:
        ...        ...
        ...    else:
        ...        ...
        ... ''')
        >>> len(list(Function(f.body[0]).ellipsis_nodes()))
        2
        """
        nodes = deque([self.function])
        while nodes:
            node = nodes.popleft()
            for statement in self.child_nodes_with_path(node):
                if (
                    type(statement) == ast.Expr
                    and type(statement.value) == ast.Ellipsis
                ):
                    yield statement
                else:
                    nodes.append(statement)

    def child_nodes_with_path(self, node: ast.AST) -> Iterator[ast.stmt]:
        for statement_attr in ["body", "orelse", "finalbody"]:
            for i, statement in enumerate(getattr(node, statement_attr, [])):
                statement.path = node.path.append((statement_attr, i))
                yield statement

    def replace(self, old_statement: ast.stmt, new_statement: ast.stmt) -> F:
        path: ASTPath = old_statement.path
        new_function = path.replace(self.function, new_statement)
        new_nesting = self.nesting
        new_complexity = self.complexity
        if type(new_statement) == ast.If:
            new_complexity += 2
        elif type(new_statement) == ast.For:
            new_nesting += 1
            new_complexity += 2
        return Function(
            function=new_function,
            nesting=new_nesting,
            complexity=new_complexity,
        )

    def insert_return(self, stmt: ast.stmt, index: int = 0) -> "Function":
        stmt.path = self.function.path.append("body", index)
        self.body.insert(stmt, index)
        return self.function

    @property
    def body(self) -> List[ast.stmt]:
        return self.function.body

    def to_source(self) -> str:
        return astor.to_source(self.function)
