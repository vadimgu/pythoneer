import ast
from typing import List, Union

ASTOperator = Union[
    ast.Add,
    ast.BitAnd,
    ast.BitOr,
    ast.BitXor,
    ast.Div,
    ast.FloorDiv,
    ast.LShift,
    ast.MatMult,
    ast.Mod,
    ast.Mult,
    ast.Pow,
    ast.RShift,
    ast.Sub,
]


class BinaryOperators:
    pass


def exprs(a, b):
    yield f"({a} + {b})"
    yield f"({a} - {b})"
    yield f"({b} - {a})"
    yield f"({a} * {b})"
    yield f"({a} // {b})"
    yield f"({a} >> {b})"
    yield f"({a} ** {b})"
    yield f"({b} ** {a})"


class BinaryOperationExpressions:
    """
    Generate all possible binary operation expressions for a list of expressions.

    Add, Sub, Mult, FloorDiv, Mod, Pow

    Constant operations on each variable
    expr('a', Constant('1'), Constant('2'))
    n1 = a + 1
    n2 = a - 1
    n3 = a + 2
    n4 = a - 2
    n5 = a * 2
    n6 = a // 2
    n7 = a ** 2
    n8 = 2 ** a
    n7 = a ** 2
    n8 = 2 ** a
    nx = a * b
    """

    def __init__(self, operands, operators=("+", "-", "*", "//")):
        self.operands = operands
        self.operators = operators

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