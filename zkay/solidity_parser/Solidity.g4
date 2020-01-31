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
  : ( 'contract' ) idf=identifier
    '{' parts+=contractPart* '}' ;

// REMOVED: structDefinition, usingForDeclaration, modifierDefinition, eventDefinition
contractPart
  : stateVariableDeclaration
  | constructorDefinition
  | functionDefinition
  | enumDefinition;

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

enumValue
  : idf=identifier ;

enumDefinition
  : 'enum' idf=identifier '{' values+=enumValue? (',' values+=enumValue)* '}' ;

variableDeclaration
  : (keywords+=FinalKeyword)? annotated_type=annotatedTypeName idf=identifier ;

// REMOVED:
// - typeName '[' expression? ']' (arrays)
//
// special types:
// - address payable: Same as address, but with the additional members transfer and send
// - arrays: allows fixed size (T[k]) and dynamic size (T[])
typeName
  : elementaryTypeName
  | userDefinedTypeName
  | mapping ;

userDefinedTypeName
  : names+=identifier ( '.' names+=identifier )* ;

mapping
  : 'mapping' '(' key_type=elementaryTypeName ( '!' key_label=identifier )? '=>' value_type=annotatedTypeName ')' ;

// REMOVED (only allow default)
// storage location
// - memory: Not persisting (default for function parameters)
// - storage: Where the state variables are held. (default for local variables, forced for state variables)
// - calldata: non-modifiable, non-persistent area for function arguments (forced for function parameters of external
//   functions)

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
// - throwStatement
// - emitStatement
statement
  : ifStatement
  | whileStatement
  | forStatement
  | block
  | doWhileStatement
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

doWhileStatement
  : 'do' body=statement 'while' '(' condition=expression ')' ';' ;

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

// REMOVED:
// - string
// - var: type deduction
// - byte
// - Byte
// - Fixed
// - Ufixed
elementaryTypeName
  : name=('address' | 'address payable' | 'bool' | Int | Uint | Byte )  ;

Uint
  : 'uint' | 'uint8' | 'uint16' | 'uint24' | 'uint32' | 'uint40' | 'uint48' | 'uint56' | 'uint64' | 'uint72' | 'uint80' | 'uint88' | 'uint96' | 'uint104' | 'uint112' | 'uint120' | 'uint128' | 'uint136' | 'uint144' | 'uint152' | 'uint160' | 'uint168' | 'uint176' | 'uint184' | 'uint192' | 'uint200' | 'uint208' | 'uint216' | 'uint224' | 'uint232' | 'uint240' | 'uint248' | 'uint256' ;

Int
  : 'int' | 'int8' | 'int16' | 'int24' | 'int32' | 'int40' | 'int48' | 'int56' | 'int64' | 'int72' | 'int80' | 'int88' | 'int96' | 'int104' | 'int112' | 'int120' | 'int128' | 'int136' | 'int144' | 'int152' | 'int160' | 'int168' | 'int176' | 'int184' | 'int192' | 'int200' | 'int208' | 'int216' | 'int224' | 'int232' | 'int240' | 'int248' | 'int256' ;

Byte
   : 'bytes1' | 'bytes2' | 'bytes3' | 'bytes4' | 'bytes5' | 'bytes6' | 'bytes7' | 'bytes8' | 'bytes9' | 'bytes10' | 'bytes11' | 'bytes12' | 'bytes13' | 'bytes14' | 'bytes15' | 'bytes16' | 'bytes17' | 'bytes18' | 'bytes19' | 'bytes20' | 'bytes21' | 'bytes22' | 'bytes23' | 'bytes24' | 'bytes25' | 'bytes26' | 'bytes27' | 'bytes28' | 'bytes29' | 'bytes30' | 'bytes31' | 'bytes32' ;

// CHANGED: INLINED: primaryExpression
// REMOVED from primaryExpression:
// - HexLiteral
// - elementaryTypeNameExpression ('[' ']')? (for type casts)
// CHANGED from primaryExpression:
// - identifier ('[' ']')? -> identifier
// - added me and all
// REMOVED:
// - 'new' typeName
// - ('after' | 'delete') expression
expression
  : MeKeyword # MeExpr
  | AllKeyword # AllExpr
  | expr=expression op=('++' | '--') # PostCrementExpr
  | arr=expression '[' index=expression ']' # IndexExpr
  | elem_type=elementaryTypeName '(' expr=expression ')' # PrimitiveCastExpr
  | func=expression '(' args=functionCallArguments ')' # FunctionCallExpr
  | expr=expression '.' member=identifier # MemberAccessExpr
  | '(' expr=expression ')' # ParenthesisExpr
  | op=('++' | '--') expr=expression # PreCrementExpr
  | op=('+' | '-') expr=expression # SignExpr
  | '!' expr=expression # NotExpr
  | '~' expr=expression # BitwiseNotExpr
  | lhs=expression op='**' rhs=expression # PowExpr
  | lhs=expression op=('*' | '/' | '%') rhs=expression # MultDivModExpr
  | lhs=expression op=('+' | '-') rhs=expression # PlusMinusExpr
  | lhs=expression op=('<<' | '>>') rhs=expression # BitShiftExpr
  | lhs=expression op='&' rhs=expression # BitwiseAndExpr
  | lhs=expression op='^' rhs=expression # BitwiseXorExpr
  | lhs=expression op='|' rhs=expression # BitwiseOrExpr
  | lhs=expression op=('<' | '>' | '<=' | '>=') rhs=expression # CompExpr
  | lhs=expression op=('==' | '!=') rhs=expression # EqExpr
  | lhs=expression op='&&' rhs=expression # AndExpr
  | lhs=expression op='||' rhs=expression # OrExpr
  | cond=expression '?' then_expr=expression ':' else_expr=expression # IteExpr
  | lhs=expression op=('=' | '|=' | '^=' | '&=' | '<<=' | '>>=' | '+=' | '-=' | '*=' | '/=' | '%=') rhs=expression # AssignmentExpr
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
  : DecimalNumber | HexNumber ;

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
  : ( DecimalDigits ) ( [eE] DecimalDigits )? ; // NB: removed fractional literals since they are useless without fixed point type
  //: ([0-9]+ | ([0-9]* '.' [0-9]+) ) ( [eE] [0-9]+ )? ;

fragment
DecimalDigits
  : [0-9] ( '_'? [0-9] )* ;

HexNumber
  : '0' [xX] HexDigits ;

fragment
HexDigits
  : HexCharacter ( '_'? HexCharacter )* ;

fragment
HexCharacter
  : [0-9A-Fa-f] ;

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
