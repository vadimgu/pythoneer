import ast
from itertools import product
from functools import reduce
from operator import mul
from typing import (
    Callable,
    Iterable,
    Iterator,
    List,
    Tuple,
    Type,
    TypeVar,
)


from pythoneer.context import Context
from pythoneer.expression import AnnotatedExpression


SetterType = Callable[[ast.expr], None]

T = TypeVar("T")


class ExpressionSlot(ast.expr):
    _fields = ("type", "with_vars")

    def __init__(self, type: Type, with_vars=[]):
        self.type = type
        self.with_vars = with_vars


class SettersNodeVisitor(ast.NodeVisitor):
    """
    SettersNodeVisitors can traverse all nodes and accumulate typed setters.

    The setters are callables of type SetterType.
    """

    setters: List[Tuple[Type, SetterType]]

    def __init__(self):
        self.setters = []

    def register_setter(self, type: Type, setter: SetterType):
        self.setters.append((type, setter))

    def get_setters(self, node: ast.AST) -> List[Tuple[Type, SetterType]]:
        """
        >>> node = ast.If(
        ...     test=ExpressionSlot(type=bool),
        ...     body=[ast.Assign(targets=[ast.Name(id="a", ctx=ast.Store())], value=ExpressionSlot(type=int))],
        ...     orelse=[ast.Assign(targets=[ast.Name(id="a", ctx=ast.Store())], value=ExpressionSlot(type=int))],
        ... )
        >>> setters = SettersNodeVisitor().get_setters(node)
        >>> setters  # doctest: +ELLIPSIS
        [(<class 'bool'>, <function ...>), (<class 'int'>, <function ...>), (<class 'int'>, <function ...>)]

        >>> setters[0][1](ast.Name(id='a', ctx=ast.Load()))
        >>> setters[1][1](ast.Name(id='b', ctx=ast.Load()))
        >>> setters[2][1](ast.Name(id='c', ctx=ast.Load()))
        >>> ast.dump(node.test)
        "Name(id='a', ctx=Load())"
        >>> ast.dump(node.body[0].value)
        "Name(id='b', ctx=Load())"
        >>> ast.dump(node.orelse[0].value)
        "Name(id='c', ctx=Load())"
        """
        self.visit(node)
        return self.setters

    def visit_If(self, node: ast.If):
        """
        Visit a ast.If node register a setter for the "test" field.

        >>> node = ast.If(test=ExpressionSlot(type=bool), body=[], orelse=[])
        >>> v = SettersNodeVisitor()
        >>> v.visit_If(node)
        >>> v.setters  # doctest: +ELLIPSIS
        [(<class 'bool'>, <function ...>)]

        Using a setter will replace the "test" field

        >>> type, setter = v.setters[0]
        >>> expr = ast.Name(id='a', ctx=ast.Load())
        >>> setter(expr)
        >>> node.test == expr
        True
        """
        if isinstance(node.test, ExpressionSlot):
            slot = node.test

            def setter(test_expr: ast.expr):
                node.test = test_expr

            self.register_setter(slot.type, setter)
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        """
        Visit a ast.For node and register a setter for the "iter" field.
        >>> T = TypeVar('T')
        >>> node = ast.For(target=None, iter=ExpressionSlot(type=Iterable[T]), body=[], orelse=[])
        >>> v = SettersNodeVisitor()
        >>> v.visit_For(node)
        >>> v.setters  # doctest: +ELLIPSIS
        [(typing.Iterable[~T], <function ...>)]

        Using a setter will replace the "iter" field

        >>> type, setter = v.setters[0]
        >>> expr = ast.Name(id='a', ctx=ast.Load())
        >>> setter(expr)
        >>> node.iter == expr
        True
        """
        if isinstance(node.iter, ExpressionSlot):
            slot = node.iter

            def setter(iter_expr: ast.expr):
                node.iter = iter_expr

            self.register_setter(slot.type, setter)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        """
        Visit a ast.Assign node and register a setter for the "value" field.

        >>> node = ast.Assign(targets=[ast.Name(id="a", ctx=ast.Store())], value=ExpressionSlot(type=int))
        >>> v = SettersNodeVisitor()
        >>> v.visit_Assign(node)
        >>> v.setters  # doctest: +ELLIPSIS
        [(<class 'int'>, <function ...>)]

        Using a setter will replace the "value" field

        >>> type, setter = v.setters[0]
        >>> expr = ast.Name(id='b', ctx=ast.Load())
        >>> setter(expr)
        >>> node.value == expr
        True
        """
        if isinstance(node.value, ExpressionSlot):
            slot = node.value

            def setter(value_expr: ast.expr):
                node.value = value_expr

            self.register_setter(slot.type, setter)
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return):
        """
        Visit a ast.Return node and register a setter for the "value" field.

        >>> node = ast.Return(value=ExpressionSlot(type=int))
        >>> v = SettersNodeVisitor()
        >>> v.visit_Return(node)
        >>> v.setters  # doctest: +ELLIPSIS
        [(<class 'int'>, <function ...>)]

        Using a setter will replace the "value" field

        >>> type, setter = v.setters[0]
        >>> expr = ast.Name(id='b', ctx=ast.Load())
        >>> setter(expr)
        >>> node.value == expr
        True
        """
        if isinstance(node.value, ExpressionSlot):
            slot = node.value

            def setter(value_expr: ast.expr):
                node.value = value_expr

            self.register_setter(slot.type, setter)
        self.generic_visit(node)


def trivial_pattern(
    return_type: Type, preamble: List[ast.stmt] = [], conclusion: List[ast.stmt] = []
):
    return ast.Module(
        body=preamble
        + [
            ast.Return(value=ExpressionSlot(type=return_type)),
        ]
        + conclusion,
    )


