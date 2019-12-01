from typing import Dict, Optional, List, Tuple

import zkay.config as cfg
from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper
from zkay.compiler.privacy.transformer.internal_call_transformer import transform_internal_calls
from zkay.compiler.privacy.transformer.transformer_visitor import AstTransformerVisitor
from zkay.compiler.privacy.transformer.zkay_transformer import ZkayVarDeclTransformer, ZkayExpressionTransformer, ZkayCircuitTransformer, \
    ZkayStatementTransformer
from zkay.compiler.privacy.used_contract import get_contract_instance_idf
from zkay.zkay_ast.ast import Expression, ConstructorOrFunctionDefinition, IdentifierExpr, VariableDeclaration, AnnotatedTypeName, \
    StateVariableDeclaration, Identifier, ExpressionStatement, SourceUnit, ReturnStatement, AST, \
    Comment, FunctionDefinition, NumberLiteralExpr, CastExpr, StructDefinition, Array, FunctionCallExpr, StructTypeName, \
    ContractTypeName, BlankLine, Block, RequireStatement, NewExpr, ContractDefinition, ConstructorDefinition, SliceExpr, LabeledBlock
from zkay.zkay_ast.pointers.parent_setter import set_parents
from zkay.zkay_ast.pointers.symbol_table import link_identifiers
from zkay.zkay_ast.visitor.deep_copy import deep_copy


def transform_ast(ast: AST) -> Tuple[AST, 'ZkayTransformer']:
    zt = ZkayTransformer()
    new_ast = zt.visit(ast)

    # restore all parent pointers and identifier targets
    set_parents(new_ast)
    link_identifiers(new_ast)
    return new_ast, zt


