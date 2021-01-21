import ast
from typing import Type, NamedTuple

import astor

from pythoneer.annotation import TypeAnnotation
from pythoneer.utils import parse_expr


class AnnotatedExpression:
    """
    A AnnotatedExpression wraps a ast.expr instance with a type information.
    """

    def __init__(self, expr: ast.expr, annotation: TypeAnnotation):
        self.expr = expr
        self.annotation = annotation

    def __str__(self):
        return (
            f"<AnnotatedExpression({repr(self.to_source())}, {self.annotation.type})>"
        )

    @classmethod
    def parse(cls, expr: str, annotation: str, globals: dict):
        """
        Parse an expression `expr` with an `annotation` as strings.

        >>> expr = AnnotatedExpression.parse('a == b', 'int', {})
        >>> expr.annotation.type
        <class 'int'>

        Pass the globals namespace in the globals parameters.

        >>> from typing import List
        >>> expr = AnnotatedExpression.parse('a + b', 'List[int]', globals())
        >>> expr.annotation.type
        typing.List[int]
        """
        return cls(
            parse_expr(expr),
            TypeAnnotation.parse(annotation, globals),
        )

    @classmethod
    def from_arg(cls, arg: ast.arg, namespace: dict = {}):
        assert arg.annotation is not None
        return cls(
            expr=ast.Name(id=arg.arg, ctx=ast.Load()),
            annotation=TypeAnnotation.from_ast(arg.annotation, namespace),
        )

    @classmethod
    def from_annassign(cls, stmt: ast.AnnAssign, namespace: dict = {}):
        assert isinstance(stmt.target, ast.Name)
        return cls(
            expr=ast.Name(id=stmt.target.id, ctx=ast.Load()),
            annotation=TypeAnnotation.from_ast(stmt.annotation, namespace),
        )

    def to_source(self):
        """
        >>> expr = AnnotatedExpression.parse('a > b', 'bool', {})
        >>> expr.to_source()
        '(a > b)'
        """
        return astor.to_source(self.expr).strip()