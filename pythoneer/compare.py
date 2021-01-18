import ast
from typing import List, Union, Tuple
from itertools import combinations

from pythoneer.expression import AnnotatedExpression
from pythoneer.context import Context


CompareOperator = Union[
    ast.Eq,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.Is,
    ast.IsNot,
    ast.Lt,
    ast.LtE,
    ast.NotEq,
    ast.NotIn,
]


class CompareExpressions:
    """
    Generate compare operations for all 2-combinations of expressions.
    """

    def __init__(
        self,
        expressions: List[AnnotatedExpression],
        operators: Tuple[CompareOperator] = (ast.Eq, ast.Gt, ast.GtE),
    ):
        self.expressions = expressions
        self.operators = operators

    @classmethod
    def from_context(cls, context: Context):
        return cls(context.expressions)

    def __iter__(self) -> ast.Compare:
        operators = self.operators
        for left, right in combinations(self.expressions, 2):
            for operator in operators:
                yield ast.Compare(left=left, ops=[operator()], comparators=[right])
