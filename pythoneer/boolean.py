import ast
from typing import List, Union


class BooleanExpressionProgrammer:
    """
    Generate all possible boolean expressions for a list of boolean expresions.

    This gives us 2^(2^n) boolean expressions where `n` is the size of `booleans`.
    """

    def __init__(self, booleans: List[Union[ast.Name, ast.BoolOp, ast.Compare]]):
        self.booleans = booleans

    def __iter__(self):
        for bool_expr in self.boolean_expressions():
            yield bool_expr

    def minterms(self):
        n = 2 ** len(self.booleans)
        for i in range(n):
            values = []
            for j, boolean_value in enumerate(self.booleans):
                if (i >> j) % 2 == 1:
                    values.append(ast.UnaryOp(op=ast.Not(), operand=boolean_value))
                else:
                    values.append(boolean_value)
            yield ast.BoolOp(op=ast.And(), values=values)

    def boolean_expressions(self):
        minterms = list(self.minterms())
        for i in range(2 ** len(minterms)):
            terms = []
            for j, minterm in enumerate(minterms):
                if (i >> j) % 2 == 1:
                    terms.append(minterm)
            if len(terms) == 0:
                continue
            if len(terms) == 1:
                yield terms[0]
            else:
                yield ast.BoolOp(op=ast.Or(), values=terms)


#Expr = Union[ast.Name, ast.BoolOp, ast.Compare]
#
#class FunctionProgrammer:
#    def __init__(self, name, args):
#        self.name = name
#        self.args = args
#
#    @property
#    def expression_programmer(self, expressions: List[Expr]=[]):
#        booleans = [ast.Name(id=arg.arg, ctx=ast.Load()) for arg in self.args]
#        booleans.extend(expressions)
#        return BooleanExpressionProgrammer(booleans)
#
#    def __iter__(self):
#        for expr in self.expression_programmer:
#            yield ast.Module(
#                body=[ast.FunctionDef(
#                    name=self.name,
#                    args=ast.arguments(args=self.args, vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
#                    body=[
#                        ast.Return(expr),
#                    ],
#                    decorator_list=[],
#                    returns=None,
#                )],
#                type_ignores=[],
#            )
#
#import unittest
#class TestCaseF1(unittest.TestCase):
#    def test_truth_table(self):
#        self.assertTrue(
#            all([
#                f1(0, 0, 0) == 0,
#                f1(0, 0, 1) == 1,
#                f1(0, 1, 0) == 1,
#                f1(0, 1, 1) == 1,
#                f1(1, 0, 0) == 1,
#                f1(1, 0, 1) == 1,
#                f1(1, 1, 0) == 1,
#                f1(1, 1, 1) == 1,
#            ])
#        )
#
#
#class Constraint:
#    def __init__(self, input, output):
#        self.input
#        self.output
#    
#    def verify(self, func):
#        return func(*self.input) == self.output
#
#
#class ExampleStub(PythonModule):
#    module='examples.stub'
#
#    def test_f1(self):
#        assert self.module.f1() is None
#    
#    def test_f2(self):
#        assert self.module.f2() == 1
#
#
#
#class SearchProgram:
#    def __init__(self, db, constraints):
#        self.db = db
#        self.constraints = constraints
#    
#    def __iter__(self):
#        for program in self.db:
#            if self.test(program):
#                yield program
#
#    def test(self, program):
#        ast.fix_missing_locations(program)
#        compiled = compile(program, filename='<ast_generated>', mode="exec")
#        exec(compiled)
#        f = generated_f
#        for constraint in self.constraints:
#            constraint.verify(f)
#
#if __name__ == '__main__':
#    
#    db = FunctionProgrammer(
#        name="f1",
#        args=[
#            ast.arg(arg='a', annotation=None),
#            ast.arg(arg='b', annotation=None),
#            ast.arg(arg='c', annotation=None),
#        ],
#    )
#
#    search = SearchProgram(
#        db=db,
#        constraints=[
#            Constraint(input=(0, 0, 0), output=0),
#            Constraint(input=(0, 0, 1), output=1),
#            Constraint(input=(0, 1, 0), output=1),
#            Constraint(input=(0, 1, 1), output=1),
#            Constraint(input=(1, 0, 0), output=1),
#            Constraint(input=(1, 0, 1), output=1),
#            Constraint(input=(1, 1, 0), output=1),
#            Constraint(input=(1, 1, 1), output=1),
#        ]
#    )
#
#
#    for program in search:
#        ast.fix_missing_locations(program)
#        compiled = compile(program, filename='<ast_generated>', mode="exec")
#        exec(compiled)
#        constraints = all([
#            f1(0, 0, 0) == 0,
#            f1(0, 0, 1) == 1,
#            f1(0, 1, 0) == 1,
#            f1(0, 1, 1) == 1,
#            f1(1, 0, 0) == 1,
#            f1(1, 0, 1) == 1,
#            f1(1, 1, 0) == 1,
#            f1(1, 1, 1) == 1,
#        ])
#        if constraints:
#            import astor
#            print(astor.dump_tree(program))
#            print(astor.to_source(program))
#            break
#    else:
#        print("Program not found")