import ast
from itertools import combinations, permutations, product
from typing import (
    Iterator,
    Callable,
    List,
    Mapping,
    Set,
    Type,
)

from pythoneer.context import Context
from pythoneer.expression import AnnotatedExpression
from pythoneer.annotation import TypeAnnotation


class ExpressionSpace:
    """
    The ExpressionSpace build new expressions based on a context. It can be
    configured by setting the operations it can use when generating new
    expressions.
    """

    binary_operators: List[Type[ast.operator]]
    compare_operators: List[Type[ast.cmpop]]
    unary_operators: List[Type[ast.unaryop]]

    cummitative_operator_set: Set[Type[ast.operator]] = {
        ast.Add,
        ast.Mult,
        ast.BitAnd,
        ast.BitOr,
        ast.BitXor,
    }

    def __init__(
        self,
        binary_operators: List[Type[ast.operator]] = [],
        compare_operators: List[Type[ast.cmpop]] = [ast.Eq],
        unary_operators: List[Type[ast.unaryop]] = [],
        expression_levels: int = 1,
    ):
        self.binary_operators = binary_operators
        self.compare_operators = compare_operators
        self.unary_operators = unary_operators
        self.expression_levels = expression_levels

    def enrich_context(self, ctx: Context) -> Context:
        """
        Makes a new context with new expressions.

        By default only using a comparison operator "==".

        >>> ctx = Context.parse([], {'a': 'int', 'b': 'int'}, {})
        >>> print(ctx)
        expressions: {
            <class 'int'>: ['a', 'b'],
        }
        >>> p = ExpressionSpace()
        >>> print(p.enrich_context(ctx))
        expressions: {
            <class 'int'>: ['a', 'b'],
            <class 'bool'>: ['(a == b)'],
        }

        A more complexe example. Functions are applied after operations.

        >>> from math import factorial
        >>> ctx = Context.parse([], {'n': 'int', 'k': 'int', 'factorial': 'Callable[[int],int]'}, globals())
        >>> p = ExpressionSpace(
        ...    unary_operators=[],
        ...    compare_operators=[],
        ...    binary_operators=[ast.Sub, ast.FloorDiv],
        ...    expression_levels=1,
        ... )
        >>> p.compare_operators
        []
        >>> new_ctx = p.enrich_context(ctx)
        >>> print([expr.to_source() for expr in new_ctx.expressions_by_type(int)])  # doctest: +ELLIPSIS
        [...'factorial(n - k)'...]

        """
        new_ctx = Context(ctx.expressions[:], ctx.namespace)
        for _ in range(self.expression_levels):
            new_ctx.extend(list(self.properties(new_ctx)))
            new_ctx.extend(list(self.unary_ops(new_ctx)))
            new_ctx.extend(list(self.binary_ops(new_ctx)))
            new_ctx.extend(list(self.calls(new_ctx)))
            new_ctx.extend(list(self.comparisons(new_ctx)))
            new_ctx.extend(list(self.bool_ops(new_ctx)))
        return new_ctx

    def properties(self, ctx: Context) -> Iterator[AnnotatedExpression]:
        """
        Return all properties expressions for "self" if it's found.
        """
        if "self" in ctx.namespace:
            self_expr = ctx.namespace["self"]
            if hasattr(self_expr.annotation.type, "__annotations__"):
                class_annotations = (
                    self_expr.annotation.type.__annotations__
                )  # type: Mapping[str,Type]
                for attr_name, attr_type in class_annotations.items():
                    yield AnnotatedExpression(
                        ast.Attribute(
                            value=ast.Name(id="self", ctx=ast.Load()),
                            attr=attr_name,
                            ctx=ast.Load(),
                        ),
                        TypeAnnotation(attr_type, None),
                    )

    @property
    def commutative_operators(self) -> List[Type[ast.operator]]:
        """
        A list of commutative (order independed) operators for that instance.

        >>> p = ExpressionSpace(binary_operators=[ast.Add, ast.Sub, ast.Mult, ast.Div])
        >>> p.commutative_operators
        [<class '_ast.Add'>, <class '_ast.Mult'>]
        """
        return [
            op for op in self.binary_operators if op in self.cummitative_operator_set
        ]

    @property
    def non_commutative_operators(self) -> List[Type[ast.operator]]:
        """
        A list of non commutative (order dependent) binary operators for that instance.

        >>> p = ExpressionSpace(binary_operators=[ast.Add, ast.Sub, ast.Mult, ast.Div])
        >>> p.non_commutative_operators
        [<class '_ast.Sub'>, <class '_ast.Div'>]
        """
        return [
            op
            for op in self.binary_operators
            if op not in self.cummitative_operator_set
        ]

    def unary_ops(self, ctx: Context) -> Iterator[AnnotatedExpression]:
        """
        Return all unary operation expression.

        >>> ctx = Context.parse([], {'a': 'int', 'b': 'int'}, {})
        >>> p = ExpressionSpace(unary_operators=[ast.USub])
        >>> for expr in p.unary_ops(ctx):
        ...    print(expr.to_source())
        (-a)
        (-b)
        """
        # TODO: extend to all types
        exprs = ctx.expressions_by_type(int)
        for expr in exprs:
            for unary_operator in self.unary_operators:
                yield AnnotatedExpression(
                    ast.UnaryOp(op=unary_operator(), operand=expr.expr),
                    TypeAnnotation(int),
                )

    def binary_ops(self, ctx: Context) -> Iterator[AnnotatedExpression]:
        """
        Generate binary operations such as "+" or "-" for all pairs of compatible expressions.

        >>> ctx = Context.parse([], {'a': 'int', 'b': 'int', 'x': 'float', 'y': 'float'}, {})
        >>> p = ExpressionSpace(binary_operators=[ast.Add, ast.Sub])
        >>> for expr in p.binary_ops(ctx):
        ...    print(expr.to_source())
        (a + b)
        (a - b)
        (b - a)
        (x + y)
        (x - y)
        (y - x)
        """
        for type, expr_group in ctx.groupby_type():
            if type in (bool, Callable):
                continue
            # TODO: Allow tuple comparisons?
            if TypeAnnotation(type).iterable:
                continue

            for commutative_operator in self.commutative_operators:
                for left, right in combinations(expr_group, 2):
                    yield AnnotatedExpression(
                        ast.BinOp(
                            left=left.expr, op=commutative_operator(), right=right.expr
                        ),
                        TypeAnnotation(type),
                    )
            for dependent_operator in self.non_commutative_operators:
                for left, right in permutations(expr_group, 2):
                    yield AnnotatedExpression(
                        ast.BinOp(
                            left=left.expr, op=dependent_operator(), right=right.expr
                        ),
                        TypeAnnotation(type),
                    )

    def calls(self, ctx: Context) -> Iterator[AnnotatedExpression]:
        """
        Return first level callables.
        >>> from typing import Callable
        >>> ctx = Context.parse([], {'a': 'int', 'b': 'int', 'pow': 'Callable[[int, int], int]'}, globals())
        >>> p = ExpressionSpace()
        >>> for expr in p.calls(ctx):
        ...    print(expr.to_source())
        pow(a, a)
        pow(a, b)
        pow(b, a)
        pow(b, b)

        >>> ctx = Context.parse([], {'a': 'bool', 'b': 'bool', 'i': 'int', 'f': 'Callable[[bool, int, bool], int]'}, globals())
        >>> p = ExpressionSpace()
        >>> for expr in p.calls(ctx):
        ...    print(expr.to_source())
        f(a, i, a)
        f(a, i, b)
        f(b, i, a)
        f(b, i, b)
        """
        exprs_by_type = dict(ctx.groupby_type())
        for callable in ctx.callables():
            type_matchd_args = [
                exprs_by_type[arg.type] for arg in callable.annotation.callable_args
            ]
            for exprs_for_args in product(*type_matchd_args):
                call_expression = AnnotatedExpression(
                    ast.Call(
                        func=callable.expr,
                        args=[expr.expr for expr in exprs_for_args],
                        keywords=[],
                    ),
                    callable.annotation.callable_returns,
                )
                yield call_expression

    def bool_ops(self, ctx: Context) -> Iterator[AnnotatedExpression]:
        """
        Generate boolean operations for all pairs of boolean expressions.

        >>> ctx = Context.parse([('(i<j)', 'bool')], {'a': 'bool', 'b': 'bool'}, {})
        >>> p = ExpressionSpace()
        >>> for expr in p.bool_ops(ctx):
        ...    print(expr.to_source())
        (a and b)
        (a or b)
        (a and i < j)
        (a or i < j)
        (b and i < j)
        (b or i < j)
        """
        for left, right in combinations(ctx.expressions_by_type(bool), 2):
            yield AnnotatedExpression(
                ast.BoolOp(op=ast.And(), values=[left.expr, right.expr]),
                TypeAnnotation(bool),
            )
            yield AnnotatedExpression(
                ast.BoolOp(op=ast.Or(), values=[left.expr, right.expr]),
                TypeAnnotation(bool),
            )

    def comparisons(self, ctx: Context) -> Iterator[AnnotatedExpression]:
        """

        Generate comparison for all combinations for comparable types.

        >>> ctx = Context.parse([], {'a': 'int', 'b': 'int'}, {})
        >>> p = ExpressionSpace(compare_operators=[ast.Lt, ast.Eq])
        >>> for expr in p.comparisons(ctx):
        ...    print(expr.to_source())
        (a < b)
        (a == b)
        """
        for type, expr_group in ctx.groupby_type():
            if type in (bool, Callable):
                continue
            for operator in self.compare_operators:
                for left, right in combinations(expr_group, 2):
                    yield AnnotatedExpression(
                        ast.Compare(
                            left=left.expr, ops=[operator()], comparators=[right.expr]
                        ),
                        TypeAnnotation(bool),
                    )
