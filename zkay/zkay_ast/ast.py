import abc
import textwrap
from collections import OrderedDict
from enum import IntEnum
from os import linesep
from typing import List, Dict, Union, Optional, Callable, Set, Tuple

from zkay.config import cfg
from zkay.zkay_ast.analysis.partition_state import PartitionState
from zkay.zkay_ast.visitor.visitor import AstVisitor


class ChildListBuilder:
    def __init__(self):
        self.children = []

    def add_child(self, ast: 'AST') -> 'AST':
        if ast is not None:
            self.children.append(ast)
        return ast


class AST:

    def __init__(self):
        # set later by parent setter
        self.parent: AST = None

        # Names accessible by AST nodes below this node.
        # Does not include names already listed by parents.
        # Maps strings (names) to Identifiers.
        #
        # set later by symbol table
        self.names: Dict[str, AST] = {}

        self.line = -1
        self.column = -1

        self.modified_values: Set[InstanceTarget] = set()
        self.read_values: Set[InstanceTarget] = set()

    def children(self) -> List['AST']:
        cb = ChildListBuilder()
        self.process_children(cb.add_child)
        return cb.children

    def process_children(self, f: Callable[['AST'], 'AST']):
        pass

    def code(self) -> str:
        v = CodeVisitor()
        s = v.visit(self)
        return s

    def replaced_with(self, replacement: 'AST') -> 'AST':
        replacement.parent = self.parent
        replacement.names = self.names
        replacement.line = self.line
        replacement.column = self.column
        return replacement

    def __str__(self):
        return self.code()


class Identifier(AST):

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    @property
    def is_final(self):
        return isinstance(self.parent, StateVariableDeclaration) and self.parent.is_final

    def clone(self) -> 'Identifier':
        return Identifier(self.name)

    def decl_var(self, t: Union['TypeName', 'AnnotatedTypeName'], expr: Optional['Expression'] = None):
        if isinstance(t, TypeName):
            t = AnnotatedTypeName(t)
        storage_loc = '' if t.type_name.is_primitive_type() else 'memory'
        return VariableDeclarationStatement(VariableDeclaration([], t, self.clone(), storage_loc), expr)


class Comment(AST):

    def __init__(self, text: str = ''):
        super().__init__()
        self.text = text

    @staticmethod
    def comment_list(text: str, block: List[AST]) -> List[AST]:
        return block if not block else [Comment(text)] + block + [BlankLine()]

    @staticmethod
    def comment_wrap_block(text: str, block: List[AST]) -> List[AST]:
        if not block:
            return block
        return [
            Comment('-' * 31),
            Comment(text),
            Comment('-' * 31),
        ] + block + [
            Comment('-' * 31),
            BlankLine(),
        ]


class BlankLine(Comment):
    def __init__(self):
        super().__init__()


class Expression(AST):

    @staticmethod
    def all_expr():
        return AllExpr()

    @staticmethod
    def me_expr(stmt: Optional['Statement']=None):
        me = MeExpr()
        me.statement = stmt
        return me

    def implicitly_converted(self, expected: 'TypeName'):
        if expected == TypeName.bool_type() and not self.instanceof_data_type(TypeName.bool_type()):
            ret = FunctionCallExpr(BuiltinFunction('!='), [self, NumberLiteralExpr(0)])
        elif expected == TypeName.uint_type() and self.instanceof_data_type(TypeName.bool_type()):
            ret = FunctionCallExpr(BuiltinFunction('ite'), [self, NumberLiteralExpr(1), NumberLiteralExpr(0)])
        else:
            assert self.annotated_type.type_name == expected, f"Expected {expected.code()}, was {self.annotated_type.type_name.code()}"
            return self
        ret.annotated_type = AnnotatedTypeName(expected.clone(), self.annotated_type.privacy_annotation.clone())
        return ret

    def __init__(self):
        super().__init__()
        # set later by type checker
        self.annotated_type: AnnotatedTypeName = None
        # set by expression to statement
        self.statement: Statement = None

        self.has_side_effects = False
        self.is_private = False

    def is_all_expr(self):
        return self == Expression.all_expr()

    def is_me_expr(self):
        return self == Expression.me_expr()

    def privacy_annotation_label(self):
        if isinstance(self, IdentifierExpr):
            if isinstance(self.target, Mapping):
                return self.target.instantiated_key.privacy_annotation_label()
            else:
                return self.target.idf
        elif self.is_all_expr():
            return self
        elif self.is_me_expr():
            return self
        else:
            return None

    def instanceof_data_type(self, expected: 'TypeName') -> bool:
        assert (isinstance(expected, TypeName))

        # Implicit conversions
        if isinstance(self.annotated_type.type_name, AddressPayableTypeName) and expected == TypeName.address_type():
            return True

        # check data type
        actual = self.annotated_type.type_name
        return expected == actual

    def is_lvalue(self) -> bool:
        # TODO not really correct once we have reference types (there can be nested rvalues in left assignment subexpressions)
        return isinstance(self.statement, AssignmentStatement) and self.statement.lhs.is_parent_of(self)

    def is_rvalue(self) -> bool:
        return not self.is_lvalue()

    def unop(self, op: str) -> 'Expression':
        return FunctionCallExpr(BuiltinFunction(op), [self])

    def binop(self, op: str, rhs: 'Expression') -> 'Expression':
        return FunctionCallExpr(BuiltinFunction(op), [self, rhs])

    def is_parent_of(self, child):
        e = child
        while e != self and isinstance(e.parent, Expression):
            e = e.parent
        return e == self

    def instanceof(self, expected):
        """

        :param expected:
        :return: True, False, or 'make-private'
        """
        assert (isinstance(expected, AnnotatedTypeName))

        actual = self.annotated_type

        if not self.instanceof_data_type(expected.type_name):
            return False

        # check privacy type
        p_expected = expected.privacy_annotation.privacy_annotation_label()
        p_actual = actual.privacy_annotation.privacy_annotation_label()
        if not p_expected or not p_actual:
            return False
        else:
            if p_expected == p_actual:
                return True
            elif self.analysis is not None and self.analysis.same_partition(p_expected, p_actual):
                # analysis is not available, e.g., for state variables
                return True
            elif actual.privacy_annotation.is_all_expr():
                return 'make-private'
            else:
                return False

    def replaced_with(self, replacement: 'Expression') -> 'Expression':
        repl = super().replaced_with(replacement)
        assert isinstance(repl, Expression)
        repl.statement = self.statement
        return repl

    def as_type(self, t: Union['TypeName', 'AnnotatedTypeName']):
        self.annotated_type = t if isinstance(t, AnnotatedTypeName) else AnnotatedTypeName(t)
        return self

    @property
    def analysis(self):
        if self.statement is None:
            return None
        else:
            return self.statement.before_analysis


