import ast
from types import CodeType


def compile_stmt(stmt: ast.stmt) -> CodeType:
    """
    >>> ns = {}
    >>> exec(compile_expr(ast.parse("a = 1 + 1")), ns)
    >>> ns.keys()
    2
    """
    mod = ast.Module(body=[stmt])
    ast.fix_missing_locations(mod)
    return compile(mod, "<generated>", mode="exec")


def compile_expr(expr: ast.expr) -> CodeType:
    """
    >>> eval(compile_expr(ast.parse("1 + 1").body[0].value))
    2
    """
    mod = ast.Expression(body=expr)
    # ast.fix_missing_locations(expr)
    ast.fix_missing_locations(mod)
    return compile(mod, "<generated>", mode="eval")
