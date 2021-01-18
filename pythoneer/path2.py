from typing import Hashable, Union, Tuple, Callable, Any, Sequence, List, NamedTuple

from operator import itemgetter, attrgetter, setitem
from functools import reduce, partial


class PathElement(NamedTuple):
    getter: Callable[[Any], Callable]
    value: Union[int, str]


class Item:
    def __init__(self, value: Hashable):
        ...


class Index:
    def __init__(self, idx: int):
        ...


class Atrr:
    def __init__(self, name: str):
        ...


class Path:
    def __init__(
        self, path: Sequence[Tuple[Callable[[Any], Callable], Union[int, str]]]
    ):
        self.path = path

    @classmethod
    def parse(cls, path_str: str):
        """
        >>> p = Path.parse("@a/#0/b")
        >>> p.path
        [(<class 'operator.attrgetter'>, 'a'), (<class 'operator.itemgetter'>, 0), (<class 'operator.itemgetter'>, 'b')]
        """
        path = []  # type: List[Tuple[Union[itemgetter, attrgetter], Union[str, int]]]
        for path_element in path_str.split("/"):
            if path_element:
                if path_element.startswith("@"):
                    path.append((attrgetter, path_element[1:]))
                elif path_element.startswith("#"):
                    path.append((itemgetter, int(path_element[1:])))
                else:
                    path.append((itemgetter, path_element))
        return cls(path)

    @property
    def getter(self) -> Callable[[Any], Any]:
        return partial(reduce, lambda obj, e: e[0](e[1])(obj), self.path)

    @property
    def setter(self) -> Callable[[Any, Any], Any]:
        if isinstance(self.path[-1], itemgetter):
            setitem()
        else:
            setattr()
        partial(reduce, lambda obj, func: func(obj), self.path[:-1])

        return partial(reduce(lambda obj, func: func(obj), self.path))

    def find(self, root_obj: object) -> object:
        """
        Find and return an object referenced by a path in `root_obj`.

        >>> root_obj = {'a': {'b': [{'c': 42}, {}]}}
        >>> path = Path.parse('a/b/#0/c')
        >>> path.find(root_obj)
        42
        """
        return self.getter(root_obj)

    def replace(self, root: object, replacement: object):
        self.setter(root, replacement)
