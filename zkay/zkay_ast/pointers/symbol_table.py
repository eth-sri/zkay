from zkay.zkay_ast.ast import AST, SourceUnit, ContractDefinition, FunctionDefinition, VariableDeclaration, \
    SimpleStatement, IdentifierExpr, Block, Mapping, Identifier, Comment, MemberAccessExpr, IndexExpr, LocationExpr, \
    StructDefinition, UserDefinedTypeName, StatementList, Array, Parameter
from zkay.zkay_ast.global_defs import GlobalDefs, GlobalVars, array_length_member
from zkay.zkay_ast.pointers.pointer_exceptions import UnknownIdentifierException
from zkay.zkay_ast.visitor.visitor import AstVisitor


def fill_symbol_table(ast):
    v = SymbolTableFiller()
    v.visit(ast)


def link_symbol_table(ast):
    v = SymbolTableLinker()
    v.visit(ast)


def link_identifiers(ast):
    fill_symbol_table(ast)
    link_symbol_table(ast)


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict.
    Report error on conflicting keys.
    """
    result = {}
    for dictionary in dict_args:
        for key, value in dictionary.items():
            if key in result and result[key] != value:
                raise ValueError('Conflicting definitions for', key)
            result[key] = value
    return result


def collect_children_names(ast: AST):
    names = [c.names for c in ast.children() if not isinstance(c, Block)]
    return merge_dicts(*names)


class SymbolTableFiller(AstVisitor):

    def visitSourceUnit(self, ast: SourceUnit):
        ast.names = {c.idf.name: c.idf for c in ast.contracts}
        global_defs = [d for d in [getattr(GlobalDefs, var) for var in vars(GlobalDefs) if not var.startswith('__')]]
        for d in global_defs:
            self.visit(d)
        ast.names.update({d.idf.name: d.idf for d in global_defs})

    def visitContractDefinition(self, ast: ContractDefinition):
        state_vars = {d.idf.name: d.idf for d in ast.state_variable_declarations if not isinstance(d, Comment)}
        state_vars.update({d.idf.name: d.idf for d in [getattr(GlobalVars, var) for var in vars(GlobalVars) if not var.startswith('__')]})
        funcs = {f.idf.name: f.idf for f in ast.function_definitions}
        structs = {s.idf.name: s.idf for s in ast.struct_definitions}
        ast.names = merge_dicts(state_vars, funcs, structs)

    def visitFunctionDefinition(self, ast: FunctionDefinition):
        ast.names = {p.idf.name: p.idf for p in ast.parameters}

    def visitConstructorDefinition(self, ast):
        self.visitFunctionDefinition(ast)

    def visitStructDefinition(self, ast: StructDefinition):
        ast.names = {m.idf.name: m.idf for m in ast.members}

    def visitVariableDeclaration(self, ast: VariableDeclaration):
        ast.names = {ast.idf.name: ast.idf}

    def visitStatementList(self, ast: StatementList):
        ast.names = collect_children_names(ast)

    def visitSimpleStatement(self, ast: SimpleStatement):
        ast.names = collect_children_names(ast)

    def visitMapping(self, ast: Mapping):
        ast.names = {}
        if isinstance(ast.key_label, Identifier):
            ast.names = {ast.key_label.name: ast.key_label}


class SymbolTableLinker(AstVisitor):

    @staticmethod
    def find_identifier_declaration(ast: AST, name: str):
        ancestor = ast.parent
        while ancestor:
            if name in ancestor.names:
                # found name
                return ancestor.names[name]
            ancestor = ancestor.parent
        raise UnknownIdentifierException(f'Undefined identifier {name}', ast)

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        idf = self.find_identifier_declaration(ast, ast.idf.name)
        ast.target = idf.parent
        assert (ast.target is not None)

    def visitUserDefinedTypeName(self, ast: UserDefinedTypeName):
        try:
            idf = self.find_identifier_declaration(ast, ast.names[0].name).parent
            for name in ast.names[1:]:
                idf = idf.names[name].parent
            ast.target = idf
        except UnknownIdentifierException as e:
            pass

    def visitMemberAccessExpr(self, ast: MemberAccessExpr):
        assert isinstance(ast.expr, LocationExpr), "Function call return value member access not yet supported"
        t = ast.expr.target.annotated_type.type_name
        if isinstance(t, Array):
            assert ast.member.name == 'length'
            ast.target = array_length_member
        else:
            assert isinstance(t, UserDefinedTypeName)
            if t.target is None:
                t = t.clone()
                t.parent = ast.expr.target
                self.visit(t)
            if t.target is not None:
                ast.target = t.target.names[ast.member.name].parent

    def visitIndexExpr(self, ast: IndexExpr):
        assert isinstance(ast.arr, LocationExpr), "Function call return value indexing not yet supported"
        source_t = ast.arr.target.annotated_type.type_name
        ast.target = VariableDeclaration([], source_t.value_type, Identifier(''))
