import ast
from typing import List, Union


class BooleanExpressionProgrammer:
    """
    Generate all possible boolean expressions for a list of boolean expresions.

    This gives us 2^(2^n) boolean expressions where `n` is the size of `booleans`.
    """

    def __init__(self, booleans: List[Union[ast.Name, ast.BoolOp, ast.Compare]]):
        self.booleans = booleans

    def __iter__(self):
        for bool_expr in self.boolean_expressions():
            yield bool_expr

    def minterms(self):
        n = 2 ** len(self.booleans)
        for i in range(n):
            values = []
            for j, boolean_value in enumerate(self.booleans):
                if (i >> j) % 2 == 1:
                    values.append(ast.UnaryOp(op=ast.Not(), operand=boolean_value))
                else:
                    values.append(boolean_value)
            yield ast.BoolOp(op=ast.And(), values=values)

    def boolean_expressions(self):
        minterms = list(self.minterms())
        for i in range(2 ** len(minterms)):
            terms = []
            for j, minterm in enumerate(minterms):
                if (i >> j) % 2 == 1:
                    terms.append(minterm)
            if len(terms) == 0:
                continue
            if len(terms) == 1:
                yield terms[0]
            else:
                yield ast.BoolOp(op=ast.Or(), values=terms)
