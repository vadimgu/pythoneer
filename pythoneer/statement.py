import ast

from pythoneer.context import Context


class Statement:
    def __init__(self, stmt: ast.stmt, context: Context):
        self._stmt = stmt
        self.context = context

    @property
    def stmt(self) -> ast.stmt:
        """
        A decorated `ast` statement with attribute `context`. It can be used as
        a regular `ast` statement.

        >>> ctx = Context([], {})
        >>> Statement(ast.For(), ctx).stmt.context == ctx
        True
        """
        self._stmt.context = self.context
        return self._stmt