builtin_functions = {
    'parenthesis': '({})',
    'ite': '{} ? {} : {}'
}

# arithmetic
arithmetic = {op: f'{{}} {op} {{}}' for op in ['**', '*', '/', '%', '+', '-']}
arithmetic.update({'sign+': '+{}', 'sign-': '-{}'})
# comparison
comp = {op: f'{{}} {op} {{}}' for op in ['<', '>', '<=', '>=']}
# equality
eq = {op: f'{{}} {op} {{}}' for op in ['==', '!=']}
# boolean operations
bop = {op: f'{{}} {op} {{}}' for op in ['&&', '||']}
bop['!'] = '!{}'

builtin_functions.update(arithmetic)
builtin_functions.update(comp)
builtin_functions.update(eq)
builtin_functions.update(bop)


class BuiltinFunction(Expression):

    def __init__(self, op: str):
        super().__init__()
        self.op = op
        # set later by type checker
        self.is_private: bool = False

        # input validation
        if op not in builtin_functions:
            raise ValueError(f'{op} is not a known built-in function')

    def format_string(self):
        return builtin_functions[self.op]

    def is_arithmetic(self):
        return self.op in arithmetic

    def is_neg_sign(self):
        return self.op == 'sign-'

    def is_comp(self):
        return self.op in comp

    def is_eq(self):
        return self.op in eq

    def is_bop(self):
        return self.op in bop

    def is_parenthesis(self):
        return self.op == 'parenthesis'

    def is_ite(self):
        return self.op == 'ite'

    def has_shortcircuiting(self):
        return self.is_ite() or self.op == '&&' or self.op == '||'

    def arity(self):
        return self.format_string().count('{}')

    def input_types(self):
        """

        :return: None if the type is generic
        """
        if self.is_arithmetic():
            t = TypeName.uint_type()
        elif self.is_comp():
            t = TypeName.uint_type()
        elif self.is_bop():
            t = TypeName.bool_type()
        else:
            # eq, parenthesis, ite
            return None

        return self.arity() * [t]

    def output_type(self):
        """

        :return: None if the type is generic
        """
        if self.is_arithmetic():
            return TypeName.uint_type()
        elif self.is_comp():
            return TypeName.bool_type()
        elif self.is_bop():
            return TypeName.bool_type()
        elif self.is_eq():
            return TypeName.bool_type()
        else:
            # parenthesis, ite
            return None

    def can_be_private(self) -> bool:
        """
        :return: true if operation itself can be run inside a circuit
                 for equality and ite it must be checked separately whether the arguments are also supported inside circuits
        """
        return self.op not in ['**', '/', '%']


class FunctionCallExpr(Expression):

    def __init__(self, func: Expression, args: List[Expression], sec_start_offset: Optional[int] = 0):
        super().__init__()
        self.func = func
        self.args = args
        self.sec_start_offset = sec_start_offset

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.func = f(self.func)
        self.args[:] = map(f, self.args)


class NewExpr(FunctionCallExpr):
    def __init__(self, annotated_type: 'AnnotatedTypeName', args: List[Expression]):
        assert not isinstance(annotated_type, ElementaryTypeName)
        super().__init__(Identifier(f'new {annotated_type.code()}'), args)
        self.annotated_type = annotated_type

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.annotated_type = f(self.annotated_type)
        self.args[:] = map(f, self.args)


class CastExpr(FunctionCallExpr):
    def __init__(self, t: 'TypeName', expr: 'Expression'):
        self.t = t
        super().__init__(Identifier(t.code()), [expr])

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.t = f(self.t)
        self.args[0] = f(self.args[0])


class AssignmentExpr(Expression):

    def __init__(self, lhs: 'LocationExpr', rhs: Expression):
        super().__init__()
        self.lhs = lhs
        self.rhs = rhs

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.lhs = f(self.lhs)
        self.rhs = f(self.rhs)


class LiteralExpr(Expression):
    pass


class BooleanLiteralExpr(LiteralExpr):

    def __init__(self, value: bool):
        super().__init__()
        self.value = value
        self.annotated_type = AnnotatedTypeName.bool_all()


class NumberLiteralExpr(LiteralExpr):

    def __init__(self, value: int):
        super().__init__()
        self.value = value
        self.annotated_type = AnnotatedTypeName.uint_all()


class StringLiteralExpr(LiteralExpr):

    def __init__(self, value: str):
        super().__init__()
        self.value = value


class LocationExpr(Expression):
    def __init__(self):
        super().__init__()
        # set later by symbol table
        self.target: Optional[TargetDefinition] = None

    def call(self, member: Union[str, Identifier], args: List[Expression]) -> 'FunctionCallExpr':
        member = Identifier(member) if isinstance(member, str) else member.clone()
        return FunctionCallExpr(MemberAccessExpr(self, member), args)

    def dot(self, member: Union[str, Identifier]) -> 'MemberAccessExpr':
        member = Identifier(member) if isinstance(member, str) else member.clone()
        return MemberAccessExpr(self, member)

    def index(self, item: Union[int, Expression]) -> 'IndexExpr':
        assert isinstance(self.annotated_type.type_name, (Array, Mapping))
        if isinstance(item, int):
            item = NumberLiteralExpr(item)
        return IndexExpr(self, item).as_type(self.annotated_type.type_name.value_type)

    def assign(self, val: Expression) -> 'AssignmentStatement':
        return AssignmentStatement(self, val)


class IdentifierExpr(LocationExpr):

    def __init__(self, idf: Union[str, Identifier], annotated_type: Optional['AnnotatedTypeName'] = None):
        super().__init__()
        self.idf = idf if isinstance(idf, Identifier) else Identifier(idf)
        self.annotated_type = annotated_type

    def get_annotated_type(self):
        return self.target.annotated_type

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.idf = f(self.idf)

    def with_target(self, target: AST) -> 'IdentifierExpr':
        self.target = target
        return self

    def clone(self):
        idf = IdentifierExpr(self.idf.clone()).as_type(self.annotated_type)
        idf.target = self.target
        return idf


class MemberAccessExpr(LocationExpr):
    def __init__(self, expr: LocationExpr, member: Identifier):
        super().__init__()
        assert isinstance(expr, LocationExpr)
        self.expr = expr
        self.member = member

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.expr = f(self.expr)
        self.member = f(self.member)


