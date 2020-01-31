from zkay.zkay_ast.ast import AST, SourceUnit, ContractDefinition, VariableDeclaration, \
    SimpleStatement, IdentifierExpr, Block, Mapping, Identifier, Comment, MemberAccessExpr, IndexExpr, LocationExpr, \
    StructDefinition, UserDefinedTypeName, StatementList, Array, ConstructorOrFunctionDefinition, EnumDefinition, EnumValue, \
    NamespaceDefinition
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


def get_builtin_globals():
    sf = SymbolTableFiller()
    return sf.get_builtin_globals()


class SymbolTableFiller(AstVisitor):
    def get_builtin_globals(self):
        global_defs = [d for d in [getattr(GlobalDefs, var) for var in vars(GlobalDefs) if not var.startswith('__')]]
        for d in global_defs:
            self.visit(d)
        global_defs = {d.idf.name: d.idf for d in global_defs}
        global_vars = {d.idf.name: d.idf for d in [getattr(GlobalVars, var) for var in vars(GlobalVars) if not var.startswith('__')]}
        return merge_dicts(global_defs, global_vars)

    def visitSourceUnit(self, ast: SourceUnit):
        ast.names = {c.idf.name: c.idf for c in ast.contracts}
        ast.names.update(self.get_builtin_globals())

    def visitContractDefinition(self, ast: ContractDefinition):
        state_vars = {d.idf.name: d.idf for d in ast.state_variable_declarations if not isinstance(d, Comment)}
        funcs = {}
        for f in ast.function_definitions:
            if f.idf.name in funcs:
                raise UnknownIdentifierException(f'Zkay does not currently support method overloading.', f)
            funcs[f.idf.name] = f.idf
        structs = {s.idf.name: s.idf for s in ast.struct_definitions}
        enums = {e.idf.name: e.idf for e in ast.enum_definitions}
        ast.names = merge_dicts(state_vars, funcs, structs, enums)

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        ast.names = {p.idf.name: p.idf for p in ast.parameters}

    def visitStructDefinition(self, ast: StructDefinition):
        ast.names = {m.idf.name: m.idf for m in ast.members}

    def visitEnumDefinition(self, ast: EnumDefinition):
        ast.names = {v.idf.name: v.idf for v in ast.values}

    def visitEnumValue(self, ast: EnumValue):
        ast.names = {ast.idf.name: ast.idf}

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
            type_def = self.find_identifier_declaration(ast, ast.names[0].name).parent
            for idf in ast.names[1:]:
                type_def = type_def.names[idf.name].parent
            ast.target = type_def
        except UnknownIdentifierException as e:
            pass

    def visitMemberAccessExpr(self, ast: MemberAccessExpr):
        assert isinstance(ast.expr, LocationExpr), "Function call return value member access not yet supported"
        if isinstance(ast.expr.target, NamespaceDefinition):
            ast.target = ast.expr.target.names[ast.member.name].parent
        else:
            t = ast.expr.target.annotated_type.type_name
            if isinstance(t, Array):
                assert ast.member.name == 'length'
                ast.target = array_length_member
            else:
                assert isinstance(t, UserDefinedTypeName)
                if t.target is None:
                    t = t.clone()
                    t.parent = ast
                    self.visit(t)
                if t.target is not None:
                    ast.target = t.target.names[ast.member.name].parent

    def visitIndexExpr(self, ast: IndexExpr):
        assert isinstance(ast.arr, LocationExpr), "Function call return value indexing not yet supported"
        source_t = ast.arr.target.annotated_type.type_name
        ast.target = VariableDeclaration([], source_t.value_type, Identifier(''))
