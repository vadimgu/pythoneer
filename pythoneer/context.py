"""
A Context object holds all expressions with type annotation
"""
import ast
from typing import (
    Iterator,
    List,
    Mapping,
    MutableMapping,
    Sequence,
    Tuple,
    Type,
    TypeVar,
)
from collections import defaultdict

from astor.code_gen import to_source
from pythoneer import expression

from pythoneer.expression import AnnotatedExpression
from pythoneer.annotation import TypeAnnotation
from pythoneer.namespace import AnnotatedNamespace


C = TypeVar("C", bound="Context")


class Context:
    """
    A context maintains a `namespace` and `expressions` that can be used to code.

    The expressions are not necessarily manifested in AST. They exist in a
    context waiting to be used. The namespace on the other hand, is a mapping
    of available variables with their annotation.
    """

    def __init__(
        self,
        expressions: List[AnnotatedExpression],
        namespace: MutableMapping[str, AnnotatedExpression],
    ):
        self.expressions = expressions
        self.namespace = namespace

    def __str__(self):
        out = []
        for type, exprs in self.groupby_type():
            out.append(f"    {str(type)}: {str([expr.to_source() for expr in exprs])},")
        return "expressions: {\n" + "\n".join(out) + "\n}"

    @classmethod
    def parse(
        cls, exprs: List[Tuple[str, str]], namespace: Mapping[str, str], globals: dict
    ):
        """
        Parse a context from strings

        >>> ctx = Context.parse([('a < b', 'bool')], {'a': 'int', 'b': 'int', 'c': 'int'}, {})
        >>> len(ctx.expressions)
        1
        >>> list(ctx.namespace.keys())
        ['a', 'b', 'c']
        """
        ann_exprs = [
            AnnotatedExpression.parse(expr, ann, globals) for expr, ann in exprs
        ]
        ns = AnnotatedNamespace(
            {
                name: AnnotatedExpression(
                    ast.Name(id=name, ctx=ast.Load()),
                    TypeAnnotation.parse(ann, globals),
                )
                for name, ann in namespace.items()
            }
        )
        return cls(ann_exprs, ns)

    @classmethod
    def from_function(cls, func: ast.FunctionDef, namespace: dict = {}):
        """
        >>> f =  ast.parse('def f(a: int, b: str): ...').body[0]
        >>> ctx = Context.from_function(f, {})  # doctest: +ELLIPSIS
        >>> len(ctx.expressions)
        2
        """
        expressions = []
        for arg in func.args.args:
            # Handle self
            if arg.arg == "self":
                continue
            expressions.append(AnnotatedExpression.from_arg(arg, namespace))

        # Extract first level assignment expressions
        for stmt in func.body:
            if isinstance(stmt, ast.AnnAssign):
                expressions.append(AnnotatedExpression.from_annassign(stmt, namespace))

        return cls(
            expressions=expressions,
            namespace=namespace,
        )

    def boolean_expressions(self) -> Iterator[AnnotatedExpression]:
        """
        >>> ctx = Context.parse([('b > 0', 'bool')], {'a': 'bool', 'b': 'int'}, {})
        >>> for expr in ctx.boolean_expressions():
        ...     print(expr)
        <AnnotatedExpression('a', <class 'bool'>)>
        <AnnotatedExpression('(b > 0)', <class 'bool'>)>
        """
        for expr in self.namespace.values():
            if expr.annotation.boolean:
                yield expr
        for expr in self.expressions:
            if expr.annotation.boolean:
                yield expr

    def iterables(self) -> Iterator[AnnotatedExpression]:
        """
        Generate all iterables expressions in a context.

        >>> from typing import List
        >>> ctx = Context.parse([('a[b:]', 'List[int]')], {'a': 'List[int]', 'b': 'int'}, globals())
        >>> for expr in ctx.iterables():
        ...     print(expr)  # doctest: +ELLIPSIS
        <AnnotatedExpression('a', ...List[int]...
        <AnnotatedExpression('a[b:]', ...List[int]...
        """
        for expr in self.namespace.values():
            if expr.annotation.iterable:
                yield expr

        for expr in self.expressions:
            if expr.annotation.iterable:
                yield expr

    def callables(self) -> Iterator[AnnotatedExpression]:
        """
        Generates all callable expressions. Both expression and the namespace are searched.

        >>> from typing import Callable, Tuple
        >>> ctx = Context.parse(
        ...    [('a.items', 'Callable[[], Tuple[str, int]]')],
        ...    {'len': 'Callable[[List], int]', 'a': 'dict'},
        ...    globals(),
        ... )
        >>> for expr in ctx.callables():
        ...    print(expr)  # doctest: +ELLIPSIS
        <AnnotatedExpression('len', typing.Callable[[typing.List], int])>
        <AnnotatedExpression('a.items', typing.Callable[[], typing.Tuple[str, int]])>
        """
        for expr in self.namespace.values():
            if expr.annotation.callable:
                yield expr

        for expr in self.expressions:
            if expr.annotation.callable:
                yield expr

    def groupby_type(
        self, exclude: Tuple[Type, ...] = ()
    ) -> Iterator[Tuple[Type, List[AnnotatedExpression]]]:
        """
        Groups expressions by type and generates tuples of type and annotated expressions.

        >>> ctx = Context.parse(
        ...     [('a>b', 'bool'), ('a + b', 'int')],
        ...     {'a': 'int', 'b': 'int', 'c': 'bool'},
        ...     {})
        >>> for type, exprs in ctx.groupby_type():
        ...    print(type)
        ...    for expr in exprs:
        ...        print("   ",expr)  # doctest: +ELLIPSIS
        <class 'int'>
            <AnnotatedExpression('a', ...int...)>
            <AnnotatedExpression('b', ...int...)>
            <AnnotatedExpression('(a + b)', ...int...)>
        <class 'bool'>
            <AnnotatedExpression('c', ...bool...)>
            <AnnotatedExpression('(a > b)', ...bool...)>

        You can exclude expressions of particular subtyptes by providing a
        tuple of types in the `exclude` parameter.

        >>> for type, exprs in ctx.groupby_type(exclude=(bool,)):
        ...    print(type)
        ...    for expr in exprs:
        ...        print("   ",expr)  # doctest: +ELLIPSIS
        <class 'int'>
            <AnnotatedExpression('a', ...int...)>
            <AnnotatedExpression('b', ...int...)>
            <AnnotatedExpression('(a + b)', ...int...)>
        """
        groups = defaultdict(
            list
        )  # type: MutableMapping[Type, List[AnnotatedExpression]]
        for expr in self.namespace.values():
            t = expr.annotation.type
            if not issubclass(t, exclude):
                groups[t].append(expr)
        for expr in self.expressions:
            t = expr.annotation.type
            if not issubclass(t, exclude):
                groups[t].append(expr)

        for t, exprs in groups.items():
            yield t, exprs

    def all_expressions(self):
        for expr in self.namespace.values():
            yield expr

        for expr in self.expressions:
            yield expr

    def expressions_by_type(self, t: Type):
        """
        Generates all expressions of type `t`

        >>> ctx = Context.parse(
        ...     [('a>b', 'bool'), ('a + b', 'int')],
        ...     {'a': 'int', 'b': 'int', 'c': 'bool'},
        ...     {})
        >>> for expr in ctx.expressions_by_type(int):
        ...     print(expr)  # doctest: +ELLIPSIS
        <AnnotatedExpression('a', ...int...)>
        <AnnotatedExpression('b', ...int...)>
        <AnnotatedExpression('(a + b)', ...int...)>
        """
        for expr in self.all_expressions():
            if expr.annotation.type == t:
                yield expr

    def extend(self, expressions: Sequence[AnnotatedExpression]):
        self.expressions.extend(expressions)

    def copy_extend(self, expressions: Sequence[AnnotatedExpression]) -> "Context":
        return Context(self.expressions + expressions, self.namespace)

    def __add__(self, expressions: Sequence[AnnotatedExpression]) -> "Context":
        return Context(self.expressions + expressions, self.namespace)

    def ellipsis(self) -> ast.Expr:
        """
        Returns an Ellipsis expression with a context.
        """
        return ast.Expr(value=ast.Ellipsis())