class IndexExpr(LocationExpr):
    def __init__(self, arr: LocationExpr, key: Expression):
        super().__init__()
        assert isinstance(arr, LocationExpr)
        self.arr = arr
        self.key = key

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.arr = f(self.arr)
        self.key = f(self.key)


class SliceExpr(LocationExpr):
    def __init__(self, arr: LocationExpr, base: Optional[Expression], start_offset: int, size: int):
        super().__init__()
        self.arr = arr
        self.base = base
        self.start_offset = start_offset
        self.size = size


class MeExpr(Expression):
    name = 'me'
    is_final = True

    def clone(self) -> 'MeExpr':
        return MeExpr()

    def __eq__(self, other):
        return isinstance(other, MeExpr)

    def __hash__(self):
        return hash('me')


class AllExpr(Expression):
    name = 'all'
    is_final = True

    def clone(self) -> 'AllExpr':
        return AllExpr()

    def __eq__(self, other):
        return isinstance(other, AllExpr)

    def __hash__(self):
        return hash('all')


class ReclassifyExpr(Expression):

    def __init__(self, expr: Expression, privacy: Expression):
        super().__init__()
        self.expr = expr
        self.privacy = privacy

        # TODO FIXME? this is violated because privacy_annotation_label returns idf, not idfexpr
        # assert privacy is None or isinstance(privacy, MeExpr) or isinstance(privacy, AllExpr) or isinstance(privacy, IdentifierExpr)

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.expr = f(self.expr)
        self.privacy = f(self.privacy)


class HybridArgType(IntEnum):
    PRIV_CIRCUIT_VAL = 0
    PUB_CIRCUIT_ARG = 1
    PUB_CONTRACT_VAL = 2


class HybridArgumentIdf(Identifier):
    def __init__(self, name: str, t: 'TypeName', arg_type: HybridArgType, corresponding_priv_expression: Optional[Expression] = None):
        super().__init__(name)
        self.t = t # transformed type of this idf
        self.arg_type = arg_type
        self.corresponding_priv_expression = corresponding_priv_expression
        self.serialized_loc: SliceExpr = SliceExpr(IdentifierExpr(''), None, -1, -1)

    def get_loc_expr(self) -> LocationExpr:
        if self.arg_type == HybridArgType.PRIV_CIRCUIT_VAL:
            return IdentifierExpr(self.clone()).as_type(self.t)
        else:
            return IdentifierExpr(cfg.zk_data_var_name).dot(self).as_type(self.t)

    def clone(self):
        ha = HybridArgumentIdf(self.name, self.t, self.arg_type, self.corresponding_priv_expression)
        ha.serialized_loc = self.serialized_loc
        return ha

    def _set_serialized_loc(self, idf, base, start_offset):
        assert self.serialized_loc.start_offset == -1
        self.serialized_loc.arr = IdentifierExpr(idf)
        self.serialized_loc.base = base
        self.serialized_loc.start_offset = start_offset
        self.serialized_loc.size = self.t.size_in_uints

    def deserialize(self, source_idf: str, base: Optional[Expression], start_offset: int) -> 'AssignmentStatement':
        self._set_serialized_loc(source_idf, base, start_offset)

        src = IdentifierExpr(source_idf).as_type(Array(AnnotatedTypeName.uint_all()))
        if isinstance(self.t, Array):
            return SliceExpr(self.get_loc_expr(), None, 0, self.t.size_in_uints).assign(self.serialized_loc)
        elif base is not None:
            return self.get_loc_expr().assign(src.index(base.binop('+', NumberLiteralExpr(start_offset))).implicitly_converted(self.t))
        else:
            return self.get_loc_expr().assign(src.index(start_offset).implicitly_converted(self.t))

    def serialize(self, target_idf: str, base: Optional[Expression], start_offset: int) -> 'AssignmentStatement':
        self._set_serialized_loc(target_idf, base, start_offset)

        tgt = IdentifierExpr(target_idf).as_type(Array(AnnotatedTypeName.uint_all()))
        if isinstance(self.t, Array):
            return self.serialized_loc.assign(SliceExpr(self.get_loc_expr(), None, 0, self.t.size_in_uints))
        elif base is not None:
            return tgt.clone().index(base.binop('+', NumberLiteralExpr(start_offset))).assign(self.get_loc_expr().implicitly_converted(TypeName.uint_type()))
        else:
            return tgt.clone().index(start_offset).assign(self.get_loc_expr().implicitly_converted(TypeName.uint_type()))


class EncryptionExpression(ReclassifyExpr):
    def __init__(self, expr: Expression, privacy: 'PrivacyLabelExpr'):
        if isinstance(privacy, Identifier):
            privacy = IdentifierExpr(privacy)
        super().__init__(expr, privacy)
        self.annotated_type = AnnotatedTypeName.cipher_type()


class Statement(AST):

    def __init__(self):
        super().__init__()
        # set by alias analysis
        self.before_analysis: PartitionState = None
        self.after_analysis: PartitionState = None
        # set by parent setter
        self.function: ConstructorOrFunctionDefinition = None

        # set by circuit helper
        self.pre_statements = []

        self.has_side_effects = False

    def replaced_with(self, replacement: 'Statement') -> 'Statement':
        repl = super().replaced_with(replacement)
        assert isinstance(repl, Statement)
        repl.before_analysis = self.before_analysis
        repl.after_analysis = self.after_analysis
        repl.function = self.function
        repl.pre_statements = self.pre_statements
        return repl


class CircuitComputationStatement(Statement):
    def __init__(self, var: HybridArgumentIdf):
        super().__init__()
        self.idf = var.clone()


class IfStatement(Statement):

    def __init__(self, condition: Expression, then_branch: 'Block', else_branch: 'Block'):
        super().__init__()
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.condition = f(self.condition)
        self.then_branch = f(self.then_branch)
        self.else_branch = f(self.else_branch)


class ReturnStatement(Statement):

    def __init__(self, expr: Expression):
        super().__init__()
        self.expr = expr

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.expr = f(self.expr)


class SimpleStatement(Statement):
    pass


class ExpressionStatement(SimpleStatement):

    def __init__(self, expr: Expression):
        super().__init__()
        self.expr = expr

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.expr = f(self.expr)


class RequireStatement(SimpleStatement):

    def __init__(self, condition: Expression, unmodified_code: Optional[str] = None):
        super().__init__()
        self.condition = condition
        self.unmodified_code = self.code() if unmodified_code is None else unmodified_code

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.condition = f(self.condition)


class AssignmentStatement(SimpleStatement):

    def __init__(self, lhs: LocationExpr, rhs: Expression):
        super().__init__()
        self.lhs = lhs
        self.rhs = rhs

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.lhs = f(self.lhs)
        self.rhs = f(self.rhs)


