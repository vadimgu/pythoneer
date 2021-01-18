import ast
from itertools import permutations, product, chain
from typing import Sequence, List, Mapping, Iterator, Tuple, NamedTuple
from collections import defaultdict, deque

from pythoneer.annotation import TypeAnnotation
from pythoneer.expression import AnnotatedExpression


def call_args(
    annotation: TypeAnnotation, exprs: Sequence[AnnotatedExpression]
) -> Iterator[List[AnnotatedExpression]]:
    """
    exprs = [a:int, b:int, c:int, d:bool, e: bool]
    annotation = [int, int, bool, bool]

    product(
        permutations(ints, 2)
        permutations(bools, 2)
    )

    (i, i, b, b)
    ____________
    (a, b, d, e)
    (a, c, d, e)
    (b, a, d, e)
    (b, c, d, e)
    (a, b, e, d)
    (a, c, e, d)
    (b, a, e, d)
    (b, c, e, d)

    annotation = [int, bool, bool, int]

    arg0: 0 int
    arg1: 1 bool
    arg2: 2 int
    arg3: 3 bool

    [int] -> 0, 2
    [bool] -> 1, 3

    idx = 0, 2, 1, 3
          ____  ____
          int    bool

    args = [i1, i2, b1, b2]
    i1, i2, b1, b2 -> i1, b1, i2, b2

    args = [args[i] for i in idx]

    a, d, b, e  -> a, b, d, e
    """
    arg_types = defaultdict(list)  # type: Mapping[type, List[AnnotatedExpression]]
    arg_annotations, _ = annotation.slice.type
    for i, arg_annotation in enumerate(arg_annotations):
        arg_types[arg_annotation].append(i)

    arg_types = dict(arg_types)
    idx = sum(arg_types.values(), [])

    param_groups = defaultdict(list)  # type: Mapping[type, List[AnnotatedExpression]]
    for expr in exprs:
        param_groups[expr.annotation.type].append(expr)

    type_perms = {}  # type: Mapping[type, Iterator[Tuple[AnnotatedExpression, ...]]]
    for arg_type, arg_type_pos in arg_types.items():
        count_args = len(arg_type_pos)
        type_perms[arg_type] = permutations(param_groups[arg_type], r=count_args)

    for typed_args_collection in product(*type_perms.values()):
        args = list(chain(*typed_args_collection))
        args = [args[i] for i in idx]
        yield args


class CallNode(NamedTuple):
    callable: AnnotatedExpression
    args: List[AnnotatedExpression]
    depth: int

    def call_expr(self) -> ast.Call:
        return ast.Call(
            func=self.callable.expr,
            args=[arg_expr.expr for arg_expr in self.args],
            keywords=[],
        )

    def returns_annotation(self) -> TypeAnnotation:
        return TypeAnnotation(
            # ??? Sometimes callable sometimes simple annotation
            self.callable.annotation.expr.slice.value.elts[1],
            namespace=self.callable.annotation.namespace,
        )

    def ann_call_expr(self) -> AnnotatedExpression:
        return AnnotatedExpression(
            self.call_expr(),
            self.returns_annotation(),
        )

    def __str__(self):

        # return ast.dump(call_expr)
        import astor

        call_expr = self.call_expr()

        ast.fix_missing_locations(call_expr)
        return f"{astor.to_source(call_expr)}"


class CallComposition:
    def __init__(
        self,
        callables: List[AnnotatedExpression],
        expressions: Sequence[AnnotatedExpression],
        depth: int = 1,
    ):
        self.callables = callables
        self.expressions = expressions
        self.depth = depth

    def __iter__(self) -> Iterator[ast.Call]:
        """
        callables =
            f1: Callable[[int, int], int]
            f2:Callable[[int, int], int]
        expressions =
            a: int
            b: int
            c: int

        f1(a, b)
        f1(a, c)
        f1(b, a)
        f1(b, c)
        f1(c, b)
        f1(c, a)

        f2(a, b)
        f2(a, c)
        f2(b, a)
        f2(b, c)
        f2(c, b)
        f2(c, a)

        f1(a, f1(a, b))
        ...
        f1(a, f2(a, b))
        ...
        f2(a, f1(a, b))
        ...
        f2(a, f2(a, b))
        ...

        """

        expressions = set(self.expressions)
        q = deque()  # type: deque[CallNode]
        new_expressions = set()
        for callable in self.callables:
            for args in call_args(callable.annotation, expressions):
                call_node = CallNode(callable, args, 1)
                q.append(call_node)
                new_expressions.add(call_node.ann_call_expr())
        expressions.update(new_expressions)
        for expr in expressions:
            print(ast.dump(expr.expr))

        while q:
            call_node = q.popleft()
            yield call_node.call_expr()
            if call_node.depth < self.depth:
                print(call_node.depth)
                new_expressions = set()
                for callable in self.callables:
                    for args in call_args(callable.annotation, expressions):
                        new_call_node = CallNode(callable, args, call_node.depth + 1)
                        new_expressions.add(new_call_node.ann_call_expr())
                        q.append(new_call_node)
                        break
                expressions.update(new_expressions)
            else:
                print("Debug reach depth")


class ParemeterPermutations:
    def __init__(self, annotation, expressions):
        ...

    def __len__(self):
        ...

    def __iter__(self):
        ...
        # permutations of the same type
        # type_permutations[
        #    permutations(ints, args.int.count),  # (int, int, int)  N = n!/(n-k)!
        #    permutations(bools, args.int.count),  # (bool, bool) M = m!/(m-k)!
        # ]  # N * M