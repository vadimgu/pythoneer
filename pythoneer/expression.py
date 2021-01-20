import ast

import astor

from pythoneer.annotation import TypeAnnotation


class AnnotatedExpression:
    """
    A AnnotatedExpression wraps a ast.expr instance with a type information.
    """

    def __init__(self, expr: ast.expr, annotation: TypeAnnotation):
        self.expr = expr
        self.annotation = annotation

    def __str__(self):
        return f"<AnnotatedExpression({repr(self.to_source())}, {repr(astor.to_source(self.annotation.expr).strip())})>"

    @classmethod
    def parse(cls, expr: str, annotation: str, globals: dict):
        """
        Parse an expression `expr` with an `annotation` as strings.

        >>> expr = AnnotatedExpression.parse('a = b', 'int', {})
        >>> expr.annotation.type
        <class 'int'>

        Pass the globals namespace in the globals parameters.

        >>> from typing import List
        >>> expr = AnnotatedExpression.parse('a + b', 'List[int]', globals())
        >>> expr.annotation.type
        typing.List[int]
        """
        return cls(
            ast.parse(expr).body[0].value,
            TypeAnnotation(
                ast.parse(annotation).body[0].value,
                globals,
            ),
        )

    @classmethod
    def from_arg(cls, arg: ast.arg, namespace: dict = {}):
        return cls(
            expr=ast.Name(id=arg.arg, ctx=ast.Load()),
            annotation=TypeAnnotation(arg.annotation, namespace),
        )

    @classmethod
    def from_annassign(cls, stmt: ast.AnnAssign, namespace: dict = {}):
        return cls(
            expr=ast.Name(id=stmt.target.id, ctx=ast.Load()),
            annotation=TypeAnnotation(stmt.annotation, namespace),
        )

    def to_source(self):
        """
        >>> expr = AnnotatedExpression.parse('a > b', 'bool', {})
        >>> expr.to_source()
        '(a > b)'
        """
        return astor.to_source(self.expr).strip()


class PExpr(ast.Expr):
    """
    PExpr
    """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.x = "hello"

    @classmethod
    def from_ast(cls, expr: ast.Expr):
        """
        >>> expr = ast.parse('...').body[0]
        >>> pexpr = PExpr.from_ast(expr)
        >>> isinstance(pexpr, ast.Expr)
        True
        >>> mod = ast.Module(body=[pexpr], type_ignores=[])
        >>> _ = ast.fix_missing_locations(mod)
        >>> exec(compile(mod, '<>', mode='exec'))


        #>>> astor.to_source(mod)  ## extend: astor.code_gen.SourceGenerator:
        #'source'
        """
        return cls(expr.value)