class CircuitInputStatement(AssignmentStatement):
    pass


class StatementList(Statement):
    def __init__(self, statements: List[Statement]):
        super().__init__()
        self.statements = statements

        # Special case, if processing a statement returns a list of statements,
        # all statements will be integrated into this block

    def process_children(self, f: Callable[['AST'], 'AST']):
        new_stmts = []
        for idx, stmt in enumerate(self.statements):
            new_stmt = f(stmt)
            if new_stmt is not None:
                if isinstance(new_stmt, List):
                    new_stmts += new_stmt
                else:
                    new_stmts.append(new_stmt)
        self.statements = new_stmts

    def __getitem__(self, key: int) -> Statement:
        return self.statements[key]


class Block(StatementList):

    def clone(self) -> 'Block':
        from zkay.zkay_ast.visitor.deep_copy import deep_copy
        return deep_copy(self, with_types=True, with_analysis=True)


class LabeledBlock(StatementList):
    def __init__(self, statements: List[Statement], label: str):
        super().__init__(statements)
        self.label = label


class IndentBlock(StatementList):
    def __init__(self, name: str, statements: List[Statement]):
        super().__init__(statements)
        self.name = name


class TypeName(AST):
    __metaclass__ = abc.ABCMeta

    @staticmethod
    def bool_type():
        return ElementaryTypeName('bool')

    @staticmethod
    def uint_type():
        return ElementaryTypeName('uint')

    @staticmethod
    def address_type():
        return AddressTypeName()

    @staticmethod
    def address_payable_type():
        return AddressPayableTypeName()

    @staticmethod
    def void_type():
        return TupleType([])

    @staticmethod
    def cipher_type():
        return CipherText()

    @staticmethod
    def rnd_type():
        return Randomness()

    @staticmethod
    def key_type():
        return Key()

    @staticmethod
    def proof_type():
        # TODO correct type
        return Proof()

    @property
    def size_in_uints(self):
        return 1

    def is_primitive_type(self):
        return self == TypeName.bool_type() or self == TypeName.uint_type() or self == TypeName.address_type() or self == TypeName.address_payable_type()

    def can_be_private(self):
        return self == TypeName.bool_type() or self == TypeName.uint_type()

    def clone(self) -> 'TypeName':
        raise NotImplementedError()

    def __eq__(self, other):
        raise NotImplementedError()


class ElementaryTypeName(TypeName):

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def clone(self) -> 'ElementaryTypeName':
        return ElementaryTypeName(self.name)

    def __eq__(self, other):
        if isinstance(other, ElementaryTypeName):
            return self.name == other.name
        return False


class UserDefinedTypeName(TypeName):
    def __init__(self, names: List[Identifier], target: Optional[Union['ContractDefinition', 'StructDefinition']] = None):
        super().__init__()
        self.names = names
        self.target = target

    def clone(self) -> 'UserDefinedTypeName':
        return UserDefinedTypeName(self.names.copy(), self.target)

    def __eq__(self, other):
        return isinstance(other, UserDefinedTypeName) and all(e[0].name == e[1].name for e in zip(self.names, other.names))


class StructTypeName(UserDefinedTypeName):
    def clone(self) -> 'StructTypeName':
        return StructTypeName(self.names.copy(), self.target)


class ContractTypeName(UserDefinedTypeName):
    def clone(self) -> 'ContractTypeName':
        return ContractTypeName(self.names.copy(), self.target)


class AddressTypeName(UserDefinedTypeName):
    def __init__(self):
        super().__init__([Identifier('<address>')], None)

    def clone(self) -> 'UserDefinedTypeName':
        return AddressTypeName()

    def __eq__(self, other):
        return isinstance(other, AddressTypeName)


class AddressPayableTypeName(UserDefinedTypeName):
    def __init__(self):
        super().__init__([Identifier('<address_payable>')], None)

    def clone(self) -> 'UserDefinedTypeName':
        return AddressPayableTypeName()

    def __eq__(self, other):
        return isinstance(other, AddressPayableTypeName)


class Mapping(TypeName):

    def __init__(self, key_type: ElementaryTypeName, key_label: Optional[Identifier], value_type: 'AnnotatedTypeName'):
        super().__init__()
        self.key_type = key_type
        self.key_label: Union[str, Optional[Identifier]] = key_label
        self.value_type = value_type
        # set by type checker: instantiation of the key by IndexExpr
        self.instantiated_key: Expression = None

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.key_type = f(self.key_type)
        if isinstance(self.key_label, Identifier):
            self.key_label = f(self.key_label)
        self.value_type = f(self.value_type)

    def clone(self) -> 'Mapping':
        from zkay.zkay_ast.visitor.deep_copy import deep_copy
        return deep_copy(self)

    def __eq__(self, other):
        if isinstance(other, Mapping):
            return self.key_type == other.key_type and self.value_type == other.value_type
        else:
            return False


class Array(TypeName):

    def __init__(self, value_type: 'AnnotatedTypeName', expr: Union[int, Expression] = None):
        super().__init__()
        self.value_type = value_type
        self.expr = NumberLiteralExpr(expr) if isinstance(expr, int) else expr

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.value_type = f(self.value_type)
        self.expr = f(self.expr)

    def clone(self) -> 'Array':
        return Array(self.value_type.clone(), self.expr)

    @property
    def size_in_uints(self):
        if self.expr is None or not isinstance(self.expr, NumberLiteralExpr):
            return -1
        else:
            return self.expr.value

    def __eq__(self, other):
        if not isinstance(other, Array):
            return False
        if self.value_type == other.value_type and isinstance(self.expr, NumberLiteralExpr) and isinstance(other.expr, NumberLiteralExpr) and self.expr.value == other.expr.value:
            return True
        if self.value_type == other.value_type and self.expr is None and other.expr is None:
            return True
        return False


class CipherText(Array):
    def __init__(self):
        super().__init__(AnnotatedTypeName.uint_all(), NumberLiteralExpr(cfg.cipher_len))

    def __eq__(self, other):
        return isinstance(other, CipherText)


class Randomness(Array):
    def __init__(self):
        if cfg.randomness_len is None:
            super().__init__(AnnotatedTypeName.uint_all(), None)
        else:
            super().__init__(AnnotatedTypeName.uint_all(), NumberLiteralExpr(cfg.randomness_len))

    def __eq__(self, other):
        return isinstance(other, Randomness)


