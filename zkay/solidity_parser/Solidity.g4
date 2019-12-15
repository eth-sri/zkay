// Copyright 2016-2019 Federico Bond <federicobond@gmail.com>
// Licensed under the MIT license. See LICENSE file in the project root for details.

// Original source: https://github.com/solidityj/solidity-antlr4/blob/master/Solidity.g4
// changes are marked with REMOVED or CHANGED
//
// - removed language features:
//   - imports (importDeclaration, importDirective)
//      -> https://solidity.readthedocs.io/en/v0.4.24/layout-of-source-files.html#importing-other-source-files
//   - interfaces, libraries
//   - inheritance (inheritanceSpecifier)
//      -> https://solidity.readthedocs.io/en/v0.4.24/contracts.html#inheritance
//   - using for (usingForDeclaration)
//      -> https://solidity.readthedocs.io/en/v0.4.24/contracts.html#using-for
//   - function modifiers / modifier definitions (modifierDefinition, modifierInvocation)
//      -> https://solidity.readthedocs.io/en/v0.4.24/common-patterns.html#restricting-access
//   - events (eventDefinition,eventParameterList,eventParameter)
//      -> https://solidity.readthedocs.io/en/v0.4.21/contracts.html#events
//   - enum (enumValue, enumDefinition)
//   - struct (structDefinition)
// - moved stateVariableAccessModifiers to separate rule
// - user defined type names (userDefinedTypeName)
// - function type name (functionTypeName, functionTypeParameterList, functionTypeParameter), needed for higher-order functions



grammar Solidity;

// : importDirective
sourceUnit
  : pragma_directive=pragmaDirective (contracts+=contractDefinition)* EOF ;

// https://solidity.readthedocs.io/en/v0.4.24/layout-of-source-files.html#version-pragma
pragmaDirective
  : 'pragma' pragmaName pragmaValue ';' ;

pragmaName
  : identifier ;

pragmaValue
  : version | expression ;

version
  : versionConstraint versionConstraint? ;

versionOperator
  : '^' | '~' | '>=' | '>' | '<' | '<=' | '=' ;

versionConstraint
  : versionOperator? VersionLiteral ;

// REMOVED: interface, library, inheritance
contractDefinition
  : ( 'contract' ) identifier
    '{' parts+=contractPart* '}' ;

// REMOVED: structDefinition, usingForDeclaration, modifierDefinition, eventDefinition, enumDefinition
contractPart
  : stateVariableDeclaration
  | constructorDefinition
  | functionDefinition ;

// CHANGED: typeName -> annotatedTypeName
// REMOVED (only allow default):
// - PublicKeyword
// - InternalKeyword
// - PrivateKeyword
//
// state variable modifiers:
// - public: all can access (default for functions)
// - internal: only this contract and contracts deriving from it can access (default for state variables)
// - private: can be accessed only from this contract
// - constant: constant at compile-time: https://solidity.readthedocs.io/en/v0.4.24/contracts.html#constant-state-variables
stateVariableDeclaration
  : ( keywords+=FinalKeyword )* annotated_type=annotatedTypeName
    ( keywords+=ConstantKeyword )*
    idf=identifier ('=' expr=expression)? ';' ;

constructorDefinition
  : 'constructor' parameters=parameterList modifiers=modifierList body=block ;

// CHANGED:
// - identifier is now required
// - empty body is now disallowed
// - inlined returnParameters
functionDefinition
  : 'function'
    idf=identifier
    parameters=parameterList
    modifiers=modifierList
    return_parameters=returnParameters?
    body=block ;

returnParameters
: 'returns' return_parameters=parameterList ;

// REMOVED:
// - modifierInvocation
// - ExternalKeyword
// - PublicKeyword
// - InternalKeyword
// - PrivateKeyword
//
// function modifiers
// - state mutability: see below
// - external: part of the contract interface. Can be called from other contracts and via transactions
// - public: part of the contract interface. Can be called internally or via messages
// - internal: can only be accessed internally (from the current contract or contracts deriving from it)
// - private: only visible for the contract they are defined in
modifierList
  : ( modifiers+=modifier )* ;

modifier
  : stateMutability | PublicKeyword | InternalKeyword | PrivateKeyword ;

