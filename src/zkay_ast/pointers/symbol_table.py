from zkay_ast.ast import AST, SourceUnit, ContractDefinition, FunctionDefinition, VariableDeclaration, Statement, \
	SimpleStatement, IdentifierExpr, Block, Mapping
from zkay_ast.visitor.visitor import AstVisitor


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

	def visitContractDefinition(self, ast: ContractDefinition):
		state_vars = {d.idf.name: d.idf for d in ast.state_variable_declarations}
		funcs = {f.idf.name: f.idf for f in ast.function_definitions}
		ast.names = merge_dicts(state_vars, funcs)

	def visitFunctionDefinition(self, ast: FunctionDefinition):
		ast.names = {p.idf.name: p.idf for p in ast.parameters}

	def visitConstructorDefinition(self, ast):
		self.visitFunctionDefinition(ast)

	def visitVariableDeclaration(self, ast: VariableDeclaration):
		ast.names = {ast.idf.name: ast.idf}

	def visitBlock(self, ast: Statement):
		ast.names = collect_children_names(ast)

	def visitSimpleStatement(self, ast: SimpleStatement):
		ast.names = collect_children_names(ast)

	def visitMapping(self, ast: Mapping):
		ast.names = {}
		if ast.key_label:
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
		raise ValueError(f'Undefined identifier {name}')

	def visitIdentifierExpr(self, ast: IdentifierExpr):
		idf = self.find_identifier_declaration(ast, ast.idf.name)
		ast.target = idf.parent
		if isinstance(ast.target, FunctionDefinition):
			raise NotImplementedError('Currently not handling function calls')
		assert(ast.target is not None)