class Key(Array):
    def __init__(self):
        super().__init__(AnnotatedTypeName.uint_all(), NumberLiteralExpr(cfg.key_len))

    def __eq__(self, other):
        return isinstance(other, Key)


class Proof(Array):
    def __init__(self):
        super().__init__(AnnotatedTypeName.uint_all(), NumberLiteralExpr(cfg.proof_len))

    def __eq__(self, other):
        return isinstance(other, Proof)


class TupleType(TypeName):
    """
    Does not appear in the syntax, but is necessary for type checking
    """

    @staticmethod
    def ensure_tuple(t: 'AnnotatedTypeName'):
        if isinstance(t.type_name, TupleType):
            return t
        else:
            return TupleType([t])

    def __init__(self, types: List['AnnotatedTypeName']):
        super().__init__()
        self.types = types

    def __len__(self):
        return len(self.types)

    def __iter__(self):
        """
        Make this class iterable, by iterating over its types
        """
        return self.types.__iter__()

    def __getitem__(self, i: int):
        return self.types[i]

    def check_component_wise(self, other, f):
        if isinstance(other, TupleType):
            if len(self) != len(other):
                return False
            else:
                for i in range(len(self)):
                    if not f(self[i], other[i]):
                        return False
                return True
        else:
            return False

    def perfect_privacy_match(self, other):
        def privacy_match(self: AnnotatedTypeName, other: AnnotatedTypeName):
            return self.privacy_annotation == other.privacy_annotation

        self.check_component_wise(other, privacy_match)

    def clone(self) -> 'TupleType':
        return TupleType(list(map(AnnotatedTypeName.clone, self.types)))

    def __eq__(self, other):
        return self.check_component_wise(other, lambda x, y: x == y)


class FunctionTypeName(TypeName):
    def __init__(self, parameters: List['Parameter'], modifiers: List[str], return_parameters: List['Parameter']):
        super().__init__()
        self.parameters = parameters
        self.modifiers = modifiers
        self.return_parameters = return_parameters

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.parameters[:] = map(f, self.parameters)
        self.return_parameters[:] = map(f, self.return_parameters)

    def clone(self) -> 'FunctionTypeName':
        # TODO deep copy if required
        return FunctionTypeName(self.parameters, self.modifiers, self.return_parameters)

    def __eq__(self, other):
        return isinstance(other, FunctionTypeName) and self.parameters == other.parameters and \
               self.modifiers == other.modifiers and self.return_parameters == other.return_parameters


class AnnotatedTypeName(AST):

    def __init__(self, type_name: TypeName, privacy_annotation: Optional[Expression] = None, old_priv_text: str = ''):
        super().__init__()
        self.type_name = type_name
        self.had_privacy_annotation = privacy_annotation is not None
        self.old_priv_text = old_priv_text
        if self.had_privacy_annotation:
            self.privacy_annotation = privacy_annotation
        else:
            self.privacy_annotation = AllExpr()

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.type_name = f(self.type_name)
        self.privacy_annotation = f(self.privacy_annotation)

    def clone(self) -> 'AnnotatedTypeName':
        assert not self.privacy_annotation is None
        at = AnnotatedTypeName(self.type_name.clone(), self.privacy_annotation.clone(), self.old_priv_text)
        at.had_privacy_annotation = self.had_privacy_annotation
        return at

    def __eq__(self, other):
        if isinstance(other, AnnotatedTypeName):
            return self.type_name == other.type_name and self.privacy_annotation == other.privacy_annotation
        else:
            return False

    def is_public(self):
        return self.privacy_annotation.is_all_expr()

    def is_private(self):
        return not self.is_public()

    def is_address(self) -> bool:
        return self.type_name == TypeName.address_type() or self.type_name == TypeName.address_payable_type()

    @staticmethod
    def uint_all():
        return AnnotatedTypeName(TypeName.uint_type())

    @staticmethod
    def bool_all():
        return AnnotatedTypeName(TypeName.bool_type())

    @staticmethod
    def address_all():
        return AnnotatedTypeName(TypeName.address_type())

    @staticmethod
    def void_all():
        return AnnotatedTypeName(TypeName.void_type())

    @staticmethod
    def cipher_type():
        return AnnotatedTypeName(TypeName.cipher_type())

    @staticmethod
    def key_type():
        return AnnotatedTypeName(TypeName.key_type())

    @staticmethod
    def proof_type():
        return AnnotatedTypeName(TypeName.proof_type())

    @staticmethod
    def all(type: TypeName):
        return AnnotatedTypeName(type, Expression.all_expr())

    @staticmethod
    def me(type: TypeName):
        return AnnotatedTypeName(type, Expression.me_expr())

    @staticmethod
    def array_all(value_type: 'AnnotatedTypeName', *length: int):
        t = value_type
        for l in length:
            t = AnnotatedTypeName(Array(t, NumberLiteralExpr(l)))
        return t


class VariableDeclaration(AST):

    def __init__(self, keywords: List[str], annotated_type: AnnotatedTypeName, idf: Identifier, storage_location: Optional[str] = None):
        super().__init__()
        self.keywords = keywords
        self.annotated_type = annotated_type
        self.idf = idf
        self.storage_location = storage_location

        self.is_final = 'final' in self.keywords

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.annotated_type = f(self.annotated_type)
        self.idf = f(self.idf)


class VariableDeclarationStatement(SimpleStatement):

    def __init__(self, variable_declaration: VariableDeclaration, expr: Optional[Expression] = None):
        """

        :param variable_declaration:
        :param expr: can be None
        """
        super().__init__()
        self.variable_declaration = variable_declaration
        self.expr = expr

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.variable_declaration = f(self.variable_declaration)
        self.expr = f(self.expr)


class Parameter(AST):

    def __init__(
            self,
            keywords: List[str],
            annotated_type: AnnotatedTypeName,
            idf: Identifier,
            storage_location: Optional[str] = None,
            original_type: Optional[AnnotatedTypeName] = None):
        super().__init__()
        self.keywords = keywords
        self.annotated_type = annotated_type
        self.idf = idf
        self.storage_location = storage_location
        self.original_type = original_type

        self.is_final = 'final' in self.keywords

    def copy(self) -> 'Parameter':
        return Parameter(self.keywords, self.annotated_type.clone(), self.idf.clone() if self.idf else None, self.storage_location, self.original_type)

    def with_changed_storage(self, match_storage: str, new_storage: str) -> 'Parameter':
        if self.storage_location == match_storage:
            self.storage_location = new_storage
        return self

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.annotated_type = f(self.annotated_type)
        self.idf = f(self.idf)