parameterList
  : '(' ( params+=parameter (',' params+=parameter)* )? ')' ;

// identifier is optional because parameters can be used to specify the return value
// CHANGED:
// - typeName -> annotatedTypeName
parameter
  : (keywords+=FinalKeyword)? annotated_type=annotatedTypeName idf=identifier? ;

variableDeclaration
  : (keywords+=FinalKeyword)? annotated_type=annotatedTypeName idf=identifier ;

// REMOVED:
// - 'address' 'payable'
// - typeName '[' expression? ']' (arrays)
// - userDefinedTypeName
//
// special types:
// - address payable: Same as address, but with the additional members transfer and send
// - arrays: allows fixed size (T[k]) and dynamic size (T[])
typeName
  : elementaryTypeName
  | mapping ;

// REMOVED:
// - string
// - var: type deduction
// - Int
// - byte
// - Byte
// - Fixed
// - Ufixed
elementaryTypeName
  : name=('address' | 'address payable' | 'bool' | Uint)  ;

mapping
  : 'mapping' '(' key_type=elementaryTypeName ( '!' key_label=identifier )? '=>' value_type=annotatedTypeName ')' ;

// REMOVED (only allow default)
// storage location
// - memory: Not persisting (default for function parameters)
// - storage: Where the state variables are held. (default for local variables, forced for state variables)
// - calldata: non-modifiable, non-persistent area for function arguments (forced for function parameters of external
//   functions)

// REMOVED
// - PureKeyword
// - ViewKeyword
//
// state mutability
// pure: function does not read or modify state
//       -> https://solidity.readthedocs.io/en/v0.4.24/contracts.html#pure-functions
// constant: deprecated for functions, alias to view
// view: function does not modify the state
//       -> https://solidity.readthedocs.io/en/v0.4.24/contracts.html#view-functions
// payable: function may receive Ether
stateMutability
  : PayableKeyword | PureKeyword | ViewKeyword ;

block
  : '{' statements+=statement* '}' ;

// REMOVED:
// - inlineAssemblyStatement
// - doWhile
// - forLoop
// - continueStatement
// - breakStatement
// - throwStatement
// - emitStatement
statement
  : ifStatement
  | whileStatement
  | forStatement
  | block
  | continueStatement
  | breakStatement
  | returnStatement
  | simpleStatement ;

expressionStatement
  : expr=expression ';' ;

ifStatement
  : 'if' '(' condition=expression ')' then_branch=statement ( 'else' else_branch=statement )? ;

whileStatement
  : 'while' '(' condition=expression ')' body=statement ;

simpleStatement
  : ( variableDeclarationStatement | expressionStatement ) ;

forStatement
  : 'for' '(' ( init=simpleStatement | ';' ) condition=expression? ';' update=expression? ')' body=statement ;

continueStatement
  : 'continue' ';' ;

breakStatement
  : 'break' ';' ;


returnStatement
  : 'return' expr=expression? ';' ;

// REMOVED:
// - 'var' identifierList
// - '(' variableDeclarationList ')'
variableDeclarationStatement
  : variable_declaration=variableDeclaration ( '=' expr=expression )? ';';

// REMOVED: identifierList

// REMOVED: Int

// REMOVED: many variants
Uint
  : 'uint' ;

