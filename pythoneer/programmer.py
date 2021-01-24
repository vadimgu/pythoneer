import ast
from functools import cached_property
from itertools import zip_longest
from typing import (
    Iterator,
    Iterable,
    List,
    Mapping,
    MutableSequence,
    MutableMapping,
    TextIO,
    Type,
)

from pythoneer.pattern import PatternPrograms, conditional_pattern, trivial_pattern
from pythoneer.validation import DoctestValidator
from pythoneer.function import Function
from pythoneer.module import Module
from pythoneer.context import Context
from pythoneer.namespace import AnnotatedNamespace
from pythoneer.expression import AnnotatedExpression
from pythoneer.annotation import TypeAnnotation
from pythoneer.return_value import ReturnValue, ListReturnValue
from pythoneer.utils import compile_expr
from pythoneer.space import ExpressionSpace


class ProgrammerException(Exception):
    pass


class NothingToImplement(ProgrammerException):
    pass


class SearchBoundary:
    def __init__(self, max_complexity, max_nesting):
        self.max_complexity = max_complexity
        self.max_nesting = max_nesting

    def crossed_by(self, function: Function) -> bool:
        """
        Tests if a `function` crosses any search boundary.

        >>> f = Function(ast.FunctionDef, complexity=3, nesting=2)
        >>> SearchBoundary(max_complexity=1, max_nesting=2).crossed_by(f)
        True
        >>> SearchBoundary(max_complexity=3, max_nesting=2).crossed_by(f)
        False
        >>> SearchBoundary(max_complexity=3, max_nesting=1).crossed_by(f)
        True
        """
        return any(
            (
                function.complexity > self.max_complexity,
                function.nesting > self.max_nesting,
            )
        )


class UnknownOption(ProgrammerException):
    pass


class Options:
    """
    Defines all options for a Programmer.
    """

    ast_operator_map: Mapping[str, Type[ast.operator]] = {
        "+": ast.Add,
        "-": ast.Sub,
        "/": ast.Div,
        "//": ast.FloorDiv,
        "@": ast.MatMult,
        "*": ast.Mult,
        "**": ast.Pow,
        "%": ast.Mod,
        "<<": ast.LShift,
        ">>": ast.RShift,
        "|": ast.BitOr,
        "^": ast.BitXor,
        "&": ast.BitAnd,
    }

    ast_unaryop_map: Mapping[str, Type[ast.unaryop]] = {
        "~": ast.Invert,
        "not": ast.Not,
        "+": ast.UAdd,
        "-": ast.USub,
    }

    ast_cmpop_map: Mapping[str, Type[ast.cmpop]] = {
        "==": ast.Eq,
        "!=": ast.NotEq,
        "<": ast.Lt,
        "<=": ast.LtE,
        ">": ast.Gt,
        ">=": ast.GtE,
        "is": ast.Is,
        "is not": ast.IsNot,
        "in": ast.In,
        "not in": ast.NotIn,
    }

    def __init__(
        self,
        unary_operators: List[str] = [],
        binary_operators: List[str] = [],
        compare_operators: List[str] = ["==", "<"],
        expression_levels: int = 1,
        max_complexity: int = 4,
        max_nesting: int = 1,
    ):
        self.max_complexity = max_complexity
        self.max_nesting = max_nesting
        self.unary_operators = unary_operators
        self.binary_operators = binary_operators
        self.compare_operators = compare_operators
        self.expression_levels = expression_levels

    @cached_property
    def search_boundary(self) -> SearchBoundary:
        return SearchBoundary(self.max_complexity, self.max_nesting)

    @classmethod
    def from_funcdef(cls, funcdef: ast.FunctionDef, globals):
        """
        Find the first ast.Dict expression. And build the Options instance.

        >>> f = '''
        ... def x():
        ...     "docstring here"
        ...     {'max_complexity': 1, 'max_nesting': 2}
        ... '''
        >>> options = Options.from_funcdef(ast.parse(f).body[0], globals())
        >>> options.max_complexity
        1
        >>> options.max_nesting
        2
        """
        for stmt in funcdef.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Dict):
                return cls(**eval(compile_expr(stmt.value), globals))
        return cls()

    @property
    def unary_operators_ast(self) -> List[Type[ast.unaryop]]:
        return [self.ast_unaryop_map[op] for op in self.unary_operators]

    @property
    def binary_operators_ast(self) -> List[Type[ast.operator]]:
        return [self.ast_operator_map[op] for op in self.binary_operators]

    @property
    def compare_operators_ast(self) -> List[Type[ast.cmpop]]:
        return [self.ast_cmpop_map[op] for op in self.compare_operators]


