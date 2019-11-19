from datetime import datetime
from textwrap import dedent
from typing import Dict, List, Optional

import zkay.config as cfg
from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper, HybridArgumentIdf
from zkay.compiler.privacy.transformer.zkay_transformer import proof_param_name
from zkay.zkay_ast.ast import ContractDefinition, SourceUnit, ConstructorOrFunctionDefinition, \
    ConstructorDefinition, indent, FunctionCallExpr, IdentifierExpr, BuiltinFunction, \
    StateVariableDeclaration, MemberAccessExpr, IndexExpr, Parameter, TypeName, AnnotatedTypeName, Identifier, \
    ReturnStatement, EncryptionExpression, MeExpr, Expression, LabeledBlock, CipherText, Key, Randomness, SliceExpr, \
    Array, Comment, AddressTypeName, StructTypeName, HybridArgType, CircuitInputStatement, \
    AddressPayableTypeName, CircuitComputationStatement, BlankLine, VariableDeclarationStatement
from zkay.zkay_ast.visitor.python_visitor import PythonCodeVisitor

PROJECT_DIR_NAME = 'self.project_dir'
PROVER_OBJ_NAME = 'self.prover'
CRYPTO_OBJ_NAME = 'self.crypto'
CONN_OBJ_NAME = 'self.conn'
KEYSTORE_OBJ_NAME = 'self.keystore'
SK_OBJ_NAME = f'{KEYSTORE_OBJ_NAME}.sk'
PK_OBJ_NAME = f'{KEYSTORE_OBJ_NAME}.pk'
PRIV_VALUES_NAME = 'self.priv_values'
STATE_VALUES_NAME = 'self.state_values'
CONTRACT_NAME = 'self.contract_name'
CONTRACT_HANDLE = 'self.contract_handle'
GET_STATE = 'self.get_state'
IS_EXTERNAL_CALL = 'self.is_external'

UINT256_MAX_NAME = 'uint256_scalar_field'
SCALAR_FIELD_NAME = 'bn128_scalar_field'


