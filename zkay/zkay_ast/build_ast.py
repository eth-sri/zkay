from antlr4.Token import CommonToken
from semantic_version import NpmSpec, Version

import zkay.zkay_ast.ast as ast

from zkay.config import cfg
from zkay.solidity_parser.parse import SyntaxException
from zkay.solidity_parser.emit import Emitter
from zkay.solidity_parser.generated.SolidityParser import SolidityParser, ParserRuleContext, CommonTokenStream
from zkay.solidity_parser.generated.SolidityVisitor import SolidityVisitor
from zkay.solidity_parser.parse import MyParser
from zkay.zkay_ast.ast import StateVariableDeclaration, ContractDefinition, NumberLiteralExpr, \
    BooleanLiteralExpr, StringLiteralExpr, FunctionCallExpr, ExpressionStatement, IdentifierExpr, \
    ReclassifyExpr, BuiltinFunction, IndexExpr


def build_ast_from_parse_tree(parse_tree: ParserRuleContext, tokens: CommonTokenStream, code: str) -> ast.AST:
    v = BuildASTVisitor(tokens, code)
    return v.visit(parse_tree)


def build_ast(code):
    p = MyParser(code)
    full_ast = build_ast_from_parse_tree(p.tree, p.tokens, code)
    assert isinstance(full_ast, ast.SourceUnit)
    full_ast.original_code = str(code).splitlines()
    return full_ast


