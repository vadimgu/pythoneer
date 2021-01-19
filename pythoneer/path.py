import ast
from pythoneer.binop import ASTOperator
from typing import Union, Tuple, Callable, Any, Sequence, List, NamedTuple
import copy


class ASTPath:
    """
    path = ('body', 0, 'body', 1, 'orelse', 2, 'value')
    """

    def __init__(self, path: Tuple = ()):
        self.path = path

    def append(self, path: Union[str, int]):
        return ASTPath(self.path + path)

    def assign(self, old_node_parent, new_node):

        old_node_parent[self.path[-1]] = new_node

    def replace(self, root_node: ast.AST, new_node: ast.AST) -> ast.AST:
        new_node.path = self.path
        new_root_node = copy.deepcopy(root_node)
        node = new_root_node
        for path_element in self.path[:-1]:
            if type(path_element) == str:
                node = getattr(node, path_element)
            else:
                node = node[path_element]

        last_path_element = self.path[-1]
        if type(last_path_element) == str:
            setattr(node, last_path_element, new_node)
        else:
            node[last_path_element] = new_node

        return new_root_node