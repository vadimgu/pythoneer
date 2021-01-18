import ast
import sys
from io import StringIO

from doctest import DocTestParser, DocTest, DocTestRunner


class DoctestValidator:
    def __init__(self, docstring: str, globals: dict, name: str):
        self.docstring = docstring
        self.test = DocTest(
            examples=DocTestParser().get_examples(docstring, name=name),
            globs=globals,
            name=name,
            filename=None,
            lineno=None,
            docstring=docstring,
        )

    @classmethod
    def from_ast(cls, funcdef: ast.FunctionDef, globals):
        """
        >>> import ast
        >>> f = ast.parse('''
        ... def a():
        ...     'Hello'
        ... ''')
        >>> DoctestValidator.from_ast(f.body[0], {})  # doctest: +ELLIPSIS
        <validation.DoctestValidator ...>
        """
        docstring = funcdef.body[0].value.s
        name = funcdef.name
        return cls(docstring, globals, name)

    def validate_module(self) -> bool:
        """
        Run all tests for a given function implementation

        >>> v = DoctestValidator('''
        ... >>> 1
        ... 1''', {}, '<test>')
        >>> v.validate_module()
        True

        >>> v = DoctestValidator('''
        ... >>> 2
        ... 1''', {}, '<test>')
        >>> v.validate_module()
        False
        """
        out = StringIO()
        # out = sys.stdout
        runner = DocTestRunner()
        runner.run(self.test, out=out.write)
        return runner.failures == 0
