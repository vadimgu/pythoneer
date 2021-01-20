import ast
from typing import Union, Tuple, TypeVar
import copy


T = TypeVar("T")


class ASTPath:
    """
    path = ('body', 0, 'body', 1, 'orelse', 2, 'value')
    """

    def __init__(self, path: Tuple = ()):
        self.path = path

    def append(self, path: Union[str, int]):
        return ASTPath(self.path + path)  # type: ignore

    def assign(self, old_node_parent, new_node):

        old_node_parent[self.path[-1]] = new_node

    def replace(self, root_node: T, new_node: ast.AST) -> T:
        new_node.path = self.path  # type: ignore
        new_root_node = copy.deepcopy(root_node)
        node = new_root_node
        for path_element in self.path[:-1]:
            if isinstance(path_element, str):
                node = getattr(node, path_element)
            else:
                node = node[path_element]  # type: ignore

        last_path_element = self.path[-1]
        if type(last_path_element) == str:
            setattr(node, last_path_element, new_node)
        else:
            node[last_path_element] = new_node  # type:ignore

        return new_root_node