class ConstructorOrFunctionDefinition(AST):

    def __init__(self, parameters: List[Parameter], modifiers: List[str], body: Block):
        super().__init__()
        self.parameters = parameters
        self.modifiers = modifiers
        self.body = body

        # specify parent type
        self.parent: ContractDefinition = None

        self.unambiguous_name: Optional[str] = None

        self.called_functions: OrderedDict[ConstructorOrFunctionDefinition, None] = OrderedDict()
        self.is_recursive = False
        self.has_static_body = True
        self.can_be_private = True

        # True if this function contains private expressions
        self.requires_verification = False

        # True if this function is public and either requires verification or has private arguments
        self.requires_verification_when_external = False

        self.has_side_effects = not ('pure' in self.modifiers or 'view' in self.modifiers)
        self.can_be_external = not ('private' in self.modifiers or 'internal' in self.modifiers)
        self.is_payable = 'payable' in self.modifiers

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.parameters[:] = map(f, self.parameters)
        self.body = f(self.body)

    def replaced_with(self, replacement: 'ConstructorOrFunctionDefinition') -> 'ConstructorOrFunctionDefinition':
        replacement: ConstructorOrFunctionDefinition = super().replaced_with(replacement)
        replacement.called_functions = self.called_functions
        replacement.is_recursive = self.is_recursive
        replacement.has_static_body = self.has_static_body
        replacement.requires_verification = self.requires_verification
        replacement.requires_verification_when_external = self.requires_verification_when_external
        replacement.can_be_private = self.can_be_private
        replacement.unambiguous_name = self.unambiguous_name
        return replacement

    def add_param(self, t: Union[TypeName, AnnotatedTypeName], idf: Union[str, Identifier], ref_storage_loc: str = 'memory'):
        t = t if isinstance(t, AnnotatedTypeName) else AnnotatedTypeName(t)
        idf = Identifier(idf) if isinstance(idf, str) else idf.clone()
        storage_loc = '' if t.type_name.is_primitive_type() else ref_storage_loc
        self.parameters.append(Parameter([], t, idf, storage_loc))
        self.parameters[-1].original_type = t

    @property
    def name(self):
        if isinstance(self, ConstructorDefinition):
            return 'constructor'
        else:
            assert isinstance(self, FunctionDefinition)
            return self.idf.name


class FunctionDefinition(ConstructorOrFunctionDefinition):

    def __init__(
            self,
            idf: Identifier,
            parameters: List[Parameter],
            modifiers: List[str],
            return_parameters: List[Parameter],
            body: Block):
        super().__init__(parameters, modifiers, body)
        # set fields
        self.idf = idf
        self.return_parameters = return_parameters if return_parameters else []
        self.annotated_type: AnnotatedTypeName = AnnotatedTypeName(FunctionTypeName(self.parameters, self.modifiers, self.return_parameters))
        self.original_body = body

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.idf = f(self.idf)
        self.parameters[:] = map(f, self.parameters)
        self.return_parameters[:] = map(f, self.return_parameters)
        self.body = f(self.body)

    def get_return_type(self):
        if len(self.return_parameters) == 0:
            return None
        elif len(self.return_parameters) == 1:
            return self.return_parameters[0].annotated_type
        else:
            raise AstException(f'Multiple return types are not yet supported', self)

    def get_parameter_types(self):
        types = [p.annotated_type for p in self.parameters]
        return TupleType(types)


class ConstructorDefinition(ConstructorOrFunctionDefinition):

    def __init__(self, parameters: List[Parameter], modifiers: List[str], body: Block):
        super().__init__(parameters, modifiers, body)

    def as_function(self):
        return self.replaced_with(FunctionDefinition(Identifier(self.name), self.parameters, self.modifiers, [], self.body))


class StateVariableDeclaration(AST):

    def __init__(self, annotated_type: AnnotatedTypeName, keywords: List[str], idf: Identifier, expr: Optional[Expression]):
        super().__init__()
        self.annotated_type = annotated_type
        self.keywords = keywords
        self.idf = idf
        self.expr = expr

        self.is_final = 'final' in self.keywords

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.annotated_type = f(self.annotated_type)
        self.idf = f(self.idf)
        self.expr = f(self.expr)


class StructDefinition(AST):
    def __init__(self, idf: Identifier, members: List[VariableDeclaration]):
        super().__init__()
        self.idf = idf
        self.members = members

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.idf = f(self.idf)
        self.members[:] = map(f, self.members)


class ContractDefinition(AST):

    def __init__(
            self,
            idf: Identifier,
            state_variable_declarations: List[StateVariableDeclaration],
            constructor_definitions: List[ConstructorDefinition],
            function_definitions: List[FunctionDefinition],
            struct_definitions: Optional[List[StructDefinition]] = None):
        super().__init__()
        self.idf = idf
        self.state_variable_declarations = state_variable_declarations
        self.constructor_definitions = constructor_definitions
        self.function_definitions = function_definitions
        self.struct_definitions = [] if struct_definitions is None else struct_definitions

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.idf = f(self.idf)
        self.state_variable_declarations[:] = map(f, self.state_variable_declarations)
        self.constructor_definitions[:] = map(f, self.constructor_definitions)
        self.function_definitions[:] = map(f, self.function_definitions)
        self.struct_definitions[:] = map(f, self.struct_definitions)

    def __getitem__(self, key: str):
        if key == 'constructor':
            if len(self.constructor_definitions) == 0:
                # return empty constructor
                c = ConstructorDefinition([], [], Block([]))
                c.parent = self
                return c
            elif len(self.constructor_definitions) == 1:
                return self.constructor_definitions[0]
            else:
                raise ValueError('Multiple constructors exist')
        else:
            d_identifier = self.names[key]
            return d_identifier.parent


class SourceUnit(AST):

    def __init__(self, pragma_directive: str, contracts: List[ContractDefinition], used_contracts: Optional[List[str]] = None):
        super().__init__()
        self.pragma_directive = pragma_directive
        self.contracts = contracts
        self.used_contracts = [] if used_contracts is None else used_contracts

        self.original_code: List[str] = []

    def process_children(self, f: Callable[['AST'], 'AST']):
        self.contracts[:] = map(f, self.contracts)

    def __getitem__(self, key: str):
        c_identifier = self.names[key]
        c = c_identifier.parent
        assert (isinstance(c, ContractDefinition))
        return c


PrivacyLabelExpr = Union[MeExpr, AllExpr, Identifier]
TargetDefinition = Union[VariableDeclaration, Parameter, FunctionDefinition, StateVariableDeclaration, StructDefinition, ContractDefinition]
InstanceTarget = Tuple[Union[VariableDeclaration, Parameter, StateVariableDeclaration], Optional[Identifier]]