class ZkayTransformer(AstTransformerVisitor):
    """ Transformer, which transforms zkay contracts into equivalent public solidity contracts """

    def __init__(self):
        super().__init__()
        self.circuit_generators: Dict[ConstructorOrFunctionDefinition, CircuitHelper] = {}
        self.var_decl_trafo = ZkayVarDeclTransformer()

    @staticmethod
    def set_unique_fct_names(c: ContractDefinition):
        # TODO make sure there are no conflicts with altered names
        fcts_with_same_name: Dict[str, List[ConstructorOrFunctionDefinition]] = {}
        for f in c.constructor_definitions + c.function_definitions:
            fcts_with_same_name.setdefault(f.name, []).append(f)
        for name, fcts in fcts_with_same_name.items():
            if len(fcts) == 1:
                fcts[0].unambiguous_name = name
            else:
                for idx in range(len(fcts)):
                    fcts[idx].unambiguous_name = f'{name}_{idx}'

    @staticmethod
    def import_contract(vname: str, out_filenames: List[str], out_ext_vars_decls: List[StateVariableDeclaration], gen: Optional[CircuitHelper] = None):
        inst_idf = get_contract_instance_idf(vname)
        c_type = ContractTypeName([Identifier(vname)])
        import_filename = f'./{vname}.sol'

        if gen:
            gen.verifier_contract_type = c_type
            gen.verifier_contract_filename = import_filename

        out_filenames.append(import_filename)
        out_ext_vars_decls.append(StateVariableDeclaration(AnnotatedTypeName(c_type), ['constant'], inst_idf.clone(), CastExpr(c_type, NumberLiteralExpr(0))))

    def include_verification_contracts(self, c: ContractDefinition, ext_var_decls: List[StateVariableDeclaration]):
        import_filenames = []

        for f in c.constructor_definitions + c.function_definitions:
            if f.requires_verification_when_external:
                name = f'Verify_{c.idf.name}_{f.unambiguous_name}'
                self.import_contract(name, import_filenames, ext_var_decls, self.circuit_generators[f])

        # Add external contract state variables
        c.state_variable_declarations = Comment.comment_list('External contracts', ext_var_decls) + \
                                        [Comment('User state variables')] + c.state_variable_declarations

        return import_filenames

    @staticmethod
    def create_circuit_helper(fct: ConstructorOrFunctionDefinition, global_owners: List, internal_circ: Optional[CircuitHelper] = None):
        return CircuitHelper(fct, global_owners, ZkayExpressionTransformer, ZkayCircuitTransformer, internal_circ)

    def visitSourceUnit(self, ast: SourceUnit):
        # Include pki contract
        pki_decl = []
        self.import_contract(cfg.pki_contract_name, ast.used_contracts, pki_decl)

        for c in ast.contracts:
            self.transform_contract(ast, c, [deep_copy(pki_decl[0])])

        return ast

    def transform_contract(self, su: SourceUnit, c: ContractDefinition, ext_var_decls: List[StateVariableDeclaration]):
        # Get list of static owner labels for this contract
        global_owners = [Expression.me_expr()]
        for var in c.state_variable_declarations:
            if var.annotated_type.is_address() and 'final' in var.keywords:
                global_owners.append(var.idf)

        # Transform types of normal state variables
        c.state_variable_declarations = self.var_decl_trafo.visit_list(c.state_variable_declarations)

        self.set_unique_fct_names(c)

        # Split into functions which require verification and those which don't and create generators
        all_fcts = c.constructor_definitions + c.function_definitions
        req_ext_fcts = {}
        new_fcts, new_constr = [], []
        for fct in all_fcts:
            assert isinstance(fct, ConstructorOrFunctionDefinition)
            if fct.requires_verification or fct.requires_verification_when_external:
                self.circuit_generators[fct] = self.create_circuit_helper(fct, global_owners)

            if fct.requires_verification_when_external:
                req_ext_fcts[fct] = fct.parameters[:]
            elif isinstance(fct, ConstructorDefinition):
                new_constr.append(fct)
            else:
                new_fcts.append(fct)

        # Import verification contracts
        su.used_contracts += self.include_verification_contracts(c, ext_var_decls)

        # Transform signatures
        for f in all_fcts:
            f.parameters = self.var_decl_trafo.visit_list(f.parameters)
        for f in c.function_definitions:
            f.return_parameters = self.var_decl_trafo.visit_list(f.return_parameters)

        # Transform bodies
        for fct in all_fcts:
            gen = self.circuit_generators.get(fct, None)
            fct.original_body = fct.body
            fct.body = ZkayStatementTransformer(gen).visit(fct.body.clone())

        # Transform hybrid functions to support verification
        hybrid_fcts = [fct for fct in all_fcts if fct.requires_verification]
        transform_internal_calls(hybrid_fcts, self.circuit_generators)
        for f in hybrid_fcts:
            circuit = self.circuit_generators[f]
            assert circuit.requires_verification()
            if circuit.out_size + circuit.in_size > 0:
                zk_data_struct = StructDefinition(Identifier(circuit.zk_data_struct_name), [
                    VariableDeclaration([], AnnotatedTypeName(idf.t), idf.clone(), '')
                    for idf in circuit.output_idfs + circuit.input_idfs
                ])
                circuit.internal_zk_data_struct = zk_data_struct
                c.struct_definitions.append(zk_data_struct)
            self.create_internal_verification_wrapper(f)

        # Introduce external functions which perform verification if necessary
        for f, params in req_ext_fcts.items():
            orig_params = f.parameters[:-4] if f.requires_verification else f.parameters

            def param_copy(parameters, new_storage='memory'):
                return [deep_copy(p, with_types=True).with_changed_storage('memory', new_storage) for p in parameters]

            is_payable = 'payable' in f.modifiers

            if isinstance(f, ConstructorDefinition):
                circuit = self.circuit_generators.pop(f)
                f = f.as_function()
                circuit.fct = f
                self.circuit_generators[f] = circuit

                new_f = ConstructorDefinition(param_copy(orig_params), ['public'], Block([]))
                new_constr.append(new_f)
            else:
                new_f = FunctionDefinition(Identifier(f.name), param_copy(orig_params, 'calldata'), ['external'],
                                           param_copy(f.return_parameters), Block([]))
                new_fcts.append(new_f)

            # Make function internal
            f.idf = Identifier(cfg.get_internal_name(f))
            f.modifiers = ['internal' if mod == 'public' else mod for mod in f.modifiers if mod != 'payable']
            f.can_be_external = False
            f.requires_verification_when_external = False
            new_fcts.append(f)

            # Create new external wrapper function
            new_f.unambiguous_name = f.unambiguous_name
            new_f.requires_verification = True
            new_f.requires_verification_when_external = True
            new_f.called_functions = f.called_functions
            if is_payable:
                new_f.modifiers.append('payable')
            self.create_external_verification_wrapper(new_f, f, global_owners)

        c.constructor_definitions = new_constr
        c.function_definitions = new_fcts
        return c

    def create_internal_verification_wrapper(self, ast: ConstructorOrFunctionDefinition):
        circuit = self.circuit_generators[ast]
        stmts = []

        # Add additional params
        ast.add_param(Array(AnnotatedTypeName.uint_all()), cfg.zk_in_name)
        ast.add_param(AnnotatedTypeName.uint_all(), f'{cfg.zk_in_name}_start_idx')
        ast.add_param(Array(AnnotatedTypeName.uint_all()), cfg.zk_out_name)
        ast.add_param(AnnotatedTypeName.uint_all(), f'{cfg.zk_out_name}_start_idx')

        # Verify that in/out parameters have correct size
        out_start_idx, in_start_idx = IdentifierExpr(f'{cfg.zk_out_name}_start_idx'), IdentifierExpr(f'{cfg.zk_in_name}_start_idx')
        out_var, in_var = IdentifierExpr(cfg.zk_out_name), IdentifierExpr(cfg.zk_in_name)
        stmts.append(RequireStatement(out_start_idx.binop('+', NumberLiteralExpr(circuit.out_size_trans)).binop('<=', out_var.dot('length'))))
        stmts.append(RequireStatement(in_start_idx.binop('+', NumberLiteralExpr(circuit.in_size_trans)).binop('<=', in_var.dot('length'))))

        # Declare zk_data struct var (if needed)
        if circuit.internal_zk_data_struct is not None:
            zk_struct_type = StructTypeName([Identifier(circuit.zk_data_struct_name)])
            stmts += [Identifier(cfg.zk_data_var_name).decl_var(zk_struct_type), BlankLine()]

        # Declare return variable if necessary
        if isinstance(ast, FunctionDefinition) and ast.return_parameters:
            assert len(ast.return_parameters) == 1  # for now
            stmts += Comment.comment_list("Declare return variable", [
                Identifier(cfg.return_var_name).decl_var(ast.return_parameters[0].annotated_type)
            ])

        # Deserialize out array (if any)
        deserialize_stmts = []
        offset = 0
        for s in circuit.output_idfs:
            deserialize_stmts += [s.deserialize(cfg.zk_out_name, out_start_idx, offset)]
            offset += s.t.size_in_uints
        if deserialize_stmts:
            stmts.append(LabeledBlock(Comment.comment_wrap_block("Deserialize output values", deserialize_stmts), 'exclude'))

        # Include original transformed function body
        stmts += ast.body.statements

        # Serialize in parameters to in array (if any)
        serialize_stmts = []
        offset = 0
        for s in circuit.input_idfs:
            serialize_stmts += [s.serialize(cfg.zk_in_name, in_start_idx, offset)]
            offset += s.t.size_in_uints
        if offset:
            stmts += Comment.comment_wrap_block('Serialize input values', serialize_stmts)

        # Add return statement at the end if necessary
        # (was previously replaced by assignment to return_var by ZkayStatementTransformer)
        if circuit.has_return_var:
            stmts.append(ReturnStatement(IdentifierExpr(cfg.return_var_name)))

        ast.body.statements[:] = stmts

    def create_external_verification_wrapper(self, ext_fct: ConstructorOrFunctionDefinition, int_fct: FunctionDefinition, global_owners):
        # Create new circuit for external function
        circuit = self.create_circuit_helper(ext_fct, global_owners, self.circuit_generators[int_fct])
        if not int_fct.requires_verification:
            del self.circuit_generators[int_fct]
        self.circuit_generators[ext_fct] = circuit

        # Verify that out parameter has correct size
        stmts = [RequireStatement(IdentifierExpr(cfg.zk_out_name).dot('length').binop('==', NumberLiteralExpr(circuit.out_size_trans)))]

        # Check encrypted parameters
        param_stmts = []
        offset = 0
        for p in ext_fct.parameters:
            """ * of T_e rule 8 """
            if p.original_type.is_private():
                param_stmts.append(circuit.ensure_parameter_encryption(int_fct, p, offset))
                offset += p.annotated_type.type_name.size_in_uints

        # Request static public keys
        key_req_stmts = []
        if circuit.requested_global_keys:
            tmp_key_var = Identifier('_tmp_key')
            key_req_stmts.append(tmp_key_var.decl_var(AnnotatedTypeName.key_type()))
            for key_owner in circuit.requested_global_keys:
                idf, assignment = circuit.request_public_key(key_owner, circuit.get_glob_key_name(key_owner))
                assignment.lhs = IdentifierExpr(tmp_key_var.clone())
                key_req_stmts.append(assignment)
                key_req_stmts.append(SliceExpr(IdentifierExpr(cfg.zk_in_name), None, offset, idf.t.size_in_uints).assign(
                    SliceExpr(IdentifierExpr(tmp_key_var.clone()), None, 0, idf.t.size_in_uints)))
                offset += idf.t.size_in_uints
                assert offset == circuit.in_size

        # Declare in array
        new_in_array_expr = NewExpr(AnnotatedTypeName(Array(AnnotatedTypeName.uint_all())), [NumberLiteralExpr(circuit.in_size_trans)])
        in_var_decl = Identifier(cfg.zk_in_name).decl_var(Array(AnnotatedTypeName.uint_all()), new_in_array_expr)
        stmts.append(in_var_decl)

        stmts += Comment.comment_wrap_block('Backup private arguments for verification', param_stmts)
        stmts += Comment.comment_wrap_block('Request static public keys', key_req_stmts)

        # Call internal function
        args = [IdentifierExpr(param.idf.clone()) for param in ext_fct.parameters]
        internal_call = FunctionCallExpr(IdentifierExpr(int_fct.idf.clone()).with_target(int_fct), args)
        internal_call.sec_start_offset = circuit.priv_in_size
        ext_fct.called_functions[int_fct] = None
        if int_fct.requires_verification:
            circuit.call_function(internal_call)
            args += [IdentifierExpr(cfg.zk_in_name), NumberLiteralExpr(circuit.in_size),
                     IdentifierExpr(cfg.zk_out_name), NumberLiteralExpr(circuit.out_size)]

        if int_fct.return_parameters:
            in_call = Identifier(cfg.return_var_name).decl_var(int_fct.return_parameters[0].annotated_type, internal_call)
        else:
            in_call = ExpressionStatement(internal_call)
        stmts.append(in_call)

        # Add out and proof parameter
        storage_loc = 'calldata' if isinstance(ext_fct, FunctionDefinition) else 'memory'
        ext_fct.add_param(Array(AnnotatedTypeName.uint_all()), Identifier(cfg.zk_out_name), storage_loc)
        ext_fct.add_param(AnnotatedTypeName.proof_type(), Identifier(cfg.proof_param_name), storage_loc)

        # Call verifier
        verifier = IdentifierExpr(get_contract_instance_idf(circuit.verifier_contract_type.code()))
        verifier_args = [IdentifierExpr(cfg.proof_param_name), IdentifierExpr(cfg.zk_in_name), IdentifierExpr(cfg.zk_out_name)]
        verify = ExpressionStatement(verifier.call(cfg.verification_function_name, verifier_args))
        stmts.append(LabeledBlock([Comment('Verify zk proof of execution'), verify], 'exclude'))

        # Add return statement at the end if necessary
        if int_fct.return_parameters:
            stmts.append(ReturnStatement(IdentifierExpr(cfg.return_var_name)))

        ext_fct.body.statements = stmts