def conditional_pattern(
    return_type: Type, preamble: List[ast.stmt] = [], conclusion: List[ast.stmt] = []
):
    module = ast.Module(
        body=preamble
        + [
            ast.If(
                test=ExpressionSlot(type=bool),
                body=[
                    ast.Assign(
                        targets=[ast.Name(id="rvalue", ctx=ast.Store())],
                        value=ExpressionSlot(type=return_type),
                    ),
                ],
                orelse=[
                    ast.Assign(
                        targets=[ast.Name(id="rvalue", ctx=ast.Store())],
                        value=ExpressionSlot(type=return_type),
                    ),
                ],
            ),
            ast.Return(
                value=ast.Name(id="rvalue", ctx=ast.Load()),
            ),
        ]
        + conclusion,
    )
    return module


def iteration_pattern(return_type: Type):
    return ast.Module(
        body=[
            ast.Assign(
                targets=[ast.Name(id="rvalue", ctx=ast.Store())],
                value=ExpressionSlot(type=return_type),
            ),
            ast.For(
                target=ast.Name(id="item_x", ctx=ast.Store()),
                iter=ExpressionSlot(type=Iterable[T]),
                body=[
                    ast.Assign(
                        targets=[ast.Name(id="rvalue", ctx=ast.Store())],
                        value=ExpressionSlot(type=return_type),
                    ),
                ],
                orelse=[],
            ),
            ast.Return(value=ast.Name(id="rvalue", ctx=ast.Load())),
        ],
    )


def mixed_pattern(return_type: Type):
    ast_pattern = ast.Module(
        body=[
            ast.Assign(
                targets=[ast.Name(id="rvalue", ctx=ast.Store())],
                value=ExpressionSlot(type=return_type),
            ),
            ast.If(
                test=ExpressionSlot(type=return_type),
                body=[
                    ast.For(  # for item in iterable:
                        target=ast.Name(id="item_x", ctx=ast.Store()),
                        iter=ExpressionSlot(type=Iterable[T]),
                        body=[
                            ast.If(
                                test=ExpressionSlot(type=bool),
                                body=[
                                    ast.Assign(
                                        targets=[
                                            ast.Name(id="rvalue", ctx=ast.Store())
                                        ],
                                        value=ExpressionSlot(type=return_type),
                                    )
                                ],
                                orelse=[],
                            )
                        ],
                        orelse=[],
                    ),
                ],
                orelse=[],
            ),
            ast.Return(value=ast.Name(id="rvalue", ctx=ast.Load())),
        ],
    )
    return ast_pattern


class PatternPrograms:
    """
    Generate programs from a patern and a context
    """

    def __init__(self, pattern: ast.Module, context: Context):
        self.pattern = pattern
        self.context = context
        self.setters = SettersNodeVisitor().get_setters(self.pattern)

    @property
    def types(self) -> List[Type]:
        """
        >>> ctx = Context.parse([], {}, {})
        >>> pp = PatternPrograms(conditional_pattern(int), ctx)
        >>> pp.types
        [<class 'bool'>, <class 'int'>, <class 'int'>]
        """
        return [type for type, _ in self.setters]

    def type_matched_args(self) -> List[List[AnnotatedExpression]]:
        """
        Build a lists of expression matching the `self.types` positions.

        >>> ctx = Context.parse([('a < b', 'bool'), ('a == b', 'bool')], {'a': 'int', 'b': 'int'}, {})
        >>> pp = PatternPrograms(conditional_pattern(int), ctx)
        >>> pp.type_matched_args()  # doctest: +ELLIPSIS
        [[...], [...], [...]]
        """
        exprs_by_type = dict(self.context.groupby_type())
        return [exprs_by_type[type] for type in self.types]

    def generate(self) -> Iterator[ast.Module]:
        """
        Generate AST programs filled with expressions from the context.

        >>> ctx = Context.parse(
        ...     [('a < b', 'bool'), ('a == b', 'bool'), ('a > b', 'bool')],
        ...     {'a': 'int', 'b': 'int'},
        ...     {}
        ... )

        Combined with a pattern that has slots (bool, int, int)

        >>> pp = PatternPrograms(conditional_pattern(int), ctx)
        >>> list(pp.generate())  # doctest: +ELLIPSIS
        [<_ast.Module ...>, ...]
        """
        for exprs in product(*self.type_matched_args()):
            setters = [setter for _, setter in self.setters]
            ast_exprs = [expr.expr for expr in exprs]
            for setter, ast_expr in zip(setters, ast_exprs):
                setter(ast_expr)
            yield self.pattern

    def __len__(self):
        """
        Evaluate the number of programs.

        The number of programs depends on the context and on the pattern
        being used. For a context with 3 booleans an 2 integers.

        >>> ctx = Context.parse(
        ...     [('a < b', 'bool'), ('a == b', 'bool'), ('a > b', 'bool')],
        ...     {'a': 'int', 'b': 'int'},
        ...     {}
        ... )

        Combined with a pattern that has slots (bool, int, int)

        >>> pp = PatternPrograms(conditional_pattern(int), ctx)
        >>> pp.types
        [<class 'bool'>, <class 'int'>, <class 'int'>]

        The size of this program set can be evaluated as 3 * 2 * 2

        >>> len(pp)
        12

        It should be the same number as the count of pragrams generated by
        this program set.

        >>> len(pp) == len(list(pp.generate()))
        True
        """
        size = 1
        for exprs in self.type_matched_args():
            size *= len(exprs)
        return size