// CHANGED: INLINED: primaryExpression
// REMOVED from primaryExpression:
// - StringLiteral
// - HexLiteral
// - tupleExpression
// - elementaryTypeNameExpression ('[' ']')? (for type casts)
// CHANGED from primaryExpression:
// - identifier ('[' ']')? -> identifier
// - added me and all
// REMOVED:
// - expression ('++' | '--')
// - 'new' typeName
// - expression '.' identifier
// - ('after' | 'delete') expression
// - ~ (bitwise not)
// - <<, >> (bit shift)
// - &, ^, | (bitwise operations)
// - ('++' | '--') expression
// - '|=' | '^=' | '&=' | '<<=' | '>>=' | '+=' | '-=' | '*=' | '/=' | '%='
expression
  : MeKeyword # MeExpr
  | AllKeyword # AllExpr
  | arr=expression '[' index=expression ']' # IndexExpr
  | func=expression '(' args=functionCallArguments ')' # FunctionCallExpr
  | expr=expression '.' member=identifier # MemberAccessExpr // NB: add member access again
  | '(' expr=expression ')' # ParenthesisExpr
  | op=('+' | '-') expr=expression # SignExpr
  | '!' expr=expression # NotExpr
  | lhs=expression op='**' rhs=expression # PowExpr
  | lhs=expression op=('*' | '/' | '%') rhs=expression # MultDivModExpr
  | lhs=expression op=('+' | '-') rhs=expression # PlusMinusExpr
  | lhs=expression op=('<' | '>' | '<=' | '>=') rhs=expression # CompExpr
  | lhs=expression op=('==' | '!=') rhs=expression # EqExpr
  | lhs=expression op='&&' rhs=expression # AndExpr
  | lhs=expression op='||' rhs=expression # OrExpr
  | cond=expression '?' then_expr=expression ':' else_expr=expression # IteExpr
  | lhs=expression ('=' ) rhs=expression # AssignmentExpr
  | BooleanLiteral # BooleanLiteralExpr
  | numberLiteral # NumberLiteralExpr
  | StringLiteral # StringLiteralExpr
  | expr=tupleExpression # TupleExpr
  | idf=identifier # IdentifierExpr ;

// CHANGED:
// - inlined expressionList
// REMOVED
// - '{' nameValueList? '}'
functionCallArguments
  : (exprs+=expression (',' exprs+=expression)*)? ;

// REMOVED
// - functionCall (already covered by expressions)

tupleExpression
  : '(' ( expression? ( ',' expression? )* ) ')' ;

elementaryTypeNameExpression
  : elementaryTypeName ;

// REMOVED:
// - NumberUnit
// - HexNumber
numberLiteral
  : DecimalNumber ;

// CHANGED: ADDED RULES FOR PRIVACY ANNOTATIONS

MeKeyword : 'me' ;
AllKeyword : 'all' ;

annotatedTypeName
  : type_name=typeName ('@' privacy_annotation=expression)? ;

// REMOVED:
// - 'from'
// - 'calldata'
identifier
  : (name=Identifier) ;

VersionLiteral
  : [0-9]+ '.' [0-9]+ '.' [0-9]+ ;

BooleanLiteral
  : 'true' | 'false' ;

DecimalNumber
  : ([0-9]+ | ([0-9]* '.' [0-9]+) ) ( [eE] [0-9]+ )? ;

// REMOVED:
// - final
ReservedKeyword
  : 'abstract'
  | 'after'
  | 'case'
  | 'catch'
  | 'default'
  | 'in'
  | 'inline'
  | 'let'
  | 'match'
  | 'null'
  | 'of'
  | 'relocatable'
  | 'static'
  | 'switch'
  | 'try'
  | 'type'
  | 'typeof' ;

AnonymousKeyword : 'anonymous' ;
BreakKeyword : 'break' ;
ConstantKeyword : 'constant' ;
ContinueKeyword : 'continue' ;
ExternalKeyword : 'external' ;
IndexedKeyword : 'indexed' ;
InternalKeyword : 'internal' ;
PayableKeyword : 'payable' ;
PrivateKeyword : 'private' ;
PublicKeyword : 'public' ;
PureKeyword : 'pure' ;
ViewKeyword : 'view' ;

// ADDED
FinalKeyword : 'final' ;

Identifier
  : IdentifierStart IdentifierPart* ;

fragment
IdentifierStart
  : [a-zA-Z$_] ;

fragment
IdentifierPart
  : [a-zA-Z0-9$_] ;

StringLiteral
  : '"' DoubleQuotedStringCharacter* '"'
  | '\'' SingleQuotedStringCharacter* '\'' ;

fragment
DoubleQuotedStringCharacter
  : ~["\r\n\\] | ('\\' .) ;
fragment
SingleQuotedStringCharacter
  : ~['\r\n\\] | ('\\' .) ;

// CHANGED: switched WS to HIDDEN channel (allows preserving whitespaces)
WS
  : [ \t\r\n\u000C]+ -> channel(HIDDEN) ;

COMMENT
  : '/*' .*? '*/' -> channel(HIDDEN) ;

LINE_COMMENT
  : '//' ~[\r\n]* -> channel(HIDDEN) ;
