import ast
from typing import List


class ConditionStatements:
    def __init__(self, boolean_expressions: List[ast.expr]):
        self.boolean_expressions = boolean_expressions

    def __iter__(self) -> ast.If:
        for exp in self.boolean_expressions:
            yield ast.If(
                test=exp,
                body=[ast.Expr(value=ast.Ellipsis())],
                orelse=[ast.Expr(value=ast.Ellipsis())],
            )