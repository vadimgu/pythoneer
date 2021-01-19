import ast
from functools import lru_cache
from typing import TypeVar, Type, Tuple, Iterable, Callable, List

from pythoneer.utils import compile_expr, parse_expr


T = TypeVar("T", bound="TypeAnnotation")


class AnnotationError(Exception):
    pass


class NotImplementedAnnotationExpression(AnnotationError):
    @classmethod
    def from_expr(cls, expr: ast.expr):
        return cls(f"Not supported anotation expression: {ast.dump(expr)}")


class NonParametrizedAnnotationError(AnnotationError):
    @classmethod
    def from_expr(cls, expr: ast.expr):
        return cls(f"Missing parameter in expression: {ast.dump(expr)}")


class TypeAnnotation:
    def __init__(self, expr: ast.expr, namespace: dict = {}):
        self.expr = expr
        self.namespace = namespace

    def __hash__(self):
        return id(self)

    @classmethod
    def parse(cls, expr: str, globals: dict):
        """
        >>> TypeAnnotation.parse('int', {}) # doctest: +ELLIPSIS
        <...TypeAnnotation ...>
        """

        return cls(parse_expr(expr), globals)

    @property
    @lru_cache(maxsize=None)
    def type(self) -> Type:
        """
        A Type instance based on the globals.

        >>> TypeAnnotation.parse('int', globals()).type
        <class 'int'>

        >>> ta = TypeAnnotation.parse('List[int]', globals())
        >>> ta.type
        typing.List[int]
        """
        return eval(compile_expr(self.expr), self.namespace)

    def __str__(self):
        return f"<TypeAnnotation {str(self.type)}>"

    @property
    def iterable(self) -> bool:
        """
        >>> ta = TypeAnnotation.parse('List[int]', globals())
        >>> ta.iterable
        True

        Only parametrised annotations are considered iterable.

        >>> ta = TypeAnnotation.parse('List', globals())
        >>> ta.iterable
        False

        >>> ta = TypeAnnotation('int', globals())
        >>> ta.iterable
        False
        """
        if type(self.expr) == ast.Subscript and type(self.expr.slice) == ast.Index:
            return issubclass(self.type, Iterable)
        else:
            return False
            # TODO: Implement iterables without iterable type "List" or "[]". ?

    @property
    def callable(self) -> bool:
        """
        `True` if the type annotation is callable.

        >>> TypeAnnotation.parse('Callable', globals()).callable
        True
        >>> TypeAnnotation.parse('Callable[[int, int], int]', globals()).callable
        True
        >>> TypeAnnotation.parse('int', globals()).callable
        False

        A class implementing a `__call__` method is also considered callable

        >>> class C:
        ...     def __call__(self): pass
        >>> TypeAnnotation.parse('C', globals()).callable
        True
        """
        return issubclass(self.type, Callable)

    @property
    def boolean(self) -> bool:
        """
        `True` if the annotation is of a boolean type.

        The `bool` types are considered to be boolean.

        >>> ta = TypeAnnotation.parse('bool', globals())
        >>> ta.boolean
        True

        Any other type is not considered as boolean.

        >>> ta = TypeAnnotation.parse('int', globals())
        >>> ta.boolean
        False
        """
        return self.type == bool

    def __eq__(self, other: object) -> bool:
        """
        Equality comparision of two annotations.

        >>> from typing import List, Sequence
        >>> ns = globals()

        >>> TypeAnnotation.parse('int', ns) == TypeAnnotation.parse('int', ns)
        True

        >>> TypeAnnotation.parse('int', ns) == TypeAnnotation.parse('bool', ns)
        False

        The container parameters must match

        >>> TypeAnnotation.parse('List[int]', ns) == TypeAnnotation.parse('List[int]', ns)
        True

        If the container parameters don't match, consider the two types as different.

        >>> TypeAnnotation.parse('List[int]', ns) == TypeAnnotation.parse('List[bool]', ns)
        False

        Container types are matched exactly

        >>> TypeAnnotation.parse('List[int]', ns) == TypeAnnotation.parse('Sequence[int]', ns)
        False
        """
        if isinstance(other, TypeAnnotation):
            return self.type == other.type
        else:
            raise NotImplementedError()

    @property
    def parametrized(self) -> bool:
        """
        >>> from typing import List, Callable
        >>> ns = globals()
        >>> TypeAnnotation.parse('List[int]', globals()).parametrized
        True
        >>> TypeAnnotation.parse('Callable[[int, int], int]', globals()).parametrized
        True
        >>> TypeAnnotation.parse('List', globals()).parametrized
        False
        >>> TypeAnnotation.parse('int', globals()).parametrized
        False
        """
        return isinstance(self.expr, ast.Subscript) and isinstance(
            self.expr.slice, ast.Index
        )

    @property
    def slice(self) -> "TypeAnnotation":
        """
        Return the slice
        >>> from typing import List, Callable, Mapping
        >>> param = TypeAnnotation.parse('List[int]', globals()).slice
        >>> param.type == int
        True

        >>> param = TypeAnnotation.parse('Callable[[int, int], int]', globals()).slice
        >>> param.type
        ([<class 'int'>, <class 'int'>], <class 'int'>)

        >>> param = TypeAnnotation.parse('Mapping[str, List]', globals()).slice
        >>> param.type
        (<class 'str'>, typing.List)

        Non parametrized type annotations fail with a
        `NotImplementAnnotationExpression`.

        >>> TypeAnnotation.parse('int', {}).slice  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        NonParametrizedAnnotationError
        """
        if self.parametrized:
            return TypeAnnotation(self.expr.slice.value, self.namespace)
        else:
            raise NonParametrizedAnnotationError.from_expr(self.expr)

    @property
    def args(self) -> Tuple[Type, ...]:
        return self.type.__args__[:-1]

    @property
    def arg_annotations(self) -> List["TypeAnnotation"]:
        """
        >>> from typing import Callable
        >>> ta = TypeAnnotation.parse('Callable[[int, bool], str]', globals())
        >>> for arg_annotation in ta.arg_annotations:
        ...     print(arg_annotation)
        <TypeAnnotation <class 'int'>>
        <TypeAnnotation <class 'bool'>>
        """
        annotations = []
        for expr in self.expr.slice.value.elts[0].elts:
            annotations.append(TypeAnnotation(expr, self.namespace))
        return annotations

    @property
    def returns_annotation(self) -> "TypeAnnotation":
        """
        >>> from typing import Callable
        >>> ta = TypeAnnotation.parse('Callable[[int, bool], str]', globals())
        >>> print(ta.returns_annotation)
        <TypeAnnotation <class 'str'>>
        """
        return TypeAnnotation(
            self.expr.slice.value.elts[1],
            self.namespace,
        )
