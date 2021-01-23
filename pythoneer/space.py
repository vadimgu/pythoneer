"""
This module contains various specialist programmers

- MathematicalProgrammer
- FunctionalProgrammer
- OOProgrammer

"""
import ast
from collections import deque, defaultdict
from itertools import combinations, permutations, product
from typing import (
    Iterator,
    Sequence,
    Callable,
    Deque,
    MutableMapping,
    List,
    Set,
    Type,
)

from pythoneer.context import Context
from pythoneer.expression import AnnotatedExpression
from pythoneer.annotation import TypeAnnotation


class ProgramSpace:
    def expressions(self, context: Context) -> Iterator[AnnotatedExpression]:
        ...

    def statements(self, context: Context) -> Iterator[ast.stmt]:
        ...


class NaiveProgrammer:
    """
    Attributes > Functions > Operations > Comparisons > BooleanExpressions
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

    @property
    def commutative_operators(self) -> List[Type[ast.operator]]:
        """
        A list of commutative (order independed) operators for that instance.

        >>> p = NaiveProgrammer(binary_operators=[ast.Add, ast.Sub, ast.Mult, ast.Div])
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

        >>> p = NaiveProgrammer(binary_operators=[ast.Add, ast.Sub, ast.Mult, ast.Div])
        >>> p.non_commutative_operators
        [<class '_ast.Sub'>, <class '_ast.Div'>]
        """
        return [
            op
            for op in self.binary_operators
            if op not in self.cummitative_operator_set
        ]

    def enrich_context(self, ctx: Context) -> Context:
        """
        Makes a new context with new expressions.

        By default only using a comparison operator "==".

        >>> ctx = Context.parse([], {'a': 'int', 'b': 'int'}, {})
        >>> print(ctx)
        expressions: {
            <class 'int'>: ['a', 'b'],
        }
        >>> p = NaiveProgrammer()
        >>> print(p.enrich_context(ctx))
        expressions: {
            <class 'int'>: ['a', 'b'],
            <class 'bool'>: ['(a == b)'],
        }

        A more complexe example:

        >>> from math import factorial
        >>> ctx = Context.parse([], {'n': 'int', 'k': 'int', 'factorial': 'Callable[[int],int]'}, globals())
        >>> p = NaiveProgrammer(
        ...    unary_operators=[],
        ...    compare_operators=[],
        ...    binary_operators=[ast.Sub, ast.FloorDiv],
        ...    expression_levels=2,
        ... )
        >>> p.compare_operators
        []
        >>> new_ctx = p.enrich_context(ctx)
        >>> print([expr.to_source() for expr in new_ctx.expressions_by_type(int)])  # doctest: +ELLIPSIS
        [...'n // factorial(n - k)'...

        """
        new_ctx = Context(ctx.expressions[:], ctx.namespace)
        for _ in range(self.expression_levels):
            new_ctx.extend(list(self.unary_ops(new_ctx)))
            new_ctx.extend(list(self.binary_ops(new_ctx)))
            new_ctx.extend(list(self.calls(new_ctx)))
            new_ctx.extend(list(self.comparisons(new_ctx)))
            new_ctx.extend(list(self.bool_ops(new_ctx)))
        return new_ctx

    def unary_ops(self, ctx: Context) -> Iterator[AnnotatedExpression]:
        """
        Return all unary operation expression.

        >>> ctx = Context.parse([], {'a': 'int', 'b': 'int'}, {})
        >>> p = NaiveProgrammer(unary_operators=[ast.USub])
        >>> for expr in p.unary_ops(ctx):
        ...    print(expr.to_source())
        (-a)
        (-b)

        #  TODO:
        #  Also includes all callables with one argument

        #  >>> from math import factorial
        #  >>> ctx = Context.parse([], {'a', 'int', 'b': 'int', 'factorial': Callable[[int], int]}, globals())
        #  >>> for expr in p.unary_ops(ctx):
        #  ...     print(expr.to_source)
        #  factorial(a)
        #  factorial(b)
        """
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
        >>> p = NaiveProgrammer(binary_operators=[ast.Add, ast.Sub])
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
        >>> p = NaiveProgrammer()
        >>> for expr in p.calls(ctx):
        ...    print(expr.to_source())
        pow(a, a)
        pow(a, b)
        pow(b, a)
        pow(b, b)

        >>> ctx = Context.parse([], {'a': 'bool', 'b': 'bool', 'i': 'int', 'f': 'Callable[[bool, int, bool], int]'}, globals())
        >>> p = NaiveProgrammer()
        >>> for expr in p.calls(ctx):
        ...    print(expr.to_source())
        f(a, i, a)
        f(a, i, b)
        f(b, i, a)
        f(b, i, b)
        """
        exprs_by_type = defaultdict(
            list
        )  # type: MutableMapping[Type, List[AnnotatedExpression]]
        exprs_by_type.update(ctx.groupby_type())
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
        >>> p = NaiveProgrammer()
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
        >>> p = NaiveProgrammer(compare_operators=[ast.Lt, ast.Eq])
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


class BooleanExpressionProgrammer:
    """
    Generate all possible boolean expressions for a list of boolean expresions.

    This gives us 2^(2^n) boolean expressions where `n` is the size of `booleans`.
    """

    def __init__(self):
        pass

    def expressions(self, context: Context) -> Iterator[AnnotatedExpression]:
        """
        Generate all boolean expressions from all boolean expressions and
        variables in `context`.

        >>> ctx = Context.parse([], {'a': 'bool', 'b': 'bool'}, {})
        >>> p = BooleanExpressionProgrammer()
        >>> boolean_expressions = list(p.expressions(ctx))
        >>> [expr.to_source() for expr in boolean_expressions]  # doctest: +ELLIPSIS
        ['(a and b)', '(not a and b)', ...'(a and b or not a and b or a and not b or not a and not b)']

        The number of such boolean expressions will be equal to `2^{2^n}`.
        Where `n` is the number of boolean variables.

        >>> len(boolean_expressions)
        15
        """
        boolean_exprs = list(context.boolean_expressions())
        minterms = list(self.minterms(boolean_exprs))
        for i in range(2 ** len(minterms)):
            terms = []
            for j, minterm in enumerate(minterms):
                if (i >> j) % 2 == 1:
                    terms.append(minterm.expr)
            if len(terms) == 0:
                continue
            if len(terms) == 1:
                yield AnnotatedExpression(terms[0], TypeAnnotation.parse("bool", {}))
            else:
                yield AnnotatedExpression(
                    ast.BoolOp(op=ast.Or(), values=terms),
                    TypeAnnotation.parse("bool", {}),
                )

    def minterms(
        self, boolean_exprs: Sequence[AnnotatedExpression]
    ) -> Iterator[AnnotatedExpression]:
        """
        Generate all minterm (AND operation) expressions

        >>> parse = AnnotatedExpression.parse
        >>> exprs = [parse('a', 'bool', {}), parse('b', 'bool', {})]
        >>> p = BooleanExpressionProgrammer()
        >>> [expr.to_source() for expr in p.minterms(exprs)]
        ['(a and b)', '(not a and b)', '(a and not b)', '(not a and not b)']
        """
        n = 2 ** len(boolean_exprs)
        for i in range(n):
            values = []  # type: List[ast.expr]
            for j, boolean_expr in enumerate(boolean_exprs):
                if (i >> j) % 2 == 1:
                    values.append(ast.UnaryOp(op=ast.Not(), operand=boolean_expr.expr))
                else:
                    values.append(boolean_expr.expr)
            yield AnnotatedExpression(
                ast.BoolOp(op=ast.And(), values=values),
                TypeAnnotation.parse("bool", {}),
            )


class MathematicalSpace:
    """
    Mathematical expressions space includes all operations with binary and unitary operators.
    a + b
    a * b
    -a, -b
    """

    def __init__(self, **options):
        ...

    def expressions(self, context: Context) -> Iterator[AnnotatedExpression]:
        # integers = context.expressions_by_type(int)
        # # negations
        # for expr in integers:
        #     ...

        # # binary operations
        # for a, b in combinations(integers, 2):
        #     a * b
        ...


class FunctionalCompositionSpace:
    """
    Functional composition space

    Using concept like `map` and `sum`
    """

    def __init__(self, **options):
        ...

    def expressions(self, context: Context) -> Iterator[AnnotatedExpression]:
        """
        Build function calls

        >>> from typing import Callable
        >>> from operator import sub
        >>> ctx = Context.parse([], {'sub': 'Callable[[int,int], int]', 'a': 'int', 'b': 'int'}, globals())
        >>> space = FunctionalCompositionSpace()
        >>> for expr in space.expressions(ctx):
        ...     print(expr)
        <AnnotatedExpression('sub(a, a)', <class 'int'>)>
        <AnnotatedExpression('sub(a, b)', <class 'int'>)>
        <AnnotatedExpression('sub(b, a)', <class 'int'>)>
        <AnnotatedExpression('sub(b, b)', <class 'int'>)>
        """
        exprs_by_type = defaultdict(
            list
        )  # type: MutableMapping[Type, List[AnnotatedExpression]]
        exprs_by_type.update(context.groupby_type())

        call_expressions = set()  # type: Set[AnnotatedExpression]

        d = deque()  # type: Deque[AnnotatedExpression]
        for callable in context.callables():
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
                d.append(call_expression)
                call_expressions.add(call_expression)
                exprs_by_type[call_expression.annotation.type].append(call_expression)

        while d:
            call = d.popleft()
            yield call
        #    for arg in call.args:
        #        call_expression = AnnotatedExpression(
        #            ast.Call(
        #                func=call.expr.func,
        #                arts=[...],
        #                keywords=[],
        #            ),
        #            call.annotation,
        #        )
        #        d.append(call_expression)
        #        call_expression.append(call_expression)


class ObjectCompositionSpace:
    """
    Object composition space
    """

    def expressions(self, context: Context) -> Iterator[AnnotatedExpression]:
        """
        Generate annotated expression that build objects.
        """

    def statements(self, context: Context) -> Iterator[ast.stmt]:
        """
        Assignments
        """
        ...


class StructuredProgrammingSpace:
    """
    Structured programming space
    """

    non_comparable_types = (bool, Callable)

    def __init__(self, globals, compare_operators=(ast.Gt,)):
        self.compare_operators = compare_operators
        self.globals = globals

    def expressions(self, context: Context) -> Iterator[AnnotatedExpression]:
        """
        Generate all comparison expressions with self.compare_operators.

        The comparisons are made between objects of the same type.
        """
        for _, expr_group in context.groupby_type(exclude=(bool, Callable)):
            for left, right in combinations(expr_group, 2):
                for operator in self.compare_operators:
                    yield AnnotatedExpression(
                        ast.Compare(
                            left=left.expr, ops=[operator()], comparators=[right.expr]
                        ),
                        TypeAnnotation(bool, None),
                    )

    def statements(self, context: Context) -> Iterator[ast.stmt]:
        yield from self.if_statements(context)
        yield from self.for_statements(context)

    def if_statements(self, context: Context) -> Iterator[ast.stmt]:
        """
        Generate if statements for all boolean expressions
        """
        for bool_expr in context.boolean_expressions():
            yield ast.If(
                test=bool_expr.expr,
                body=[context.ellipsis()],
                orelse=[context.ellipsis()],
            )

    def for_statements(self, context: Context) -> Iterator[ast.stmt]:
        """
        Generate for statements for all iterable expressions
        """
        for iterable in context.iterables():
            iteration_var = AnnotatedExpression(
                expr=ast.Name(id="item", ctx=ast.Load()),
                annotation=TypedAnnotation(iterable.annotation.arg),
            )
            iter_context = context + [iteration_var]
            iter_context = self.enrich_context(iter_context)

            yield ast.For(
                target=ast.Name(id="item", ctx=ast.Store()),
                iter=iterable.expr,
                body=[iter_context.ellipsis()],
                orelse=[],
            )
