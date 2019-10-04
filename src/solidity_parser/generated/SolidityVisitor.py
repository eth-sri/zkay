# Generated from /home/nibau/msc-thesis/zkay/src/solidity_parser/Solidity.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .SolidityParser import SolidityParser
else:
    from SolidityParser import SolidityParser

# This class defines a complete generic visitor for a parse tree produced by SolidityParser.

class SolidityVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by SolidityParser#sourceUnit.
    def visitSourceUnit(self, ctx:SolidityParser.SourceUnitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#pragmaDirective.
    def visitPragmaDirective(self, ctx:SolidityParser.PragmaDirectiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#pragmaName.
    def visitPragmaName(self, ctx:SolidityParser.PragmaNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#pragmaValue.
    def visitPragmaValue(self, ctx:SolidityParser.PragmaValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#version.
    def visitVersion(self, ctx:SolidityParser.VersionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#versionOperator.
    def visitVersionOperator(self, ctx:SolidityParser.VersionOperatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#versionConstraint.
    def visitVersionConstraint(self, ctx:SolidityParser.VersionConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#contractDefinition.
    def visitContractDefinition(self, ctx:SolidityParser.ContractDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#contractPart.
    def visitContractPart(self, ctx:SolidityParser.ContractPartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#stateVariableDeclaration.
    def visitStateVariableDeclaration(self, ctx:SolidityParser.StateVariableDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#constructorDefinition.
    def visitConstructorDefinition(self, ctx:SolidityParser.ConstructorDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#functionDefinition.
    def visitFunctionDefinition(self, ctx:SolidityParser.FunctionDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#returnParameters.
    def visitReturnParameters(self, ctx:SolidityParser.ReturnParametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#modifierList.
    def visitModifierList(self, ctx:SolidityParser.ModifierListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#modifier.
    def visitModifier(self, ctx:SolidityParser.ModifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#parameterList.
    def visitParameterList(self, ctx:SolidityParser.ParameterListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#parameter.
    def visitParameter(self, ctx:SolidityParser.ParameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#variableDeclaration.
    def visitVariableDeclaration(self, ctx:SolidityParser.VariableDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#typeName.
    def visitTypeName(self, ctx:SolidityParser.TypeNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#elementaryTypeName.
    def visitElementaryTypeName(self, ctx:SolidityParser.ElementaryTypeNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#mapping.
    def visitMapping(self, ctx:SolidityParser.MappingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#payableAddress.
    def visitPayableAddress(self, ctx:SolidityParser.PayableAddressContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#stateMutability.
    def visitStateMutability(self, ctx:SolidityParser.StateMutabilityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#block.
    def visitBlock(self, ctx:SolidityParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#statement.
    def visitStatement(self, ctx:SolidityParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#expressionStatement.
    def visitExpressionStatement(self, ctx:SolidityParser.ExpressionStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#ifStatement.
    def visitIfStatement(self, ctx:SolidityParser.IfStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#whileStatement.
    def visitWhileStatement(self, ctx:SolidityParser.WhileStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#simpleStatement.
    def visitSimpleStatement(self, ctx:SolidityParser.SimpleStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#returnStatement.
    def visitReturnStatement(self, ctx:SolidityParser.ReturnStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#variableDeclarationStatement.
    def visitVariableDeclarationStatement(self, ctx:SolidityParser.VariableDeclarationStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#AndExpr.
    def visitAndExpr(self, ctx:SolidityParser.AndExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#MultDivModExpr.
    def visitMultDivModExpr(self, ctx:SolidityParser.MultDivModExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#ParenthesisExpr.
    def visitParenthesisExpr(self, ctx:SolidityParser.ParenthesisExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#AllExpr.
    def visitAllExpr(self, ctx:SolidityParser.AllExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#IteExpr.
    def visitIteExpr(self, ctx:SolidityParser.IteExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#PowExpr.
    def visitPowExpr(self, ctx:SolidityParser.PowExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#PlusMinusExpr.
    def visitPlusMinusExpr(self, ctx:SolidityParser.PlusMinusExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#CompExpr.
    def visitCompExpr(self, ctx:SolidityParser.CompExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#AssignmentExpr.
    def visitAssignmentExpr(self, ctx:SolidityParser.AssignmentExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#OrExpr.
    def visitOrExpr(self, ctx:SolidityParser.OrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#IndexExpr.
    def visitIndexExpr(self, ctx:SolidityParser.IndexExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#SignExpr.
    def visitSignExpr(self, ctx:SolidityParser.SignExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#NumberLiteralExpr.
    def visitNumberLiteralExpr(self, ctx:SolidityParser.NumberLiteralExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#FunctionCallExpr.
    def visitFunctionCallExpr(self, ctx:SolidityParser.FunctionCallExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#MemberAccess.
    def visitMemberAccess(self, ctx:SolidityParser.MemberAccessContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#IdentifierExpr.
    def visitIdentifierExpr(self, ctx:SolidityParser.IdentifierExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#EqExpr.
    def visitEqExpr(self, ctx:SolidityParser.EqExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#BooleanLiteralExpr.
    def visitBooleanLiteralExpr(self, ctx:SolidityParser.BooleanLiteralExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#MeExpr.
    def visitMeExpr(self, ctx:SolidityParser.MeExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#NotExpr.
    def visitNotExpr(self, ctx:SolidityParser.NotExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#functionCallArguments.
    def visitFunctionCallArguments(self, ctx:SolidityParser.FunctionCallArgumentsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#elementaryTypeNameExpression.
    def visitElementaryTypeNameExpression(self, ctx:SolidityParser.ElementaryTypeNameExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#numberLiteral.
    def visitNumberLiteral(self, ctx:SolidityParser.NumberLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#annotatedTypeName.
    def visitAnnotatedTypeName(self, ctx:SolidityParser.AnnotatedTypeNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SolidityParser#identifier.
    def visitIdentifier(self, ctx:SolidityParser.IdentifierContext):
        return self.visitChildren(ctx)



del SolidityParser