# UTIL FUNCTIONS


def indent(s: str):
    return textwrap.indent(s, cfg.indentation)


# EXCEPTIONS


def get_code_error_msg(line: int, column: int, code: List[str], ctr: Optional[ContractDefinition] = None,
                       fct: Optional[FunctionDefinition] = None, stmt: Optional[Statement] = None):
    assert line <= len(code)

    # Print Location
    error_msg = f'Line: {line};{column}'
    if fct is not None:
        assert ctr is not None
        error_msg += f', in function \'{fct.name}\' of contract \'{ctr.idf.name}\''
    elif ctr is not None:
        error_msg += f', in contract \'{ctr.idf.name}\''
    error_msg += '\n'

    start_line = line if stmt is None else stmt.line
    if start_line != -1:
        for line in range(start_line, line + 1):
            # replace tabs with 4 spaces for consistent output
            orig_line: str = code[line - 1]
            orig_line = orig_line.replace('\t', '    ')
            error_msg += f'{orig_line}\n'

        affected_line: str = code[line - 1]
        loc_string = ''.join('----' if c == '\t' else '-' for c in affected_line[:column - 1])
        return f'{error_msg}{loc_string}/'
    else:
        return error_msg


class AstException(Exception):
    """
    Generic exception for errors in an AST
    """

    def __init__(self, msg, ast):
        # Get surrounding statement
        if isinstance(ast, Expression):
            stmt = ast.statement
        elif isinstance(ast, Statement):
            stmt = ast
        else:
            stmt = None

        # Get surrounding function
        if stmt is not None:
            fct = stmt.function
        elif isinstance(ast, ConstructorOrFunctionDefinition):
            fct = ast
        else:
            fct = None

        # Get surrounding contract
        ctr = ast if fct is None else fct
        while ctr is not None and not isinstance(ctr, ContractDefinition):
            ctr = ctr.parent

        # Get source root
        root = ast if ctr is None else ctr
        while root is not None and not isinstance(root, SourceUnit):
            root = root.parent

        if root is None:
            error_msg = 'error'
        else:
            error_msg = get_code_error_msg(ast.line, ast.column, root.original_code, ctr, fct, stmt)

        super().__init__(f'\n{error_msg}\n{msg}')


# CODE GENERATION

