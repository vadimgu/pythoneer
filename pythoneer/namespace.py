import ast
import _ast
from pythoneer.utils import parse_expr
import re
from typing import Mapping, List, Dict

from pythoneer.annotation import TypeAnnotation
from pythoneer.expression import AnnotatedExpression


class AnnotatedNamespace:
    """
    Used to maintain a mapping of named annotated expressions.
    """

    def __init__(self, namespace: Mapping[str, AnnotatedExpression]):
        self.namespace = namespace

    def __getitem__(self, name):
        """
        Getting the annotated expression by name

        >>> ns = AnnotatedNamespace({'a': None})
        >>> ns['a'] is None
        True
        >>> ns['b'] # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        KeyError: 'b'
        """
        return self.namespace[name]

    def __contains__(self, name):
        """
        >>> ns = AnnotatedNamespace({'a': None})
        >>> 'a' in ns
        True
        >>> 'b' in ns
        False
        """
        return name in self.namespace

    def keys(self):
        """
        >>> ns = AnnotatedNamespace({'a': None, 'b': None})
        >>> list(ns.keys())
        ['a', 'b']
        """
        return self.namespace.keys()

    def values(self):
        """
        >>> ns = AnnotatedNamespace({'a': None, 'b': None})
        >>> list(ns.values())
        [None, None]
        """
        return self.namespace.values()

    def items(self):
        return self.namespace.items()

    @classmethod
    def from_ast(cls, ast_node: ast.AST, source_lines: List[str], globals):
        """
        >>> from typing import List
        >>> source = '''
        ... def x(a: int, b: str) -> int:
        ...     c = [1, 2]  # type: List[int]
        ...     d: int = c[0]
        ... '''
        >>> node = ast.parse(source).body[0]
        >>> ns = AnnotatedNamespace.from_ast(node, source.split('\\n'), globals())
        >>> list(ns.keys())
        ['a', 'b', 'c', 'd']
        """

        namespace = {}  # type: Dict[str, AnnotatedExpression]

        if isinstance(ast_node, ast.FunctionDef):
            if len(ast_node.args.args) > 0:
                if ast_node.args.args[0].arg == "self":
                    start = 1
                elif ast_node.args.args[0].arg == "cls":
                    start = 1
                else:
                    start = 0

                for arg in ast_node.args.args[start:]:
                    name = arg.arg
                    namespace[name] = AnnotatedExpression.from_arg(arg, globals)

        for child in ast.iter_child_nodes(ast_node):
            if isinstance(child, ast.Assign):
                # TODO support unpack assignment such as "a, b = 1, 2"
                first_target = child.targets[0]
                if isinstance(first_target, ast.Name):
                    name = first_target.id
                    _, comment = re.split("# type:", source_lines[child.lineno - 1], 1)
                    type_expr = parse_expr(comment.strip())
                    namespace[name] = AnnotatedExpression(
                        ast.Name(id=name, ctx=ast.Load()),
                        TypeAnnotation(type_expr, globals),
                    )
            elif isinstance(child, ast.AnnAssign):
                if isinstance(child.target, ast.Name):
                    namespace[child.target.id] = AnnotatedExpression.from_annassign(
                        child, globals
                    )
        return cls(namespace)
