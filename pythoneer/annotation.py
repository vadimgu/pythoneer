import ast
from collections import abc
import typing
from typing import Optional, TypeVar, Type, Tuple, Iterable, Callable, List
from collections.abc import Iterable as ABC_Iterable

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
    type: Type
    ann_expr: Optional[ast.expr]

    def __init__(self, type: Type, ann_expr: Optional[ast.expr]):
        self.type = type
        self.ann_expr = ann_expr

    def __hash__(self):
        return hash(self.type)

    @classmethod
    def from_ast(cls, annotation_ast: ast.expr, globals):
        return cls(eval(compile_expr(annotation_ast), globals), annotation_ast)

    @classmethod
    def parse(cls, string: str, globals: dict):
        """
        Parse a type annotation from Python source string.

        >>> ta = TypeAnnotation.parse('int', {})
        >>> ta.type
        <class 'int'>
        """
        return cls.from_ast(parse_expr(string), globals)

    def __str__(self):
        return f"<TypeAnnotation {self.type}>"

    @property
    def iterable(self) -> bool:
        """
        >>> TypeAnnotation.parse('List[int]', globals()).iterable
        True

        Only parametrised generics are considered iterable.

        >>> TypeAnnotation.parse('List', globals()).iterable
        False

        >>> TypeAnnotation.parse('int', {}).iterable
        False

        >>> TypeAnnotation.parse('str', {}).iterable
        False
        """
        t = self.type
        original_generic_type = typing.get_origin(t)
        if original_generic_type is not None:
            if typing.get_args(t):
                return issubclass(original_generic_type, abc.Iterable)
        return False

    @property
    def callable(self) -> bool:
        """
        `True` if the type annotation is a parametrized Callable.

        >>> TypeAnnotation.parse('Callable[[int, int], int]', globals()).callable
        True
        >>> TypeAnnotation.parse('Callable', globals()).callable
        False
        >>> TypeAnnotation.parse('int', globals()).callable
        False
        >>> TypeAnnotation.parse('dict', globals()).callable
        False

        A class implementing a `__call__` method is not considered callable
        unless it's typed as a prametrized Callable.

        >>> class C:
        ...     def __call__(self): pass
        >>> TypeAnnotation.parse('C', globals()).callable
        False
        """
        if typing.get_origin(self.type) is abc.Callable:
            if len(typing.get_args(self.type)) == 2:
                return True
        return False

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
        return bool(typing.get_args(self.type))

    @property
    def arg(self) -> Optional["TypeAnnotation"]:
        """
        Return the TypeAnnotation Generic type argument
        >>> from typing import List, Callable, Mapping
        >>> TypeAnnotation(List[int], None).arg.type
        <class 'int'>
        >>> TypeAnnotation(List, None).arg is None
        True
        """
        args = typing.get_args(self.type)
        if args:
            return TypeAnnotation(args[0], None)
        else:
            return None

    @property
    def callable_args(self) -> List["TypeAnnotation"]:
        """
        >>> from typing import Callable
        >>> ta = TypeAnnotation(Callable[[int, bool], str], None)
        >>> for arg_annotation in ta.callable_args:
        ...     print(arg_annotation)
        <TypeAnnotation <class 'int'>>
        <TypeAnnotation <class 'bool'>>
        """
        annotations = []
        for type in typing.get_args(self.type)[0]:
            annotations.append(TypeAnnotation(type, self.ann_expr))
        return annotations

    @property
    def callable_returns(self) -> "TypeAnnotation":
        """
        >>> from typing import Callable
        >>> ta = TypeAnnotation.parse('Callable[[int, bool], str]', globals())
        >>> print(ta.callable_returns)
        <TypeAnnotation <class 'str'>>
        """
        return TypeAnnotation(
            typing.get_args(self.type)[1],
            self.ann_expr,
        )