class BuildASTVisitor(SolidityVisitor):

    def __init__(self, tokens: CommonTokenStream, code: str):
        self.emitter = Emitter(tokens)
        self.code = code

    def visit(self, tree):
        sub_ast = super().visit(tree)
        if isinstance(sub_ast, ast.AST):
            sub_ast.line = tree.start.line
            sub_ast.column = tree.start.column + 1
        return sub_ast

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

    def visitIdentifier(self, ctx: SolidityParser.IdentifierContext):
        name: str = ctx.name.text
        if name.startswith(cfg.reserved_name_prefix) or name.startswith(f'_{cfg.reserved_name_prefix}'):
            raise SyntaxException(f'Identifiers must not start with reserved prefix _?{cfg.reserved_name_prefix}', ctx, self.code)
        elif name.endswith(cfg.reserved_conflict_resolution_suffix):
            raise SyntaxException(f'Identifiers must not end with reserved suffix {cfg.reserved_name_prefix}', ctx, self.code)
        return ast.Identifier(name)

    def visitPragmaDirective(self, ctx: SolidityParser.PragmaDirectiveContext):
        return f'pragma {self.visit(ctx.pragma())};'

    def visitVersionPragma(self, ctx: SolidityParser.VersionPragmaContext):
        version = ctx.ver.getText().strip()
        spec = NpmSpec(version)
        name = self.handle_field(ctx.name)
        if name == 'zkay' and Version(cfg.zkay_version) not in spec:
            raise SyntaxException(f'Contract requires a different zkay version.\n'
                                  f'Current version is {cfg.zkay_version} but pragma zkay mandates {version}.',
                                  ctx.ver, self.code)
        elif name != 'zkay' and spec != cfg.zkay_solc_version_compatibility:
            # For backwards compatibility with older zkay versions
            assert name == 'solidity'
            raise SyntaxException(f'Contract requires solidity version {spec}, which is not compatible '
                                  f'with the current zkay version (requires {cfg.zkay_solc_version_compatibility}).',
                                  ctx.ver, self.code)

        return f'{name} {version}'

    # Visit a parse tree produced by SolidityParser#contractDefinition.
    def visitContractDefinition(self, ctx: SolidityParser.ContractDefinitionContext):
        identifier = self.visit(ctx.idf)
        if '$' in identifier.name:
            raise SyntaxException('$ is not allowed in zkay contract identifiers', ctx.idf, self.code)
        parts = [self.visit(c) for c in ctx.parts]
        state_vars = [p for p in parts if isinstance(p, StateVariableDeclaration)]
        cfdefs = [p for p in parts if isinstance(p, ast.ConstructorOrFunctionDefinition)]
        constructors = [p for p in cfdefs if p.is_constructor]
        functions = [p for p in cfdefs if p.is_function]
        enums = [p for p in parts if isinstance(p, ast.EnumDefinition)]
        return ContractDefinition(identifier, state_vars, constructors, functions, enums)

    def handle_fdef(self, ctx):
        if isinstance(ctx, SolidityParser.ConstructorDefinitionContext):
            idf, ret_params = None, None
        else:
            idf, ret_params = self.visit(ctx.idf), self.handle_field(ctx.return_parameters)
            if '$' in idf.name:
                raise SyntaxException('$ is not allowed in zkay function identifiers', ctx.idf, self.code)
        params, mods, body = self.handle_field(ctx.parameters), self.handle_field(ctx.modifiers), self.visit(ctx.body)
        return ast.ConstructorOrFunctionDefinition(idf, params, mods, ret_params, body)

    def visitFunctionDefinition(self, ctx:SolidityParser.FunctionDefinitionContext):
        return self.handle_fdef(ctx)

    def visitConstructorDefinition(self, ctx:SolidityParser.ConstructorDefinitionContext):
        return self.handle_fdef(ctx)

    def visitEnumDefinition(self, ctx:SolidityParser.EnumDefinitionContext):
        idf = self.visit(ctx.idf)
        if '$' in idf.name:
            raise SyntaxException('$ is not allowed in zkay enum identifiers', ctx.idf, self.code)
        values = [self.visit(v) for v in ctx.values]
        return ast.EnumDefinition(idf, values)

    def visitEnumValue(self, ctx:SolidityParser.EnumValueContext):
        idf = self.visit(ctx.idf)
        if '$' in idf.name:
            raise SyntaxException('$ is not allowed in zkay enum value identifiers', ctx.idf, self.code)
        return ast.EnumValue(idf)

    # Visit a parse tree produced by SolidityParser#NumberLiteralExpr.
    def visitNumberLiteralExpr(self, ctx: SolidityParser.NumberLiteralExprContext):
        v = int(ctx.getText().replace('_', ''), 0)
        return NumberLiteralExpr(v, ctx.getText().startswith(('0x', '0X')))

    # Visit a parse tree produced by SolidityParser#BooleanLiteralExpr.
    def visitBooleanLiteralExpr(self, ctx: SolidityParser.BooleanLiteralExprContext):
        b = ctx.getText() == 'true'
        return BooleanLiteralExpr(b)

    def visitStringLiteralExpr(self, ctx: SolidityParser.StringLiteralExprContext):
        s = ctx.getText()

        # Remove quotes
        if s.startswith('"'):
            s = s[1:-1].replace('\\"', '"')
        else:
            s = s[2:-2]

        raise SyntaxException('Use of unsupported string literal expression', ctx, self.code)
        # return StringLiteralExpr(s)

    def visitTupleExpr(self, ctx:SolidityParser.TupleExprContext):
        contents = ctx.expr.children[1:-1]
        elements = []
        for idx in range(0, len(contents), 2):
            elements.append(self.visit(contents[idx]))
        return ast.TupleExpr(elements)

    def visitModifier(self, ctx: SolidityParser.ModifierContext):
        return ctx.getText()

    def visitAnnotatedTypeName(self, ctx: SolidityParser.AnnotatedTypeNameContext):
        pa = None
        if ctx.privacy_annotation is not None:
            pa = self.visit(ctx.privacy_annotation)

            if not (isinstance(pa, ast.AllExpr) or isinstance(pa, ast.MeExpr) or isinstance(pa, IdentifierExpr)):
                raise SyntaxException('Privacy annotation can only be me | all | Identifier', ctx.privacy_annotation, self.code)

        return ast.AnnotatedTypeName(self.visit(ctx.type_name), pa)

    def visitElementaryTypeName(self, ctx: SolidityParser.ElementaryTypeNameContext):
        t = ctx.getText()
        if t == 'address':
            return ast.AddressTypeName()
        elif t == 'address payable':
            return ast.AddressPayableTypeName()
        elif t == 'bool':
            return ast.BoolTypeName()
        elif t.startswith('int'):
            return ast.IntTypeName(t)
        elif t.startswith('uint'):
            return ast.UintTypeName(t)
        elif t == 'var':
            raise SyntaxException(f'Use of unsupported var keyword', ctx, self.code)
        else:
            raise SyntaxException(f"Use of unsupported type '{t}'.", ctx, self.code)

    def visitIndexExpr(self, ctx: SolidityParser.IndexExprContext):
        arr = self.visit(ctx.arr)
        if not isinstance(arr, ast.LocationExpr):
            raise SyntaxException(f'Expression cannot be indexed', ctx.arr, self.code)
        index = self.visit(ctx.index)
        return IndexExpr(arr, index)

    def visitParenthesisExpr(self, ctx: SolidityParser.ParenthesisExprContext):
        f = BuiltinFunction('parenthesis').override(line=ctx.start.line, column=ctx.start.column)
        expr = self.visit(ctx.expr)
        return FunctionCallExpr(f, [expr])

    def visitSignExpr(self, ctx: SolidityParser.SignExprContext):
        f = BuiltinFunction('sign' + ctx.op.text).override(line=ctx.op.line, column=ctx.op.column)
        expr = self.visit(ctx.expr)
        return FunctionCallExpr(f, [expr])

    def visitNotExpr(self, ctx: SolidityParser.NotExprContext):
        f = BuiltinFunction('!').override(line=ctx.start.line, column=ctx.start.column)
        expr = self.visit(ctx.expr)
        return FunctionCallExpr(f, [expr])

    def visitBitwiseNotExpr(self, ctx: SolidityParser.BitwiseNotExprContext):
        f = BuiltinFunction('~').override(line=ctx.start.line, column=ctx.start.column)
        expr = self.visit(ctx.expr)
        return FunctionCallExpr(f, [expr])

    def _visitBinaryExpr(self, ctx):
        lhs = self.visit(ctx.lhs)
        rhs = self.visit(ctx.rhs)
        f = BuiltinFunction(ctx.op.text).override(line=ctx.op.line, column=ctx.op.column)
        return FunctionCallExpr(f, [lhs, rhs])

    def _visitBoolExpr(self, ctx):
        return self._visitBinaryExpr(ctx)

    def visitPowExpr(self, ctx: SolidityParser.PowExprContext):
        return self._visitBinaryExpr(ctx)

    def visitMultDivModExpr(self, ctx: SolidityParser.MultDivModExprContext):
        return self._visitBinaryExpr(ctx)

    def visitPlusMinusExpr(self, ctx: SolidityParser.PlusMinusExprContext):
        return self._visitBinaryExpr(ctx)

    def visitCompExpr(self, ctx: SolidityParser.CompExprContext):
        return self._visitBinaryExpr(ctx)

    def visitEqExpr(self, ctx: SolidityParser.EqExprContext):
        return self._visitBinaryExpr(ctx)

    def visitAndExpr(self, ctx: SolidityParser.AndExprContext):
        return self._visitBoolExpr(ctx)

    def visitOrExpr(self, ctx: SolidityParser.OrExprContext):
        return self._visitBoolExpr(ctx)

    def visitBitwiseOrExpr(self, ctx: SolidityParser.BitwiseOrExprContext):
        return self._visitBinaryExpr(ctx)

    def visitBitShiftExpr(self, ctx: SolidityParser.BitShiftExprContext):
        return self._visitBinaryExpr(ctx)

    def visitBitwiseAndExpr(self, ctx: SolidityParser.BitwiseAndExprContext):
        return self._visitBinaryExpr(ctx)

    def visitBitwiseXorExpr(self, ctx: SolidityParser.BitwiseXorExprContext):
        return self._visitBinaryExpr(ctx)

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
                    raise SyntaxException(f'Invalid number of arguments for reveal: {args}', ctx.args, self.code)
                return ReclassifyExpr(args[0], args[1])

        return FunctionCallExpr(func, args)

    def visitIfStatement(self, ctx: SolidityParser.IfStatementContext):
        cond = self.visit(ctx.condition)
        then_branch = self.visit(ctx.then_branch)
        if not isinstance(then_branch, ast.Block):
            then_branch = ast.Block([then_branch], was_single_statement=True)

        if ctx.else_branch is not None:
            else_branch = self.visit(ctx.else_branch)
            if not isinstance(else_branch, ast.Block):
                else_branch = ast.Block([else_branch], was_single_statement=True)
        else:
            else_branch = None

        return ast.IfStatement(cond, then_branch, else_branch)

    def visitWhileStatement(self, ctx: SolidityParser.WhileStatementContext):
        cond = self.visit(ctx.condition)
        body = self.visit(ctx.body)
        if not isinstance(body, ast.Block):
            body = ast.Block([body], was_single_statement=True)
        return ast.WhileStatement(cond, body)

    def visitDoWhileStatement(self, ctx: SolidityParser.DoWhileStatementContext):
        body = self.visit(ctx.body)
        cond = self.visit(ctx.condition)
        if not isinstance(body, ast.Block):
            body = ast.Block([body], was_single_statement=True)
        return ast.DoWhileStatement(body, cond)

    def visitForStatement(self, ctx: SolidityParser.ForStatementContext):
        init = None if ctx.init is None else self.visit(ctx.init)
        cond = self.visit(ctx.condition)
        update = None if ctx.update is None else self.visit(ctx.update)
        if isinstance(update, ast.Expression):
            update = ast.ExpressionStatement(update)
        body = self.visit(ctx.body)
        if not isinstance(body, ast.Block):
            body = ast.Block([body], was_single_statement=True)
        return ast.ForStatement(init, cond, update, body)

    def is_expr_stmt(self, ctx: SolidityParser.ExpressionContext) -> bool:
        if isinstance(ctx.parentCtx, SolidityParser.ExpressionStatementContext):
            return True
        elif isinstance(ctx.parentCtx, SolidityParser.ForStatementContext) and ctx == ctx.parentCtx.update:
            return True
        else:
            return False

    def visitAssignmentExpr(self, ctx: SolidityParser.AssignmentExprContext):
        if not self.is_expr_stmt(ctx):
            raise SyntaxException('Assignments are only allowed as statements', ctx, self.code)
        lhs = self.visit(ctx.lhs)
        rhs = self.visit(ctx.rhs)
        assert ctx.op.text[-1] == '='
        op = ctx.op.text[:-1] if ctx.op.text != '=' else ''
        if op:
            # If the assignment contains an additional operator -> replace lhs = rhs with lhs = lhs 'op' rhs
            rhs = FunctionCallExpr(BuiltinFunction(op).override(line=ctx.op.line, column=ctx.op.column), [self.visit(ctx.lhs), rhs])
            rhs.line = ctx.rhs.start.line
            rhs.column = ctx.rhs.start.column + 1
        return ast.AssignmentStatement(lhs, rhs, op)

    def _handle_crement_expr(self, ctx, kind: str):
        if not self.is_expr_stmt(ctx):
            raise SyntaxException(f'{kind}-crement expressions are only allowed as statements', ctx, self.code)
        op = '+' if ctx.op.text == '++' else '-'

        one = NumberLiteralExpr(1)
        one.line = ctx.op.line
        one.column = ctx.op.column + 1

        fct = FunctionCallExpr(BuiltinFunction(op).override(line=ctx.op.line, column=ctx.op.column), [self.visit(ctx.expr), one])
        fct.line = ctx.op.line
        fct.column = ctx.op.column + 1

        return ast.AssignmentStatement(self.visit(ctx.expr), fct, f'{kind}{ctx.op.text}')

    def visitPreCrementExpr(self, ctx: SolidityParser.PreCrementExprContext):
        return self._handle_crement_expr(ctx, 'pre')

    def visitPostCrementExpr(self, ctx: SolidityParser.PostCrementExprContext):
        return self._handle_crement_expr(ctx, 'post')

    def visitExpressionStatement(self, ctx: SolidityParser.ExpressionStatementContext):
        e = self.visit(ctx.expr)
        if isinstance(e, ast.Statement):
            return e
        else:
            # handle require
            if isinstance(e, FunctionCallExpr):
                f = e.func
                if isinstance(f, IdentifierExpr):
                    if f.idf.name == 'require':
                        if len(e.args) != 1:
                            raise SyntaxException(f'Invalid number of arguments for require: {e.args}', ctx.expr, self.code)
                        return ast.RequireStatement(e.args[0])

            assert isinstance(e, ast.Expression)
            return ExpressionStatement(e)
