import ast
from collections import deque
import copy
from functools import cached_property
from pythoneer.validation import DoctestValidator
from typing import (
    Iterator,
    Iterable,
    List,
    Mapping,
    MutableSequence,
    MutableMapping,
    TextIO,
    Deque,
    Type,
)

from pythoneer.function import Function
from pythoneer.module import Module
from pythoneer.context import Context
from pythoneer.namespace import AnnotatedNamespace
from pythoneer.compare import CompareExpressions
from pythoneer.expression import AnnotatedExpression
from pythoneer.annotation import TypeAnnotation
from pythoneer.return_value import ReturnValue, ListReturnValue
from pythoneer.utils import compile_stmt, compile_expr
from pythoneer.space import NaiveProgrammer, StructuredProgrammingSpace


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
    Programmer can explore program space
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
        self.expression_space = NaiveProgrammer(
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

    def __iter__(self) -> Iterator[Function]:
        """
        Iterate over all programs that this programmer can write.
        """
        print("Start...")
        self.stub.body.append(self.rvalue.return_statement())
        program = Function(self.stub)
        print("Locals", self.locals)

        # Class annotated properties
        class_properties = []  # List[AnnotatedExpression]
        if "self" in self.locals:
            class_name = self.name.split(".")[0]
            print(class_name)
            class_annotations = self.globals[class_name].__annotations__
            for attr_name, attr_type in class_annotations.items():
                class_properties.append(
                    AnnotatedExpression(
                        ast.Attribute(
                            value=ast.Name(id="self", ctx=ast.Load()),
                            attr=attr_name,
                            ctx=ast.Load(),
                        ),
                        TypeAnnotation(attr_type, None),
                    )
                )

        context = Context(class_properties, self.locals)
        context = self.enrich_context(context)
        print(
            "Initial context:", len(context.expressions), len(context.namespace.keys())
        )
        ast_stack = deque()  # type: Deque[Function]
        # Attach a context to the ast statement.
        rvalue_insertion_idx = None
        for i, stmt in enumerate(self.stub.body):
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Ellipsis):
                rvalue_insertion_idx = i
                break
        if rvalue_insertion_idx is None:
            return

        for rvalue_assignement in self.rvalue_assignement_statements(context):
            program = Function(copy.deepcopy(self.stub))
            program.function.body.insert(rvalue_insertion_idx, rvalue_assignement)

            # for stmt in program.body:
            #    setattr(stmt, "context", context)

            ast_stack.append(program)

        seen = set()
        search_boundary = self.options.search_boundary
        while ast_stack:
            ast_program = ast_stack.popleft()
            yield ast_program
            for ellipsis_stmt in ast_program.ellipsis_nodes():
                # current_context = getattr(ellipsis_stmt, "context")
                current_context = context
                for stmt in self.statements(current_context):
                    new_program = ast_program.replace(ellipsis_stmt, stmt)

                    # Stop cycles and avoid identical functions
                    new_hash = hash(ast.dump(new_program.function))
                    if new_hash in seen:
                        # print("Debug: repetition")
                        continue
                    seen.add(new_hash)

                    # Search boundary test
                    if search_boundary.crossed_by(new_program):
                        # print("Debug: hit search boundary")
                        continue

                    ast_stack.append(new_program)

    def enrich_context(self, context: Context) -> Context:
        space = self.expression_space
        return space.enrich_context(context)

    def statements(self, context: Context) -> Iterator[ast.stmt]:
        yield from self.rvalue_assignement_statements(context)
        yield from self.if_statements(context)
        yield from self.for_statements(context)
        # yield from self.break_statements(context)

    def rvalue_assignement_statements(self, context: Context) -> Iterator[ast.stmt]:
        compatible_exprs = context.expressions_by_type(self.rvalue.annotation.type)
        for stmt in self.rvalue.assigns(compatible_exprs):
            yield stmt

    def break_statements(self, context: Context) -> Iterator[ast.stmt]:
        yield ast.Expr(value=ast.Break())

    def if_statements(self, context: Context) -> Iterator[ast.stmt]:
        # Generate if statements for all boolean expressions
        for bool_expr in context.boolean_expressions():
            yield ast.If(
                test=bool_expr.expr,
                body=[context.ellipsis()],
                orelse=[context.ellipsis()],
            )

    def for_statements(self, context: Context) -> Iterator[ast.stmt]:
        # Generate for statements for all iterable expressions
        for iterable in context.iterables():
            arg = iterable.annotation.arg
            if arg is None:
                continue
            iteration_var = AnnotatedExpression(
                expr=ast.Name(id="item", ctx=ast.Load()),
                annotation=arg,
            )
            iter_context = context + [iteration_var]
            iter_context = self.enrich_context(iter_context)

            yield ast.For(
                target=ast.Name(id="item", ctx=ast.Store()),
                iter=iterable.expr,
                body=[iter_context.ellipsis()],
                orelse=[],
            )

    def filter(self) -> Iterator[Function]:
        for function in self:
            self.module.replace_node(self.name, function)
            exec(self.module.compile(), self.globals)
            validator = DoctestValidator.from_ast(self.stub, self.globals)
            if validator.validate_module():
                yield function

    def first(self) -> Function:
        for function in self.filter():
            return function
        else:
            raise NotImplementedError