class Programmer(Iterable):
    """
    Programmer will produce all programs it can write.
    """

    def __init__(
        self,
        module: Module,
        name: str,
        globals: dict,
        locals: MutableMapping[str, List[AnnotatedExpression]],
        options: Options,
    ):
        self.module = module
        self.name = name
        self.globals = globals
        self.locals = locals
        self.options = options
        self.expression_space = ExpressionSpace(
            options.binary_operators_ast,
            options.compare_operators_ast,
            options.unary_operators_ast,
            options.expression_levels,
        )

    @cached_property
    def stub(self) -> ast.FunctionDef:
        return self.module.find_function(self.name)

    @classmethod
    def parse(cls, source: str, filename: str, name: str):
        """
        Parse a source and extract a function referenced by `name`. Read the
        options and local expressions.

        >>> module = '''
        ... from typing import List
        ... def x() -> int:
        ...    'doc'
        ...    {'max_complexity': 1}
        ...    a = [1, 2]  # type: List[int]
        ... '''
        >>> Programmer.parse(module, '<test>', 'x')  # doctest: +ELLIPSIS
        <...Programmer ...>
        """
        module = Module.from_string(source, filename)
        function_stmt = module.find_function(name)
        options = Options.from_funcdef(function_stmt, module.globals)
        locals = AnnotatedNamespace.from_ast(function_stmt, name, module.globals)
        return cls(module, name, module.globals, locals, options)

    @classmethod
    def from_stream(cls, source_stream: TextIO, filename: str, name: str):
        """
        >>> from io import StringIO
        >>> module = '''
        ... from typing import List
        ... def x() -> int:
        ...    'doc'
        ...    {'max_complexity': 1}
        ...    a = [1, 2]  # type: List[int]
        ... '''
        >>> Programmer.from_stream(StringIO(module), '<test>', 'x')  # doctest: +ELLIPSIS
        <....Programmer ...>
        """
        source = source_stream.read()
        return cls.parse(source, filename, name)

    @classmethod
    def from_file(cls, filename: str, name: str):
        with open(filename, "r") as fd:
            return cls.from_stream(fd, filename, name)

    @cached_property
    def rvalue(self) -> ReturnValue:
        """
        The return value that allows for return assignment and return
        statement handling

        >>> p = Programmer.parse('def x(a:int) -> int: pass', '<test>', 'x')
        >>> p.rvalue.annotation.type
        <class 'int'>
        """
        assert self.stub.returns is not None
        rvalue_annotation = TypeAnnotation.from_ast(self.stub.returns, self.globals)
        if issubclass(rvalue_annotation.type, MutableSequence):
            return ListReturnValue(rvalue_annotation)
        else:
            return ReturnValue(rvalue_annotation)

    def __iter__(self) -> Iterator[ast.Module]:
        first_ellipsis_pos = -1
        for i, stmt in enumerate(self.stub.body):
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Ellipsis):
                first_ellipsis_pos = i
                break

        preamble = self.stub.body[:first_ellipsis_pos]
        conclusion = self.stub.body[first_ellipsis_pos + 1 :]

        context = Context([], self.locals)
        context = self.expression_space.enrich_context(context)

        pat_cond = PatternPrograms(
            conditional_pattern(self.rvalue.annotation.type, preamble, conclusion),
            context,
        )
        pat_trivial = PatternPrograms(
            trivial_pattern(self.rvalue.annotation.type, preamble, conclusion),
            context,
        )
        # Iterating in parallel over
        for progs in zip_longest(pat_cond.generate(), pat_trivial.generate()):
            for prog in progs:
                if prog is not None:
                    yield prog

        # yield from pat.generate()

    def filter(self) -> Iterator[ast.Module]:
        for generated_mod in self.__iter__():
            self.module.replace_stmts(self.name, generated_mod.body)
            exec(self.module.compile(), self.globals)
            validator = DoctestValidator.from_ast(self.stub, self.globals)
            if validator.validate_module():
                yield generated_mod

    def first(self) -> ast.Module:
        for generated_mod in self.filter():
            return generated_mod
        else:
            raise NotImplementedError
