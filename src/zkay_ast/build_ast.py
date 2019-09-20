from antlr4.Token import CommonToken

from zkay_ast.ast import StateVariableDeclaration, ContractDefinition, FunctionDefinition, NumberLiteralExpr, \
	BooleanLiteralExpr, ConstructorDefinition, FunctionCallExpr, ExpressionStatement, IdentifierExpr, ReclassifyExpr, \
	BuiltinFunction
from type_check.type_exceptions import RequireException, ReclassifyException
from solidity_parser.emit import Emitter
from solidity_parser.generated.SolidityParser import SolidityParser, ParserRuleContext, CommonTokenStream
from solidity_parser.generated.SolidityVisitor import SolidityVisitor
from solidity_parser.parse import MyParser
import zkay_ast.ast as ast


def build_ast_from_parse_tree(parse_tree: ParserRuleContext, tokens: CommonTokenStream) -> ast.AST:
	v = BuildASTVisitor(tokens)
	return v.visit(parse_tree)


def build_ast(code):
	p = MyParser(code)
	return build_ast_from_parse_tree(p.tree, p.tokens)


class BuildASTVisitor(SolidityVisitor):

	def __init__(self, tokens: CommonTokenStream):
		self.emitter = Emitter(tokens)

	def visitChildren(self, ctx: ParserRuleContext):
		# determine corresponding class name
		t = type(ctx).__name__
		t = t.replace('Context', '')

		# may be able to return the result for a SINGLE, UNNAMED CHILD without wrapping it in an object
		direct_unnamed = ['TypeName', 'ContractPart', 'StateMutability', 'Statement', 'SimpleStatement']
		if t in direct_unnamed:
			if ctx.getChildCount() != 1:
				raise TypeError(t + ' does not have a single, unnamed child')
			ret = self.handle_field(ctx.getChild(0))
			return ret

		# HANDLE ALL FIELDS of ctx
		d = ctx.__dict__

		# extract fields
		fields = d.keys()
		fields = [f for f in fields if not f.startswith('_')]
		ignore = ['parentCtx', 'invokingState', 'children', 'start', 'stop', 'exception', 'parser']
		fields = [f for f in fields if f not in ignore]

		# visit fields
		visited_fields = {}
		for f in fields:
			visited_fields[f] = self.handle_field(d[f])

		# may be able to return the result for a SINGLE, NAMED CHILD without wrapping it in an object
		direct = ['ModifierList', 'ParameterList', 'ReturnParameters', 'FunctionCallArguments']
		if t in direct:
			if len(visited_fields) != 1:
				raise TypeError(t + ' does not have a single, named child')
			key = list(visited_fields.keys())[0]
			return visited_fields[key]

		# CONSTRUCT AST FROM FIELDS
		if hasattr(ast, t):
			c = getattr(ast, t)
			# call initializer
			try:
				return c(**visited_fields)
			except TypeError as e:
				raise TypeError("Could not call initializer for " + t) from e
		else:
			# abort if not constructor found for this node type
			raise ValueError(t)

	def handle_field(self, field):
		if field is None:
			return None
		elif isinstance(field, list):
			return [self.handle_field(element) for element in field]
		elif isinstance(field, CommonToken):
			# text
			return field.text
		else:
			# other
			return self.visit(field)

	def visitBlock(self, ctx: SolidityParser.BlockContext):
		statements = [self.visit(s) for s in ctx.statements]
		for i in range(len(statements)):
			s = statements[i]

			# handle require
			if isinstance(s, ExpressionStatement):
				e = s.expr
				if isinstance(e, FunctionCallExpr):
					f = e.func
					if isinstance(f, IdentifierExpr):
						name = f.idf.name
						if name == 'require':
							if len(e.args) != 1:
								RequireException(f'Invalid number of arguments for require: {e}')
							r = ast.RequireStatement(e.args[0])
							statements[i] = r

			# handle assignment
			if isinstance(s, ast.ExpressionStatement):
				e = s.expr
				if isinstance(e, ast.AssignmentExpr):
					a = ast.AssignmentStatement(e.lhs, e.rhs)
					statements[i] = a

		return ast.Block(statements)

	def visitPragmaDirective(self, ctx: SolidityParser.PragmaDirectiveContext):
		return self.emitter.visit(ctx)

	# Visit a parse tree produced by SolidityParser#contractDefinition.
	def visitContractDefinition(self, ctx: SolidityParser.ContractDefinitionContext):
		identifier = self.visit(ctx.identifier())
		parts = [self.visit(c) for c in ctx.parts]
		state_vars = [p for p in parts if isinstance(p, StateVariableDeclaration)]
		constructors = [p for p in parts if isinstance(p, ConstructorDefinition)]
		functions = [p for p in parts if isinstance(p, FunctionDefinition)]
		return ContractDefinition(identifier, state_vars, constructors, functions)

	# Visit a parse tree produced by SolidityParser#NumberLiteralExpr.
	def visitNumberLiteralExpr(self, ctx: SolidityParser.NumberLiteralExprContext):
		v = int(ctx.getText())
		return NumberLiteralExpr(v)

	# Visit a parse tree produced by SolidityParser#BooleanLiteralExpr.
	def visitBooleanLiteralExpr(self, ctx: SolidityParser.BooleanLiteralExprContext):
		b = ctx.getText() == 'true'
		return BooleanLiteralExpr(b)

	def visitModifier(self, ctx: SolidityParser.ModifierContext):
		return ctx.getText()

	def visitIndexExpr(self, ctx: SolidityParser.IndexExprContext):
		f = BuiltinFunction('index')
		arr = self.visit(ctx.arr)
		index = self.visit(ctx.index)
		return FunctionCallExpr(f, [arr, index])

	def visitParenthesisExpr(self, ctx: SolidityParser.ParenthesisExprContext):
		f = BuiltinFunction('parenthesis')
		expr = self.visit(ctx.expr)
		return FunctionCallExpr(f, [expr])

	def visitSignExpr(self, ctx: SolidityParser.SignExprContext):
		f = BuiltinFunction('sign' + ctx.op.getText())
		expr = self.visit(ctx.expr)
		return FunctionCallExpr(f, expr)

	def visitNotExpr(self, ctx: SolidityParser.NotExprContext):
		f = BuiltinFunction('!')
		expr = self.visit(ctx.expr)
		return FunctionCallExpr(f, [expr])

	def _visitBinaryExpr(self, ctx):
		lhs = self.visit(ctx.lhs)
		rhs = self.visit(ctx.rhs)
		f = BuiltinFunction(ctx.op.text)
		return FunctionCallExpr(f, [lhs, rhs])

	def _visitBoolExpr(self, ctx):
		return self._visitBinaryExpr(ctx)

	def visitPowExpr(self, ctx: SolidityParser.PowExprContext):
		return self._visitBinaryExpr(ctx)

	def visitMultDivModExpr(self, ctx: SolidityParser.MultDivModExprContext):
		return self._visitBinaryExpr(ctx)

	def visitPlusMinusExpr(self, ctx:SolidityParser.PlusMinusExprContext):
		return self._visitBinaryExpr(ctx)

	def visitCompExpr(self, ctx:SolidityParser.CompExprContext):
		return self._visitBinaryExpr(ctx)

	def visitEqExpr(self, ctx: SolidityParser.EqExprContext):
		return self._visitBinaryExpr(ctx)

	def visitAndExpr(self, ctx: SolidityParser.AndExprContext):
		return self._visitBoolExpr(ctx)

	def visitOrExpr(self, ctx: SolidityParser.OrExprContext):
		return self._visitBoolExpr(ctx)

	def visitIteExpr(self, ctx: SolidityParser.IteExprContext):
		f = BuiltinFunction('ite')
		cond = self.visit(ctx.cond)
		then_expr = self.visit(ctx.then_expr)
		else_expr = self.visit(ctx.else_expr)
		return FunctionCallExpr(f, [cond, then_expr, else_expr])

	def visitFunctionCallExpr(self, ctx: SolidityParser.FunctionCallExprContext):
		func = self.visit(ctx.func)
		args = self.handle_field(ctx.args)

		if isinstance(func, IdentifierExpr):
			if func.idf.name == 'reveal':
				if len(args) != 2:
					ReclassifyException(f'Invalid number of arguments for reveal: {args}')
				return ReclassifyExpr(args[0], args[1])

		return FunctionCallExpr(func, args)
