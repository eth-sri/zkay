from datetime import datetime
from textwrap import dedent
from typing import Dict, List, Optional

import zkay.config as cfg
from zkay.compiler.privacy.circuit_generation.circuit_constraints import CircAssignment
from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper, HybridArgumentIdf, \
    TempVarDecl, EncConstraint, EqConstraint
from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.compiler.privacy.transformer.zkay_transformer import proof_param_name
from zkay.zkay_ast.ast import ContractDefinition, SourceUnit, ConstructorOrFunctionDefinition, \
    ConstructorDefinition, indent, FunctionCallExpr, IdentifierExpr, BuiltinFunction, \
    StateVariableDeclaration, Statement, MemberAccessExpr, IndexExpr, Parameter, TypeName, AnnotatedTypeName, \
    Identifier, \
    ReturnStatement, EncryptionExpression, MeExpr, Expression, LabeledBlock, CipherText, Key, Randomness, SliceExpr, \
    Array, Comment, AddressTypeName
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

UINT256_MAX_NAME = '_uint256_scalar_field'
SCALAR_FIELD_NAME = '_bn128_scalar_field'
SCALAR_FIELD_COMP_MAX_NAME = '_bn128_comp_scalar_field'


class PythonOffchainVisitor(PythonCodeVisitor):
    def __init__(self, circuits: List[CircuitHelper]):
        super().__init__(False)
        self.circuits: Dict[ConstructorOrFunctionDefinition, CircuitHelper] = {cg.fct: cg for cg in circuits}

        self.py_plain = PythonCodeVisitor(True)
        self.py = PythonCodeVisitor(False)
        self.current_f: Optional[ConstructorOrFunctionDefinition] = None
        self.current_params: Optional[List[Parameter]] = None
        self.current_circ: Optional[CircuitHelper] = None
        self.current_index: List[Expression] = []
        self.current_index_t: Optional[AnnotatedTypeName] = None

        self.inside_circuit: bool = False

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
        from zkay.transaction.runtime import Runtime
        from zkay.transaction.interface import CipherValue, AddressValue, RandomnessValue, PublicKeyValue

        {UINT256_MAX_NAME} = {1 << 256}
        {SCALAR_FIELD_NAME} = {bn128_scalar_field}
        {SCALAR_FIELD_COMP_MAX_NAME} = {1 << 252}


        ''') + ctrcs + (dedent(f'''
        def deploy(*args):
            return {self.visit(ast.contracts[0].idf)}.deploy(os.path.dirname(os.path.realpath(__file__)), *args)


        def connect(address: str):
            return {self.visit(ast.contracts[0].idf)}.connect(os.path.dirname(os.path.realpath(__file__)), address)


        def help():
            members = inspect.getmembers({self.visit(ast.contracts[0].idf)}, inspect.isfunction)
            signatures = [(fname, str(inspect.signature(sig))) for fname, sig in members]
            print('\\n'.join([f'{{fname}}({{sig[5:] if not sig[5:].startswith(",") else sig[7:]}}'
                             for fname, sig in signatures
                             if sig.startswith('(self') and not fname.endswith('_check_proof') and not fname.startswith('_')]))

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
                {PROJECT_DIR_NAME} = project_dir
                {CONN_OBJ_NAME} = Runtime.blockchain()
                {CRYPTO_OBJ_NAME} = Runtime.crypto()
                {KEYSTORE_OBJ_NAME} = Runtime.keystore()
                {PROVER_OBJ_NAME} = Runtime.prover()

                {PRIV_VALUES_NAME}: Dict[str, Union[int, bool, RandomnessValue]] = {{}}
                {STATE_VALUES_NAME}: Dict[str, Union[int, bool, CipherValue, AddressValue]] = {{}}

                {CONTRACT_NAME} = '{ast.idf.name}'
                {CONTRACT_HANDLE} = None

            @property
            def address(self):
                return {CONTRACT_HANDLE}.address

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

            @staticmethod
            def comp_overflow_checked(val: int):
                assert val < {SCALAR_FIELD_COMP_MAX_NAME}, f'Value {{val}} is too large for comparison'
                return val

            def get_state(self, name: str, *indices, count=0, is_encrypted=False, val_constructor: Callable[[Any], Any] = lambda x: x):
                idxvals = ''.join([f'[{{idx}}]' for idx in indices])
                loc = f'{{name}}{{idxvals}}'
                if loc in {STATE_VALUES_NAME}:
                    return {STATE_VALUES_NAME}[loc]
                else:
                    if count == 0:
                        val = val_constructor({CONN_OBJ_NAME}.req_state_var({CONTRACT_HANDLE}, name, *indices))
                    else:
                        val = val_constructor([{CONN_OBJ_NAME}.req_state_var({CONTRACT_HANDLE}, name, *indices, i) for i in range(count)])
                    if is_encrypted:
                        val = CipherValue(val)
                    {STATE_VALUES_NAME}[loc] = val
                    return val

        '''))

    def get_loc_value(self, arr: Identifier, indices: List[str]) -> str:
        if isinstance(arr, HybridArgumentIdf) and arr.is_private and not arr.name.startswith('tmp'):
            return f'{PRIV_VALUES_NAME}["{arr.name}"]'
        else:
            idxvals = ''.join([f'[{idx}]' for idx in indices])
            return f'{self.visit(arr)}{idxvals}'

    def get_rvalue(self, idf: IdentifierExpr, val_type: AnnotatedTypeName, indices: List[str]) -> str:
        if isinstance(idf.target, StateVariableDeclaration):
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
        if isinstance(idf.target, StateVariableDeclaration):
            idxvals = ''.join([f'[{{{idx}}}]' for idx in indices])
            return f"{STATE_VALUES_NAME}[f'{idf.idf.name}{idxvals}']"
        else:
            return self.get_loc_value(idf.idf, indices)

    def visitContractDefinition(self, ast: ContractDefinition):
        constr = self.visit_list(ast.constructor_definitions)
        fcts = self.visit_list(ast.function_definitions)

        return f'class {self.visit(ast.idf)}:\n' \
               f'{self.generate_constructors(ast)}' + \
               (f'{indent(constr)}\n' if constr else '') + \
               (f'{indent(fcts)}\n' if fcts else '')

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        with CircuitContext(self, ast):
            fct = super().visitConstructorOrFunctionDefinition(ast)
            if self.current_circ.requires_verification():
                fct = f'{fct}\n{self.build_proof_check_fct()}'
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
        has_in = self.current_circ.has_in_args
        has_out = self.current_circ.has_out_args

        preamble = f'''\
            {STATE_VALUES_NAME}.clear()
            {PRIV_VALUES_NAME}.clear()

            msg = lambda: None
            msg.sender = {CONN_OBJ_NAME}.my_address
        '''

        in_var_decl = None if has_in else f'{cfg.zk_in_name} = []'

        # Encrypt parameters and add private circuit inputs (plain + randomness)
        enc_param_str = ''
        for arg in self.current_params:
            if arg.original_type is not None and arg.original_type.is_private():
                sname = self.visit(arg.idf)
                enc_param_str += f'{PRIV_VALUES_NAME}["{arg.idf.name}"] = {sname}\n'
                enc_param_str += f'{sname}, {PRIV_VALUES_NAME}["{arg.idf.name}_R"] = {CRYPTO_OBJ_NAME}.enc({sname}, {PK_OBJ_NAME})\n'
        enc_param_comment_str = '\n# Encrypt parameters' if enc_param_str else ''
        enc_param_str = enc_param_str[:-1]

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

        if has_out:
            out_stmts = [Comment()] + Comment.comment_wrap_block('Serialize output values', [
                Identifier(cfg.zk_out_name).decl_var(Array(AnnotatedTypeName.uint_all(), circuit.public_out_array[1]))]
                + [out_idf.serialized_loc.assign(SliceExpr(out_idf.get_loc_expr(), 0, out_idf.t.size_in_uints)) if isinstance(out_idf.t, Array) else \
                   IdentifierExpr(f'{cfg.zk_out_name}[{out_idf.serialized_loc.start}]').assign(out_idf.get_loc_expr().implicitly_converted(TypeName.uint_type())) for out_idf in circuit.output_idfs]
                + [Identifier(f'actual_params.append({cfg.zk_out_name})')])
            out_var_decl = self.visit_list(out_stmts)[:-1]
        else:
            out_var_decl = cfg.zk_out_name + ' = []'

        if circuit.requires_verification():
            generate_proof_str += dedent(f'''
            # Generate proof
            priv_arg_list = [{PRIV_VALUES_NAME}[arg] for arg in [{", ".join([f"'{s}'" for s in circuit.secret_param_names])}]]
            self._{ast.name}_check_proof({cfg.zk_data_var_name}, priv_arg_list)
            proof = {PROVER_OBJ_NAME}.generate_proof({PROJECT_DIR_NAME}, {CONTRACT_NAME}, '{ast.name}', priv_arg_list, {cfg.zk_in_name}, {cfg.zk_out_name})
            actual_params.append(proof)''')

        should_encrypt = ", ".join([str(bool(p.annotated_type.old_priv_text)) for p in self.current_f.parameters])
        if isinstance(ast, ConstructorDefinition):
            invoke_transact_str = f'''
            # Deploy contract
            {STATE_VALUES_NAME}.clear()
            return {CONN_OBJ_NAME}.deploy({PROJECT_DIR_NAME}, {CONTRACT_NAME}, actual_params, [{should_encrypt}])
            '''
        else:
            invoke_transact_str = f'''
            # Invoke public transaction
            {STATE_VALUES_NAME}.clear()
            return {CONN_OBJ_NAME}.transact({CONTRACT_HANDLE}, '{ast.name}', actual_params, [{should_encrypt}])
            '''

        code = '\n'.join(dedent(s) for s in [
            address_wrap_str,
            preamble,
            in_var_decl,
            enc_param_comment_str,
            enc_param_str,
            actual_params_assign_str,
            begin_body_comment_str,
            body_str,
            end_body_comment_str,
            out_var_decl,
            generate_proof_str,
            invoke_transact_str
        ] if s)
        return code

    def build_proof_check_fct(self) -> str:
        circuit = self.current_circ
        pnames = ', '.join([f'{{{cfg.zk_data_var_name}["{p.name}"]}}' for p in circuit.input_idfs + circuit.output_idfs])
        stmts = [f"print(f'Circuit arguments: {{list(map(str, priv_args))}}, {pnames}')"]
        assert_str = 'assert {0} == {1}, f\'check failed for lhs={{{0}}} and rhs={{{1}}}\''

        with CircuitComputation(self):
            for stmt in circuit.phi:
                if isinstance(stmt, TempVarDecl):
                    stmts.append(f'{stmt.lhs.name}: int = {self.visit(stmt.expr.implicitly_converted(TypeName.uint_type()))}')
                elif isinstance(stmt, EncConstraint):
                    cipher_str = self.visit(stmt.cipher.get_loc_expr())
                    enc_str = f'(CipherValue() if {cipher_str} == CipherValue() else {CRYPTO_OBJ_NAME}.enc({self.visit(stmt.plain.get_loc_expr())}, {self.visit(stmt.pk.get_loc_expr())}, {self.visit(stmt.rnd.get_loc_expr())})[0])'
                    stmts.append(assert_str.format(enc_str, cipher_str))
                elif isinstance(stmt, CircAssignment):
                    stmts.append(f'{self.visit(stmt.lhs)} = {self.visit(stmt.rhs)}')
                else:
                    assert isinstance(stmt, EqConstraint)
                    stmts.append(assert_str.format(self.visit(stmt.tgt.get_loc_expr()), self.visit(stmt.val.get_loc_expr())))
        stmts.append('print(\'Proof soundness verified\')')

        params = f'self, {cfg.zk_data_var_name}: Dict, priv_args: List'
        body = '\n'.join(stmts)
        return f'def _{self.current_f.name}_check_proof({params}):\n{indent(body)}\n'

    def handle_stmt(self, ast: Statement, stmt_txt: str):
        if not stmt_txt:
            return None

        in_decrypt = ''
        for in_assign in ast.in_assignments:
            in_idf = in_assign.lhs.member
            assert isinstance(in_idf, HybridArgumentIdf)
            if in_idf.corresponding_priv_expression is not None:
                plain_idf_name = f'{PRIV_VALUES_NAME}["{in_idf.corresponding_priv_expression.idf.name}"]'
                in_decrypt += f'{plain_idf_name}, {PRIV_VALUES_NAME}["{in_idf.name}_R"]' \
                              f' = {CRYPTO_OBJ_NAME}.dec({self.visit(in_idf.get_loc_expr())}, {SK_OBJ_NAME})\n'
                plain_idf = IdentifierExpr(plain_idf_name).as_type(TypeName.uint_type())
                conv = self.visit(plain_idf.implicitly_converted(in_idf.corresponding_priv_expression.idf.t))
                if conv != plain_idf_name:
                    in_decrypt += f'{plain_idf_name} = {conv}\n'
        if in_decrypt:
            in_decrypt = in_decrypt[:-1]

        out_initializations = ''
        for out_idf in ast.out_refs:
            # For each out, simulate corresponding ExpressionToLocAssignment (and encrypt and store rnd if necessary)
            out_val = out_idf.corresponding_priv_expression
            if isinstance(out_val, EncryptionExpression):
                s = f'{self.visit(out_idf.get_loc_expr())}, {PRIV_VALUES_NAME}["{out_idf.name}_R"] = {self.visit(out_val)}'
            else:
                s = f'{self.visit(out_idf.get_loc_expr())} = {self.visit(out_val)}'
            out_initializations += f'\n{s}\n'

        return f'{in_decrypt}{out_initializations}{stmt_txt}'

    def visitLabeledBlock(self, ast: LabeledBlock):
        return None

    def visitEncryptionExpression(self, ast: EncryptionExpression):
        priv_str = 'msg.sender' if isinstance(ast.privacy, MeExpr) else self.visit(ast.privacy.clone())
        plain = self.visit(ast.expr)
        with CircuitComputation(self):
            return f'{CRYPTO_OBJ_NAME}.enc({plain}, {KEYSTORE_OBJ_NAME}.getPk({priv_str}))'

    def visitReturnStatement(self, ast: ReturnStatement):
        return None

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

        if ast.idf.name == 'msg':
            return 'msg'

        if self.current_index:
            indices, t = list(reversed(self.current_index)), self.current_index_t
            self.current_index, self.current_index_t = [], None
            indices = [self.visit(idx) for idx in indices]
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
    def __init__(self, v: PythonOffchainVisitor):
        self.v = v

    def __enter__(self):
        self.v.inside_circuit = True

    def __exit__(self, t, value, traceback):
        self.v.inside_circuit = False
