# Generated from Solidity.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .SolidityParser import SolidityParser
else:
    from SolidityParser import SolidityParser

# This class defines a complete listener for a parse tree produced by SolidityParser.
class SolidityListener(ParseTreeListener):

    # Enter a parse tree produced by SolidityParser#sourceUnit.
    def enterSourceUnit(self, ctx:SolidityParser.SourceUnitContext):
        pass

    # Exit a parse tree produced by SolidityParser#sourceUnit.
    def exitSourceUnit(self, ctx:SolidityParser.SourceUnitContext):
        pass


    # Enter a parse tree produced by SolidityParser#pragmaDirective.
    def enterPragmaDirective(self, ctx:SolidityParser.PragmaDirectiveContext):
        pass

    # Exit a parse tree produced by SolidityParser#pragmaDirective.
    def exitPragmaDirective(self, ctx:SolidityParser.PragmaDirectiveContext):
        pass


    # Enter a parse tree produced by SolidityParser#pragmaName.
    def enterPragmaName(self, ctx:SolidityParser.PragmaNameContext):
        pass

    # Exit a parse tree produced by SolidityParser#pragmaName.
    def exitPragmaName(self, ctx:SolidityParser.PragmaNameContext):
        pass


    # Enter a parse tree produced by SolidityParser#pragmaValue.
    def enterPragmaValue(self, ctx:SolidityParser.PragmaValueContext):
        pass

    # Exit a parse tree produced by SolidityParser#pragmaValue.
    def exitPragmaValue(self, ctx:SolidityParser.PragmaValueContext):
        pass


    # Enter a parse tree produced by SolidityParser#version.
    def enterVersion(self, ctx:SolidityParser.VersionContext):
        pass

    # Exit a parse tree produced by SolidityParser#version.
    def exitVersion(self, ctx:SolidityParser.VersionContext):
        pass


    # Enter a parse tree produced by SolidityParser#versionOperator.
    def enterVersionOperator(self, ctx:SolidityParser.VersionOperatorContext):
        pass

    # Exit a parse tree produced by SolidityParser#versionOperator.
    def exitVersionOperator(self, ctx:SolidityParser.VersionOperatorContext):
        pass


    # Enter a parse tree produced by SolidityParser#versionConstraint.
    def enterVersionConstraint(self, ctx:SolidityParser.VersionConstraintContext):
        pass

    # Exit a parse tree produced by SolidityParser#versionConstraint.
    def exitVersionConstraint(self, ctx:SolidityParser.VersionConstraintContext):
        pass


    # Enter a parse tree produced by SolidityParser#contractDefinition.
    def enterContractDefinition(self, ctx:SolidityParser.ContractDefinitionContext):
        pass

    # Exit a parse tree produced by SolidityParser#contractDefinition.
    def exitContractDefinition(self, ctx:SolidityParser.ContractDefinitionContext):
        pass


    # Enter a parse tree produced by SolidityParser#contractPart.
    def enterContractPart(self, ctx:SolidityParser.ContractPartContext):
        pass

    # Exit a parse tree produced by SolidityParser#contractPart.
    def exitContractPart(self, ctx:SolidityParser.ContractPartContext):
        pass


    # Enter a parse tree produced by SolidityParser#stateVariableDeclaration.
    def enterStateVariableDeclaration(self, ctx:SolidityParser.StateVariableDeclarationContext):
        pass

    # Exit a parse tree produced by SolidityParser#stateVariableDeclaration.
    def exitStateVariableDeclaration(self, ctx:SolidityParser.StateVariableDeclarationContext):
        pass


    # Enter a parse tree produced by SolidityParser#constructorDefinition.
    def enterConstructorDefinition(self, ctx:SolidityParser.ConstructorDefinitionContext):
        pass

    # Exit a parse tree produced by SolidityParser#constructorDefinition.
    def exitConstructorDefinition(self, ctx:SolidityParser.ConstructorDefinitionContext):
        pass


    # Enter a parse tree produced by SolidityParser#functionDefinition.
    def enterFunctionDefinition(self, ctx:SolidityParser.FunctionDefinitionContext):
        pass

    # Exit a parse tree produced by SolidityParser#functionDefinition.
    def exitFunctionDefinition(self, ctx:SolidityParser.FunctionDefinitionContext):
        pass


    # Enter a parse tree produced by SolidityParser#returnParameters.
    def enterReturnParameters(self, ctx:SolidityParser.ReturnParametersContext):
        pass

    # Exit a parse tree produced by SolidityParser#returnParameters.
    def exitReturnParameters(self, ctx:SolidityParser.ReturnParametersContext):
        pass


    # Enter a parse tree produced by SolidityParser#modifierList.
    def enterModifierList(self, ctx:SolidityParser.ModifierListContext):
        pass

    # Exit a parse tree produced by SolidityParser#modifierList.
    def exitModifierList(self, ctx:SolidityParser.ModifierListContext):
        pass


    # Enter a parse tree produced by SolidityParser#modifier.
    def enterModifier(self, ctx:SolidityParser.ModifierContext):
        pass

    # Exit a parse tree produced by SolidityParser#modifier.
    def exitModifier(self, ctx:SolidityParser.ModifierContext):
        pass


    # Enter a parse tree produced by SolidityParser#parameterList.
    def enterParameterList(self, ctx:SolidityParser.ParameterListContext):
        pass

    # Exit a parse tree produced by SolidityParser#parameterList.
    def exitParameterList(self, ctx:SolidityParser.ParameterListContext):
        pass


    # Enter a parse tree produced by SolidityParser#parameter.
    def enterParameter(self, ctx:SolidityParser.ParameterContext):
        pass

    # Exit a parse tree produced by SolidityParser#parameter.
    def exitParameter(self, ctx:SolidityParser.ParameterContext):
        pass


    # Enter a parse tree produced by SolidityParser#variableDeclaration.
    def enterVariableDeclaration(self, ctx:SolidityParser.VariableDeclarationContext):
        pass

    # Exit a parse tree produced by SolidityParser#variableDeclaration.
    def exitVariableDeclaration(self, ctx:SolidityParser.VariableDeclarationContext):
        pass


    # Enter a parse tree produced by SolidityParser#typeName.
    def enterTypeName(self, ctx:SolidityParser.TypeNameContext):
        pass

    # Exit a parse tree produced by SolidityParser#typeName.
    def exitTypeName(self, ctx:SolidityParser.TypeNameContext):
        pass


    # Enter a parse tree produced by SolidityParser#elementaryTypeName.
    def enterElementaryTypeName(self, ctx:SolidityParser.ElementaryTypeNameContext):
        pass

    # Exit a parse tree produced by SolidityParser#elementaryTypeName.
    def exitElementaryTypeName(self, ctx:SolidityParser.ElementaryTypeNameContext):
        pass


    # Enter a parse tree produced by SolidityParser#mapping.
    def enterMapping(self, ctx:SolidityParser.MappingContext):
        pass

    # Exit a parse tree produced by SolidityParser#mapping.
    def exitMapping(self, ctx:SolidityParser.MappingContext):
        pass


    # Enter a parse tree produced by SolidityParser#stateMutability.
    def enterStateMutability(self, ctx:SolidityParser.StateMutabilityContext):
        pass

    # Exit a parse tree produced by SolidityParser#stateMutability.
    def exitStateMutability(self, ctx:SolidityParser.StateMutabilityContext):
        pass


    # Enter a parse tree produced by SolidityParser#block.
    def enterBlock(self, ctx:SolidityParser.BlockContext):
        pass

    # Exit a parse tree produced by SolidityParser#block.
    def exitBlock(self, ctx:SolidityParser.BlockContext):
        pass


    # Enter a parse tree produced by SolidityParser#statement.
    def enterStatement(self, ctx:SolidityParser.StatementContext):
        pass

    # Exit a parse tree produced by SolidityParser#statement.
    def exitStatement(self, ctx:SolidityParser.StatementContext):
        pass


    # Enter a parse tree produced by SolidityParser#expressionStatement.
    def enterExpressionStatement(self, ctx:SolidityParser.ExpressionStatementContext):
        pass

    # Exit a parse tree produced by SolidityParser#expressionStatement.
    def exitExpressionStatement(self, ctx:SolidityParser.ExpressionStatementContext):
        pass


    # Enter a parse tree produced by SolidityParser#ifStatement.
    def enterIfStatement(self, ctx:SolidityParser.IfStatementContext):
        pass

    # Exit a parse tree produced by SolidityParser#ifStatement.
    def exitIfStatement(self, ctx:SolidityParser.IfStatementContext):
        pass


    # Enter a parse tree produced by SolidityParser#whileStatement.
    def enterWhileStatement(self, ctx:SolidityParser.WhileStatementContext):
        pass

    # Exit a parse tree produced by SolidityParser#whileStatement.
    def exitWhileStatement(self, ctx:SolidityParser.WhileStatementContext):
        pass


    # Enter a parse tree produced by SolidityParser#simpleStatement.
    def enterSimpleStatement(self, ctx:SolidityParser.SimpleStatementContext):
        pass

    # Exit a parse tree produced by SolidityParser#simpleStatement.
    def exitSimpleStatement(self, ctx:SolidityParser.SimpleStatementContext):
        pass


    # Enter a parse tree produced by SolidityParser#returnStatement.
    def enterReturnStatement(self, ctx:SolidityParser.ReturnStatementContext):
        pass

    # Exit a parse tree produced by SolidityParser#returnStatement.
    def exitReturnStatement(self, ctx:SolidityParser.ReturnStatementContext):
        pass


    # Enter a parse tree produced by SolidityParser#variableDeclarationStatement.
    def enterVariableDeclarationStatement(self, ctx:SolidityParser.VariableDeclarationStatementContext):
        pass

    # Exit a parse tree produced by SolidityParser#variableDeclarationStatement.
    def exitVariableDeclarationStatement(self, ctx:SolidityParser.VariableDeclarationStatementContext):
        pass


    # Enter a parse tree produced by SolidityParser#AndExpr.
    def enterAndExpr(self, ctx:SolidityParser.AndExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#AndExpr.
    def exitAndExpr(self, ctx:SolidityParser.AndExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#MultDivModExpr.
    def enterMultDivModExpr(self, ctx:SolidityParser.MultDivModExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#MultDivModExpr.
    def exitMultDivModExpr(self, ctx:SolidityParser.MultDivModExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#ParenthesisExpr.
    def enterParenthesisExpr(self, ctx:SolidityParser.ParenthesisExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#ParenthesisExpr.
    def exitParenthesisExpr(self, ctx:SolidityParser.ParenthesisExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#AllExpr.
    def enterAllExpr(self, ctx:SolidityParser.AllExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#AllExpr.
    def exitAllExpr(self, ctx:SolidityParser.AllExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#IteExpr.
    def enterIteExpr(self, ctx:SolidityParser.IteExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#IteExpr.
    def exitIteExpr(self, ctx:SolidityParser.IteExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#PowExpr.
    def enterPowExpr(self, ctx:SolidityParser.PowExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#PowExpr.
    def exitPowExpr(self, ctx:SolidityParser.PowExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#PlusMinusExpr.
    def enterPlusMinusExpr(self, ctx:SolidityParser.PlusMinusExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#PlusMinusExpr.
    def exitPlusMinusExpr(self, ctx:SolidityParser.PlusMinusExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#CompExpr.
    def enterCompExpr(self, ctx:SolidityParser.CompExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#CompExpr.
    def exitCompExpr(self, ctx:SolidityParser.CompExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#AssignmentExpr.
    def enterAssignmentExpr(self, ctx:SolidityParser.AssignmentExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#AssignmentExpr.
    def exitAssignmentExpr(self, ctx:SolidityParser.AssignmentExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#OrExpr.
    def enterOrExpr(self, ctx:SolidityParser.OrExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#OrExpr.
    def exitOrExpr(self, ctx:SolidityParser.OrExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#IndexExpr.
    def enterIndexExpr(self, ctx:SolidityParser.IndexExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#IndexExpr.
    def exitIndexExpr(self, ctx:SolidityParser.IndexExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#SignExpr.
    def enterSignExpr(self, ctx:SolidityParser.SignExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#SignExpr.
    def exitSignExpr(self, ctx:SolidityParser.SignExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#NumberLiteralExpr.
    def enterNumberLiteralExpr(self, ctx:SolidityParser.NumberLiteralExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#NumberLiteralExpr.
    def exitNumberLiteralExpr(self, ctx:SolidityParser.NumberLiteralExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#FunctionCallExpr.
    def enterFunctionCallExpr(self, ctx:SolidityParser.FunctionCallExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#FunctionCallExpr.
    def exitFunctionCallExpr(self, ctx:SolidityParser.FunctionCallExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#IdentifierExpr.
    def enterIdentifierExpr(self, ctx:SolidityParser.IdentifierExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#IdentifierExpr.
    def exitIdentifierExpr(self, ctx:SolidityParser.IdentifierExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#EqExpr.
    def enterEqExpr(self, ctx:SolidityParser.EqExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#EqExpr.
    def exitEqExpr(self, ctx:SolidityParser.EqExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#BooleanLiteralExpr.
    def enterBooleanLiteralExpr(self, ctx:SolidityParser.BooleanLiteralExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#BooleanLiteralExpr.
    def exitBooleanLiteralExpr(self, ctx:SolidityParser.BooleanLiteralExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#MeExpr.
    def enterMeExpr(self, ctx:SolidityParser.MeExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#MeExpr.
    def exitMeExpr(self, ctx:SolidityParser.MeExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#NotExpr.
    def enterNotExpr(self, ctx:SolidityParser.NotExprContext):
        pass

    # Exit a parse tree produced by SolidityParser#NotExpr.
    def exitNotExpr(self, ctx:SolidityParser.NotExprContext):
        pass


    # Enter a parse tree produced by SolidityParser#functionCallArguments.
    def enterFunctionCallArguments(self, ctx:SolidityParser.FunctionCallArgumentsContext):
        pass

    # Exit a parse tree produced by SolidityParser#functionCallArguments.
    def exitFunctionCallArguments(self, ctx:SolidityParser.FunctionCallArgumentsContext):
        pass


    # Enter a parse tree produced by SolidityParser#elementaryTypeNameExpression.
    def enterElementaryTypeNameExpression(self, ctx:SolidityParser.ElementaryTypeNameExpressionContext):
        pass

    # Exit a parse tree produced by SolidityParser#elementaryTypeNameExpression.
    def exitElementaryTypeNameExpression(self, ctx:SolidityParser.ElementaryTypeNameExpressionContext):
        pass


    # Enter a parse tree produced by SolidityParser#numberLiteral.
    def enterNumberLiteral(self, ctx:SolidityParser.NumberLiteralContext):
        pass

    # Exit a parse tree produced by SolidityParser#numberLiteral.
    def exitNumberLiteral(self, ctx:SolidityParser.NumberLiteralContext):
        pass


    # Enter a parse tree produced by SolidityParser#annotatedTypeName.
    def enterAnnotatedTypeName(self, ctx:SolidityParser.AnnotatedTypeNameContext):
        pass

    # Exit a parse tree produced by SolidityParser#annotatedTypeName.
    def exitAnnotatedTypeName(self, ctx:SolidityParser.AnnotatedTypeNameContext):
        pass


    # Enter a parse tree produced by SolidityParser#identifier.
    def enterIdentifier(self, ctx:SolidityParser.IdentifierContext):
        pass

    # Exit a parse tree produced by SolidityParser#identifier.
    def exitIdentifier(self, ctx:SolidityParser.IdentifierContext):
        pass


