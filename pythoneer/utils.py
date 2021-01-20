import ast
from types import CodeType


from pythoneer.exception import PythoneerException


class NotAnExpression(PythoneerException):
    pass


def parse_expr(string: str) -> ast.expr:
    """
    Parse a Python expression and return a AST node corresponding to that
    expression.

    >>> expr = parse_expr('a < b')
    >>> type(expr)
    <class '_ast.Compare'>

    If the string is not a Python expression, raise NotAnExpression error.

    >>> parse_expr('a = b')  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    utils.NotAnExpression: ... 'a = b'
    """
    mod = ast.parse(string)
    stmt = mod.body[0]
    if isinstance(stmt, ast.Expr):
        return stmt.value
    else:
        raise NotAnExpression(f"Failed to parse expression {repr(string)}")


def compile_stmt(stmt: ast.stmt) -> CodeType:
    """
    Compile a AST statement in 'exec' mode.

    >>> ns = {}
    >>> stmt = ast.parse("a = 1 + 1").body[0]
    >>> exec(compile_stmt(stmt), ns)
    >>> ns['a']
    2
    """
    mod = ast.Module(body=[stmt],type_ignores=[])
    ast.fix_missing_locations(mod)
    return compile(mod, "<generated>", mode="exec")


def compile_expr(expr: ast.expr) -> CodeType:
    """
    Compile an AST expression in mode "eval".

    >>> eval(compile_expr(parse_expr("1 + 1")))
    2
    """
    mod = ast.Expression(body=expr)
    ast.fix_missing_locations(mod)
    return compile(mod, "<generated>", mode="eval")