class PythonOffchainVisitor(PythonCodeVisitor):
    def __init__(self, circuits: List[CircuitHelper]):
        super().__init__(False)
        self.circuits: Dict[ConstructorOrFunctionDefinition, CircuitHelper] = {cg.fct: cg for cg in circuits}

        self.current_f: Optional[ConstructorOrFunctionDefinition] = None
        self.current_params: Optional[List[Parameter]] = None
        self.current_circ: Optional[CircuitHelper] = None
        self.current_index: List[Expression] = []
        self.current_index_t: Optional[AnnotatedTypeName] = None

        self.inside_circuit: bool = False
        self.follow_private: bool = False

    def visitAddressTypeName(self, ast: AddressTypeName):
        return 'AddressValue'

    def visitSourceUnit(self, ast: SourceUnit):
        ctrcs = self.visit_list(ast.contracts)
        return dedent(f'''\
        ###########################################
        ## THIS CODE WAS GENERATED AUTOMATICALLY ##
        ## Creation Time: {datetime.now().strftime('%H:%M:%S %d-%b-%Y')}   ##
        ###########################################

        import os
        import code
        import inspect
        from typing import Dict, List, Optional, Union, Any, Callable

        from zkay import my_logging
        from zkay.transaction.interface import CipherValue, AddressValue, RandomnessValue, PublicKeyValue
        from zkay.transaction.offchain import {UINT256_MAX_NAME}, {SCALAR_FIELD_NAME}, ContractSimulator, CleanState


        ''') + ctrcs + (dedent(f'''
        def deploy(*args):
            return {self.visit(ast.contracts[0].idf)}.deploy(os.path.dirname(os.path.realpath(__file__)), *args)


        def connect(address: str):
            return {self.visit(ast.contracts[0].idf)}.connect(os.path.dirname(os.path.realpath(__file__)), address)


        def help():
            ContractSimulator.help(inspect.getmembers({self.visit(ast.contracts[0].idf)}, inspect.isfunction))


        me = ContractSimulator.my_address().val
        ''') if len(ast.contracts) == 1 else '') + dedent('''
        if __name__ == '__main__':
            log_file = my_logging.get_log_file(filename='transactions', parent_dir="", include_timestamp=True, label=None)
            my_logging.prepare_logger(log_file)
            code.interact(local=locals())
        ''')

    def generate_constructors(self, ast: ContractDefinition) -> str:
        # Priv values: private function args plaintext, locally decrypted plaintexts, encryption randomness
        # State values: if key not in dict -> pull value from chain on read, otherwise retrieve cached value
        name = self.visit(ast.idf)

        if not ast.constructor_definitions:
            deploy_cmd = f'c.conn.deploy(project_dir, \'{ast.idf.name}\', [], [])'
        else:
            deploy_cmd = f'c.constructor(*constructor_args)'

        return indent(dedent(f'''\
            def __init__(self, project_dir: str):
                super().__init__(project_dir)
                {CONTRACT_NAME} = '{ast.idf.name}'

            @staticmethod
            def connect(project_dir: str, address: str) -> '{name}':
                c = {name}(project_dir)
                c.contract_handle = c.conn.connect(project_dir, '{ast.idf.name}', AddressValue(address))
                return c

            @staticmethod
            def deploy(project_dir: str, *constructor_args) -> '{name}':
                c = {name}(project_dir)
                c.contract_handle = {deploy_cmd}
                return c

        '''))

    def get_loc_value(self, arr: Identifier, indices: List[str]) -> str:
        if isinstance(arr, HybridArgumentIdf) and arr.arg_type == HybridArgType.PRIV_CIRCUIT_VAL and not arr.name.startswith('tmp'):
            return f'{PRIV_VALUES_NAME}["{arr.name}"]'
        else:
            idxvals = ''.join([f'[{idx}]' for idx in indices])
            return f'{self.visit(arr)}{idxvals}'

    @staticmethod
    def _is_builtin_var(idf: IdentifierExpr):
        if idf.target is None or idf.target.annotated_type is None:
            return False
        else:
            t = idf.target.annotated_type.type_name
            return isinstance(t, StructTypeName) and t.names[0].name.startswith('<')

    def get_rvalue(self, idf: IdentifierExpr, val_type: AnnotatedTypeName, indices: List[str]) -> str:
        if isinstance(idf.target, StateVariableDeclaration) and not self._is_builtin_var(idf):
            is_encrypted = bool(val_type.old_priv_text)
            name_str = f"'{idf.idf.name}'"
            constr = ''
            if val_type.is_address():
                constr = ', val_constructor=AddressValue'
            size = 0 if not isinstance(val_type.type_name, Array) else val_type.type_name.size_in_uints
            val_str = f"{GET_STATE}({', '.join([name_str] + indices)}, count={size}, is_encrypted={is_encrypted}{constr})"
            return val_str
        else:
            return self.get_loc_value(idf.idf, indices)

    def get_lvalue(self, idf: IdentifierExpr, indices: List[str]):
        if isinstance(idf.target, StateVariableDeclaration) and not self._is_builtin_var(idf):
            idxvals = ''.join([f'[{{{idx}}}]' for idx in indices])
            return f"{STATE_VALUES_NAME}[f'{idf.idf.name}{idxvals}']"
        else:
            return self.get_loc_value(idf.idf, indices)

    def visitContractDefinition(self, ast: ContractDefinition):
        constr = self.visit_list(ast.constructor_definitions)
        fcts = self.visit_list(ast.function_definitions)

        return f'class {self.visit(ast.idf)}(ContractSimulator):\n' \
               f'{self.generate_constructors(ast)}' + \
               (f'{indent(constr)}\n' if constr else '') + \
               (f'{indent(fcts)}\n' if fcts else '')

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        with CircuitContext(self, ast):
            fct = super().visitConstructorOrFunctionDefinition(ast)
            if cfg.generate_offchain_circuit_simulation_code and self.current_circ.requires_verification():
                fct = f'{fct}{self.build_proof_check_fct()}'
            return fct

    def visitParameter(self, ast: Parameter):
        if ast.original_type is None:
            t = 'Any'
        elif ast.original_type.is_address():
            t = 'str'
        else:
            t = self.visit(ast.original_type.type_name)
        return f'{self.visit(ast.idf)}: {t}'

    def handle_function_params(self, params: List[Parameter]):
        return super().handle_function_params(self.current_params)

    def handle_function_body(self, ast: ConstructorOrFunctionDefinition):
        address_params = [self.visit(param.idf) for param in self.current_params if param.original_type.is_address()]
        address_wrap_str = ''
        if address_params:
            address_wrap_str = f"{', '.join(address_params)} = {', '.join([f'AddressValue({p})' for p in address_params])}\n"

        circuit = self.current_circ
        all_params = ', '.join([f'{self.visit(param.idf)}' for param in self.current_params])

        preamble_str = f'''\
            msg = lambda: None
            msg.sender = {CONN_OBJ_NAME}.my_address
        '''

        in_var_decl_str = None if self.current_circ.has_in_args else f'{cfg.zk_in_name} = []'

        # Encrypt parameters and add private circuit inputs (plain + randomness)
        enc_param_str = ''
        for arg in self.current_params:
            if arg.original_type is not None and arg.original_type.is_private():
                sname = self.visit(arg.idf)
                enc_param_str += f'{PRIV_VALUES_NAME}["{arg.idf.name}"] = {sname}\n'
                enc_param_str += f'{sname}, {PRIV_VALUES_NAME}["{arg.idf.name}_R"] = {CRYPTO_OBJ_NAME}.enc({sname}, {PK_OBJ_NAME})\n'
        enc_param_comment_str = '\n# Encrypt parameters' if enc_param_str else ''
        enc_param_str = enc_param_str[:-1] if enc_param_str else ''

        actual_params_assign_str = f"actual_params = [{all_params}]"

        # Simulate public contract to compute in_values (state variable values are pulled from blockchain if necessary)
        # (out values are also computed when encountered, by locally evaluating and encrypting
        # the corresponding private expressions)
        begin_body_comment_str = f'\n## BEGIN Simulate body'
        body_str = self.visit(ast.body)
        body_str = body_str[:-1] if body_str.endswith('\n') else body_str
        end_body_comment_str = '## END Simulate body'

        # Add out__, in__ and proof to actual argument list (when required)
        generate_proof_str = ''

        if self.current_circ.has_out_args:
            out_stmts = [BlankLine()] + Comment.comment_wrap_block('Serialize output values', [
                Identifier(cfg.zk_out_name).decl_var(Array(AnnotatedTypeName.uint_all(), circuit.public_out_size))]
                + [out_idf.serialized_loc.assign(SliceExpr(out_idf.get_loc_expr(), 0, out_idf.t.size_in_uints)) if isinstance(out_idf.t, Array) else \
                   IdentifierExpr(f'{cfg.zk_out_name}[{out_idf.serialized_loc.start}]').assign(out_idf.get_loc_expr().implicitly_converted(TypeName.uint_type())) for out_idf in circuit.output_idfs])
            out_var_decl_str = self.visit_list(out_stmts) + f'actual_params.append({cfg.zk_out_name})'
        else:
            out_var_decl_str = cfg.zk_out_name + ' = []'

        if circuit.requires_verification():
            priv_args = ''
            for idx, val in enumerate(circuit.sec_idfs):
                priv_args += f"{PRIV_VALUES_NAME}.get('{val.name}', {self.get_default_value(val.t)}),"
                priv_args += '\n' if idx % 2 == 1 else ' '
            priv_args = 'priv_arg_list = [\n' + indent(priv_args) + ']'

            generate_proof_str += '\n'.join(['\n#Generate proof', priv_args, self.call_python_proof_simulator(ast.name),
                                             f"proof = {PROVER_OBJ_NAME}.generate_proof({PROJECT_DIR_NAME}, {CONTRACT_NAME}, '{ast.name}', priv_arg_list, {cfg.zk_in_name}, {cfg.zk_out_name})",
                                             'actual_params.append(proof)'])

        should_encrypt = ", ".join([str(bool(p.annotated_type.old_priv_text)) for p in self.current_f.parameters])
        if isinstance(ast, ConstructorDefinition):
            invoke_transact_str = f'''
            # Deploy contract
            return {CONN_OBJ_NAME}.deploy({PROJECT_DIR_NAME}, {CONTRACT_NAME}, actual_params, [{should_encrypt}])
            '''
        elif circuit.requires_verification() or circuit.fct.has_side_effects:
            invoke_transact_str = f'''
            # Invoke public transaction
            return {CONN_OBJ_NAME}.transact({CONTRACT_HANDLE}, '{ast.name}', actual_params, [{should_encrypt}])
            '''
        elif ast.return_parameters:
            assert len(ast.return_parameters) == 1
            t = ast.return_parameters[0].annotated_type.type_name
            constr = '{}'
            if isinstance(t, AddressTypeName) or isinstance(t, AddressPayableTypeName):
                constr = 'AddressValue({})'
            elif isinstance(t, CipherText):
                constr = 'CipherValue({})'
            elif isinstance(t, Key):
                constr = 'PublicKeyValue({})'

            invoke_transact_str = f'''
            # Call pure/view function and return value
            return {constr.format(f"{CONN_OBJ_NAME}.call({CONTRACT_HANDLE}, '{ast.name}', *actual_params)")}
            '''
        else:
            invoke_transact_str = ''

        pre_body_code = f'if {IS_EXTERNAL_CALL}:\n' + indent('\n'.join(dedent(s) for s in [
            address_wrap_str,
            in_var_decl_str,
            enc_param_comment_str,
            enc_param_str,
            actual_params_assign_str] if s))

        body_code = '\n'.join(dedent(s) for s in [
            begin_body_comment_str,
            body_str,
            end_body_comment_str,
        ] if s) + '\n'

        post_body_code = f'if {IS_EXTERNAL_CALL}:\n' + indent('\n'.join(dedent(s) for s in [
            out_var_decl_str,
            generate_proof_str,
            invoke_transact_str
        ] if s))

        code = '\n'.join(s for s in [
            dedent(preamble_str),
            pre_body_code,
            body_code,
            post_body_code
        ] if s)

        return 'with CleanState(self):\n' + indent(code)

    def visitCircuitInputStatement(self, ast: CircuitInputStatement):
        in_decrypt = ''
        in_idf = ast.lhs.member
        assert isinstance(in_idf, HybridArgumentIdf)
        if in_idf.corresponding_priv_expression is not None:
            plain_idf_name = f'{PRIV_VALUES_NAME}["{in_idf.corresponding_priv_expression.idf.name}"]'
            in_decrypt += f'\n{plain_idf_name}, {PRIV_VALUES_NAME}["{in_idf.name}_R"]' \
                          f' = {CRYPTO_OBJ_NAME}.dec({self.visit(in_idf.get_loc_expr())}, {SK_OBJ_NAME})'
            plain_idf = IdentifierExpr(plain_idf_name).as_type(TypeName.uint_type())
            conv = self.visit(plain_idf.implicitly_converted(in_idf.corresponding_priv_expression.idf.t))
            if conv != plain_idf_name:
                in_decrypt += f'\n{plain_idf_name} = {conv}'
        return self.visitAssignmentStatement(ast) + in_decrypt

    def visitCircuitComputationStatement(self, ast: CircuitComputationStatement):
        out_initializations = ''
        out_idf = ast.idf
        out_val = out_idf.corresponding_priv_expression
        if isinstance(out_val, EncryptionExpression):
            s = f'{self.visit(out_idf.get_loc_expr())}, {PRIV_VALUES_NAME}["{out_idf.name}_R"] = {self.visit(out_val)}'
        else:
            s = f'{self.visit(out_idf.get_loc_expr())} = {self.visit(out_val)}'
        out_initializations += f'{s}\n'
        return out_initializations

    def visitLabeledBlock(self, ast: LabeledBlock):
        return None

    def visitEncryptionExpression(self, ast: EncryptionExpression):
        priv_str = 'msg.sender' if isinstance(ast.privacy, MeExpr) else self.visit(ast.privacy.clone())
        with CircuitComputation(self, True):
            plain = self.visit(ast.expr)
            return f'{CRYPTO_OBJ_NAME}.enc({plain}, {KEYSTORE_OBJ_NAME}.getPk({priv_str}))'

    def visitReturnStatement(self, ast: ReturnStatement):
        return f'if not {IS_EXTERNAL_CALL}:\n{cfg.indentation}{super().visitReturnStatement(ast)}'

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction) and ast.func.is_arithmetic():
            modulo = SCALAR_FIELD_NAME if self.inside_circuit else UINT256_MAX_NAME
            return f'({super().visitFunctionCallExpr(ast)}) % {modulo}'
        elif isinstance(ast.func, BuiltinFunction) and ast.func.is_comp():
            args = [f'self.comp_overflow_checked({self.visit(a)})' for a in ast.args]
            return ast.func.format_string().format(*args)

        return super().visitFunctionCallExpr(ast)

    def visitMemberAccessExpr(self, ast: MemberAccessExpr):
        assert not isinstance(ast.target, StateVariableDeclaration), "State member accesses not handled"
        if self.current_index:
            indices = list(reversed(self.current_index))
            self.current_index, self.current_index_t = [], None
            indices = [self.visit(idx) for idx in indices]
        else:
            indices = []

        if isinstance(ast.member, HybridArgumentIdf):
            e = f'{self.visit(ast.expr)}["{ast.member.name}"]'
        else:
            e = super().visitMemberAccessExpr(ast)
        return self.get_loc_value(Identifier(e), indices)

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        if ast.idf.name == f'{cfg.pki_contract_name}_inst' and not ast.is_lvalue():
            return f'{KEYSTORE_OBJ_NAME}'

        if self.current_index:
            indices, t = list(reversed(self.current_index)), self.current_index_t
            self.current_index, self.current_index_t = [], None
            indices = [self.visit(idx) for idx in indices]
        elif self.inside_circuit and isinstance(ast.idf, HybridArgumentIdf) and ast.idf.corresponding_priv_expression is not None and self.follow_private:
            return self.visit(ast.idf.corresponding_priv_expression)
        else:
            indices, t = [], ast.target.annotated_type if isinstance(ast.target, StateVariableDeclaration) else None

        if ast.is_rvalue():
            return self.get_rvalue(ast, t, indices)
        else:
            return self.get_lvalue(ast, indices)

    def visitIndexExpr(self, ast: IndexExpr):
        if self.current_index_t is None:
            self.current_index_t = ast.target.annotated_type
        self.current_index.append(ast.key)

        return self.visit(ast.arr)

    def visitCipherText(self, ast: CipherText):
        return 'CipherValue'

    def visitKey(self, ast: Key):
        return 'PublicKeyValue'

    def visitRandomness(self, ast: Randomness):
        return 'RandomnessValue'

    def call_python_proof_simulator(self, function_name) -> str:
        return ''

    def build_proof_check_fct(self) -> str:
        return ''

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        if ast.variable_declaration.idf.name == cfg.zk_data_var_name:
            c = self.current_circ
            s = ''
            for idx, val in enumerate(c.output_idfs + c.input_idfs + c.temp_vars_outside_circuit):
                s += f"'{val.name}': {self.get_default_value(val.t)},"
                s += '\n' if idx % 4 == 3 else ' '
            return f'{cfg.zk_data_var_name}: Dict = {{\n' + indent(s) + '}'
        else:
            return super().visitVariableDeclarationStatement(ast)


class CircuitContext:
    def __init__(self, v: PythonOffchainVisitor, ast: ConstructorOrFunctionDefinition):
        self.v = v
        self.f = ast

    def __enter__(self):
        self.v.current_f = self.f
        self.v.current_circ = self.v.circuits[self.f]
        self.v.current_params = [p for p in self.f.parameters if p.idf.name != cfg.zk_out_name and p.idf.name != proof_param_name]

    def __exit__(self, t, value, traceback):
        self.v.current_f = None
        self.v.current_circ = None
        self.v.current_params = None


class CircuitComputation:
    def __init__(self, v: PythonOffchainVisitor, follow_private: bool = False):
        self.v = v
        self.follow_private = follow_private
        self.old_fp = None

    def __enter__(self):
        assert not self.v.inside_circuit
        self.v.inside_circuit = True
        self.old_fp = self.v.follow_private
        self.v.follow_private = self.follow_private

    def __exit__(self, t, value, traceback):
        assert self.v.inside_circuit
        self.v.inside_circuit = False
        self.follow_private = self.old_fp
