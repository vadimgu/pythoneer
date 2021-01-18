import ast
from typing import Iterator, Iterable

from pythoneer.annotation import TypeAnnotation
from pythoneer.expression import AnnotatedExpression


class ReturnValue:
    def __init__(self, annotation: TypeAnnotation):
        self.annotation = annotation

    @classmethod
    def from_funcdef(cls, funcdef):
        return cls(funcdef.returns)

    @property
    def id(self) -> str:
        return "rvalue"

    def initialization(self, value=None) -> ast.stmt:
        """
        rvalue: Type
        """
        return ast.AnnAssign(
            target=ast.Name(id=self.id, ctx=ast.Store()),
            annotation=self.annotation.expr,
            value=value,
            simple=1,
        )

    def assigns(self, exprs: Iterable[AnnotatedExpression]) -> Iterator[ast.stmt]:
        for expr in exprs:
            if type(expr.expr) == ast.Name and expr.expr.id == self.id:
                continue
            if expr.annotation == self.annotation:
                simple = 0
                if type(expr.expr) == ast.Name:
                    simple = 1
                yield ast.AnnAssign(
                    target=ast.Name(id=self.id, ctx=ast.Store()),
                    value=expr.expr,
                    annotation=self.annotation.expr,
                    simple=simple,
                )

    def name_expr(self) -> ast.Name:
        return ast.Name(id=self.id, ctx=ast.Load())

    def return_statement(self) -> ast.Return:
        return ast.Return(value=self.name_expr())

    def ann_name_expr(self) -> AnnotatedExpression:
        return AnnotatedExpression(
            expr=self.name_expr(),
            annotation=self.annotation,
        )


class ListReturnValue(ReturnValue):
    def initialization(self) -> ast.stmt:
        return ast.Assign(
            targets=[ast.Name(id=self.id, ctx=ast.Store())],
            value=ast.List(elts=[], ctx=ast.Load()),
        )

    def assigns(self, exprs: Iterable[AnnotatedExpression]) -> Iterator[ast.stmt]:
        """
        ...
        """
        for expr in exprs:
            if expr.annotation == self.annotation.slice:
                yield ast.Expr(
                    ast.Call(
                        func=ast.Attribute(
                            value=self.name_expr(), attr="append", ctx=ast.Load()
                        ),
                        args=[expr.expr],
                        keywords=[],
                    )
                )