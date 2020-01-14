# BUILTIN SPECIAL TYPE DEFINITIONS
from zkay.zkay_ast.ast import AnnotatedTypeName, FunctionTypeName, Parameter, Identifier, StructDefinition, \
    VariableDeclaration, TypeName, StateVariableDeclaration, UserDefinedTypeName, StructTypeName, Block, ConstructorOrFunctionDefinition
from zkay.zkay_ast.pointers.parent_setter import set_parents

array_length_member = VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('length'))


class GlobalDefs:
    # gasleft: FunctionDefinition = FunctionDefinition(
    #     idf=Identifier('gasleft'),
    #     parameters=[],
    #     modifiers=[],
    #     return_parameters=[Parameter([], annotated_type=AnnotatedTypeName.uint_all(), idf=Identifier(''))],
    #     body=Block([])
    # )
    # gasleft.idf.parent = gasleft

    address_struct: StructDefinition = StructDefinition(
        Identifier('<address>'), [
            VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('balance'))
        ]
    )
    set_parents(address_struct)

    address_payable_struct: StructDefinition = StructDefinition(
        Identifier('<address_payable>'), [
            VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('balance')),
            ConstructorOrFunctionDefinition(Identifier('send'), [Parameter([], AnnotatedTypeName.uint_all(), Identifier(''))], ['public'],
                                            [Parameter([], AnnotatedTypeName.bool_all(), Identifier(''))], Block([])),
            ConstructorOrFunctionDefinition(Identifier('transfer'), [Parameter([], AnnotatedTypeName.uint_all(), Identifier(''))], ['public'],
                                            [], Block([])),
        ]
    )
    address_payable_struct.members[1].can_be_private = False
    address_payable_struct.members[2].can_be_private = False
    set_parents(address_payable_struct)

    msg_struct: StructDefinition = StructDefinition(
        Identifier('<msg>'), [
            VariableDeclaration([], AnnotatedTypeName(TypeName.address_payable_type()), Identifier('sender')),
            VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('value')),
        ]
    )
    set_parents(msg_struct)

    block_struct: StructDefinition = StructDefinition(
        Identifier('<block>'), [
            VariableDeclaration([], AnnotatedTypeName(TypeName.address_payable_type()), Identifier('coinbase')),
            VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('difficulty')),
            VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('gaslimit')),
            VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('number')),
            VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('timestamp')),
        ]
    )
    set_parents(block_struct)

    tx_struct: StructDefinition = StructDefinition(
        Identifier('<tx>'), [
            VariableDeclaration([], AnnotatedTypeName.uint_all(), Identifier('gasprice')),
            VariableDeclaration([], AnnotatedTypeName(TypeName.address_payable_type()), Identifier('origin')),
        ]
    )
    set_parents(tx_struct)


class GlobalVars:
    msg: StateVariableDeclaration = StateVariableDeclaration(
        AnnotatedTypeName.all(StructTypeName([GlobalDefs.msg_struct.idf], GlobalDefs.msg_struct)), [],
        Identifier('msg'), None
    )
    msg.idf.parent = msg

    block: StateVariableDeclaration = StateVariableDeclaration(
        AnnotatedTypeName.all(StructTypeName([GlobalDefs.block_struct.idf], GlobalDefs.block_struct)), [],
        Identifier('block'), None
    )
    block.idf.parent = block

    tx: StateVariableDeclaration = StateVariableDeclaration(
        AnnotatedTypeName.all(StructTypeName([GlobalDefs.tx_struct.idf], GlobalDefs.tx_struct)), [],
        Identifier('tx'), None
    )
    tx.idf.parent = tx

    now: StateVariableDeclaration = StateVariableDeclaration(
        AnnotatedTypeName.uint_all(), [],
        Identifier('now'), None
    )
    now.idf.parent = now
