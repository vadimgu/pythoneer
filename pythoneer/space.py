"""
This module contains various specialist programmers

- MathematicalProgrammer
- FunctionalProgrammer
- OOProgrammer

"""
import ast
from collections import deque, defaultdict
from itertools import combinations, product
from typing import (
    Iterator,
    Sequence,
    Callable,
    Mapping,
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

    def minterms(self, boolean_exprs: Sequence[AnnotatedExpression]):
        """
        Generate all minterm (and) operation expressions

        >>> parse = AnnotatedExpression.parse
        >>> exprs = [parse('a', 'bool', {}), parse('b', 'bool', {})]
        >>> p = BooleanExpressionProgrammer()
        >>> [expr.to_source() for expr in p.minterms(exprs)]
        ['(a and b)', '(not a and b)', '(a and not b)', '(not a and not b)']
        """
        n = 2 ** len(boolean_exprs)
        for i in range(n):
            values = []
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
        integers = context.expressions_by_type(int)

        math_expressions = []
        # negations
        for expr in integers:
            ...

        # binary operations
        for a, b in combinations(integers, 2):
            a * b


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
        <AnnotatedExpression('sub(a, a)', 'int')>
        <AnnotatedExpression('sub(a, b)', 'int')>
        <AnnotatedExpression('sub(b, a)', 'int')>
        <AnnotatedExpression('sub(b, b)', 'int')>
        """
        exprs_by_type = defaultdict(
            list
        )  # type: MutableMapping[Type, List[AnnotatedExpression]]
        exprs_by_type.update(context.groupby_type())

        call_expressions = set()  # type: Set[AnnotatedExpression]

        d = deque()  # type: deque[AnnotatedExpression]
        for callable in context.callables():
            type_matchd_args = [
                exprs_by_type[arg.type] for arg in callable.annotation.arg_annotations
            ]
            for exprs_for_args in product(*type_matchd_args):
                call_expression = AnnotatedExpression(
                    ast.Call(
                        func=callable.expr,
                        args=[expr.expr for expr in exprs_for_args],
                        keywords=[],
                    ),
                    callable.annotation.returns_annotation,
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
                        TypeAnnotation(
                            ast.Name(id="bool", ctx=ast.Load()), self.globals
                        ),
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
                annotation=iterable.annotation.slice,
            )
            iter_context = context + [iteration_var]
            iter_context = self.enrich_context(iter_context)

            yield ast.For(
                target=ast.Name(id="item", ctx=ast.Store()),
                iter=iterable.expr,
                body=[iter_context.ellipsis()],
                orelse=[],
            )


class GeneratorSpace:
    def __init__(self):
        ...

    def statements(self, context: Context) -> Iterator[ast.stmt]:
        ...