class CodeVisitor(AstVisitor):

    def __init__(self, display_final=True):
        super().__init__('node-or-children')
        self.display_final = display_final

    def visit_list(self, l: List[Union[AST, str]], sep='\n'):
        if l is None:
            return 'None'

        def handle(e: Union[AST, str]):
            if isinstance(e, str):
                return e
            else:
                return self.visit(e)

        s = filter(None.__ne__, [handle(e) for e in l])
        s = sep.join(s)
        return s

    def visit_single_or_list(self, v: Union[List[AST], AST, str], sep='\n'):
        if isinstance(v, List):
            return self.visit_list(v, sep)
        elif isinstance(v, str):
            return v
        else:
            return self.visit(v)

    def visitAST(self, ast: AST):
        # should never be called
        raise NotImplementedError("Did not implement code generation for " + repr(ast))

    def visitComment(self, ast: Comment):
        if ast.text == '':
            return ''
        elif ast.text.find('\n') != -1:
            return f'/* {ast.text} */'
        else:
            return f'// {ast.text}'

    def visitIdentifier(self, ast: Identifier):
        return ast.name

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction):
            args = [self.visit(a) for a in ast.args]
            return ast.func.format_string().format(*args)
        else:
            f = self.visit(ast.func)
            a = self.visit_list(ast.args, ', ')
            return f'{f}({a})'

    def visitAssignmentExpr(self, ast: AssignmentExpr):
        lhs = self.visit(ast.lhs)
        rhs = self.visit(ast.rhs)
        return f'{lhs} = {rhs}'

    def visitBooleanLiteralExpr(self, ast: BooleanLiteralExpr):
        return str(ast.value).lower()

    def visitNumberLiteralExpr(self, ast: NumberLiteralExpr):
        return str(ast.value)

    def visitStringLiteralExpr(self, ast: StringLiteralExpr):
        return f'\'{ast.value}\''

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        return self.visit(ast.idf)

    def visitMemberAccessExpr(self, ast: MemberAccessExpr):
        return f'{self.visit(ast.expr)}.{self.visit(ast.member)}'

    def visitIndexExpr(self, ast: IndexExpr):
        return f'{self.visit(ast.arr)}[{self.visit(ast.key)}]'

    def visitMeExpr(self, _: MeExpr):
        return 'me'

    def visitAllExpr(self, _: AllExpr):
        return 'all'

    def visitReclassifyExpr(self, ast: ReclassifyExpr):
        e = self.visit(ast.expr)
        p = self.visit(ast.privacy)
        return f'reveal({e}, {p})'

    def visitIfStatement(self, ast: IfStatement):
        c = self.visit(ast.condition)
        t = self.visit_single_or_list(ast.then_branch)
        ret = f'if ({c}) {t}'
        if ast.else_branch:
            e = self.visit_single_or_list(ast.else_branch)
            ret += f'\n else {e}'
        return ret

    def visitReturnStatement(self, ast: ReturnStatement):
        if ast.expr:
            e = self.visit(ast.expr)
            return f'return {e};'
        else:
            return 'return;'

    def visitExpressionStatement(self, ast: ExpressionStatement):
        return self.visit(ast.expr) + ';'

    def visitRequireStatement(self, ast: RequireStatement):
        c = self.visit(ast.condition)
        return f'require({c});'

    def visitAssignmentStatement(self, ast: AssignmentStatement):
        if isinstance(ast.lhs, SliceExpr) and isinstance(ast.rhs, SliceExpr):
            assert ast.lhs.size == ast.rhs.size, "Slice ranges don't have same size"
            s = ''
            lexpr, rexpr = self.visit(ast.lhs.arr), self.visit(ast.rhs.arr)
            lbase = '' if ast.lhs.base is None else f'{self.visit(ast.lhs.base)} + '
            rbase = '' if ast.rhs.base is None else f'{self.visit(ast.rhs.base)} + '
            for i in range(ast.lhs.size):
                s += f'{lexpr}[{lbase}{ast.lhs.start_offset + i}] = {rexpr}[{rbase}{ast.rhs.start_offset + i}];\n'
            return s[:-1]
        else:
            lhs = self.visit(ast.lhs)
            rhs = self.visit(ast.rhs)
            return f'{lhs} = {rhs};'

    def visitCircuitComputationStatement(self, ast: CircuitComputationStatement):
        return None

    def handle_block(self, ast: StatementList):
        s = self.visit_list(ast.statements)
        s = indent(s)
        return s

    def visitStatementList(self, ast: StatementList):
        return self.visit_list(ast.statements)

    def visitBlock(self, ast: Block):
        return f'{{\n{self.handle_block(ast).rstrip()}\n}}'

    def visitIndentBlock(self, ast: IndentBlock):
        fstr = f"//{'<' * 12} {{}}{ast.name} {{}} {'>' * 12}\n"
        return f"{fstr.format('', 'BEGIN')}{self.handle_block(ast)}\n{fstr.format(' ', 'END ')}"

    def visitLabeledBlock(self, ast: LabeledBlock):
        return self.visit_list(ast.statements)

    def visitElementaryTypeName(self, ast: ElementaryTypeName):
        return ast.name

    def visitUserDefinedTypeName(self, ast: UserDefinedTypeName):
        return self.visit_list(ast.names, '.')

    def visitAddressTypeName(self, ast: AddressTypeName):
        return 'address'

    def visitAddressPayableTypeName(self, ast: AddressPayableTypeName):
        return 'address payable'

    def visitAnnotatedTypeName(self, ast: AnnotatedTypeName):
        t = self.visit(ast.type_name)
        if ast.old_priv_text != '':
            t = f'{t}/*{ast.old_priv_text}*/'
        p = self.visit(ast.privacy_annotation)
        if ast.had_privacy_annotation:
            return f'{t}@{p}'
        else:
            return t

    def visitMapping(self, ast: Mapping):
        k = self.visit(ast.key_type)
        if isinstance(ast.key_label, Identifier):
            label = '!' + self.visit(ast.key_label)
        else:
            label = f'/*!{ast.key_label}*/' if ast.key_label is not None else ''
        v = self.visit(ast.value_type)
        return f"mapping({k}{label} => {v})"

    def visitArray(self, ast: Array):
        t = self.visit(ast.value_type)
        if ast.expr is not None:
            e = self.visit(ast.expr)
        else:
            e = ''
        return f'{t}[{e}]'

    def visitTupleType(self, ast: TupleType):
        s = self.visit_list(ast.types, ', ')
        return f'({s})'

    def visitVariableDeclaration(self, ast: VariableDeclaration):
        keywords = [k for k in ast.keywords if self.display_final or k != 'final']
        k = ' '.join(keywords)
        t = self.visit(ast.annotated_type)
        s = '' if ast.storage_location is None else f' {ast.storage_location}'
        i = self.visit(ast.idf)
        return f'{k} {t}{s} {i}'.strip()

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        s = self.visit(ast.variable_declaration)
        if ast.expr:
            s += ' = ' + self.visit(ast.expr)
        s += ';'
        return s

    def visitParameter(self, ast: Parameter):
        if not self.display_final:
            f = None
        else:
            f = 'final' if 'final' in ast.keywords else None
        t = self.visit(ast.annotated_type)
        if ast.idf is None:
            i = None
        else:
            i = self.visit(ast.idf)

        description = [f, t, ast.storage_location, i]
        description = [d for d in description if d is not None]
        s = ' '.join(description)
        return s

    def visitFunctionDefinition(self, ast: FunctionDefinition):
        b = self.visit_single_or_list(ast.body)
        return self.function_definition_to_str(ast.idf, ast.parameters, ast.modifiers, ast.return_parameters, b)

    def function_definition_to_str(
            self,
            idf: Optional[Identifier],
            parameters: List[Union[Parameter, str]],
            modifiers: List[str],
            return_parameters: List[Parameter],
            body: str):
        if idf:
            i = self.visit(idf)
            definition = f'function {i}'
        else:
            definition = f'constructor'
        p = self.visit_list(parameters, ', ')
        m = ' '.join(modifiers)
        if m != '':
            m = f' {m}'
        r = self.visit_list(return_parameters, ' ')
        if r != '':
            r = f' returns ({r})'

        f = f"{definition}({p}){m}{r} {body}"
        return f

    def visitConstructorDefinition(self, ast: ConstructorDefinition):
        b = self.visit_single_or_list(ast.body)
        return self.function_definition_to_str(None, ast.parameters, ast.modifiers, [], b)

    def visitStructDefinition(self, ast: StructDefinition):
        # Define struct with members in order of descending size (to get maximum space savings through packing)
        members_by_descending_size = sorted(ast.members, key=lambda x: x.annotated_type.type_name.size_in_uints, reverse=True)
        body = '\n'.join([f'{self.visit(member)};' for member in members_by_descending_size])
        return f'struct {self.visit(ast.idf)} {{\n{indent(body)}\n}}'

    def visitStateVariableDeclaration(self, ast: StateVariableDeclaration):
        keywords = [k for k in ast.keywords if self.display_final or k != 'final']
        f = 'final ' if 'final' in keywords else ''
        t = self.visit(ast.annotated_type)
        k = ' '.join([k for k in keywords if k != 'final'])
        if k != '':
            k = f'{k} '
        i = self.visit(ast.idf)
        ret = f"{f}{t} {k}{i}".strip()
        if ast.expr:
            ret += ' = ' + self.visit(ast.expr)
        return ret + ';'

    @staticmethod
    def contract_definition_to_str(
            idf: Identifier,
            state_vars: List[str],
            constructors: List[str],
            functions: List[str],
            structs: List[str]):

        i = str(idf)
        structs = '\n\n'.join(structs)
        state_vars = '\n'.join(state_vars)
        constructors = '\n\n'.join(constructors)
        functions = '\n\n'.join(functions)
        body = '\n\n'.join(filter(''.__ne__, [structs, state_vars, constructors, functions]))
        body = indent(body)
        return f"contract {i} {{\n{body}\n}}"

    def visitContractDefinition(self, ast: ContractDefinition):
        state_vars = [self.visit(e) for e in ast.state_variable_declarations]
        constructors = [self.visit(e) for e in ast.constructor_definitions]
        functions = [self.visit(e) for e in ast.function_definitions]
        structs = [self.visit(e) for e in ast.struct_definitions]

        return self.contract_definition_to_str(
            ast.idf,
            state_vars,
            constructors,
            functions,
            structs)

    def visitSourceUnit(self, ast: SourceUnit):
        p = ast.pragma_directive
        contracts = self.visit_list(ast.contracts)
        lfstr = 'import "{}";'
        return '\n\n'.join(filter(''.__ne__, [p, linesep.join([lfstr.format(uc) for uc in ast.used_contracts]), contracts]))
