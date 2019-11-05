from datetime import datetime
from textwrap import dedent
from typing import Dict, List, Optional

import zkay.config as cfg

from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper, HybridArgumentIdf, \
    ExpressionToLocAssignment, EncConstraint, EqConstraint
from zkay.compiler.privacy.transformer.zkay_transformer import proof_param_name
from zkay.compiler.privacy.used_contract import get_contract_instance_idf
from zkay.compiler.privacy.library_contracts import bn128_scalar_field
from zkay.zkay_ast.ast import ContractDefinition, SourceUnit, ConstructorOrFunctionDefinition, \
    ConstructorDefinition, AssignmentStatement, indent, FunctionCallExpr, IdentifierExpr, BuiltinFunction, \
    StateVariableDeclaration, Statement, MemberAccessExpr, IndexExpr, Parameter, Mapping, Array, TypeName, AnnotatedTypeName, Identifier, \
    ReturnStatement
from zkay.zkay_ast.ast import ElementaryTypeName
from zkay.zkay_ast.visitor.deep_copy import deep_copy
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
        self.current_index: List[str] = []
        self.current_outs: List[HybridArgumentIdf] = []

        self.inside_circuit: bool = False

    def visitElementaryTypeName(self, ast: ElementaryTypeName):
        if ast == TypeName.address_type():
            return 'AddressValue'
        return super().visitElementaryTypeName(ast)

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
        from zkay.transaction import Runtime, CipherValue, AddressValue

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

                {PRIV_VALUES_NAME}: Dict[str, Union[int, bool]] = {{}}
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

            def get_state(self, name: str, *indices, is_encrypted=False, val_constructor: Callable[[Any], Any] = lambda x: x):
                idxvals = ''.join([f'[{{idx}}]' for idx in indices])
                loc = f'{{name}}{{idxvals}}'
                if loc in {STATE_VALUES_NAME}:
                    return {STATE_VALUES_NAME}[loc]
                else:
                    val = val_constructor({CONN_OBJ_NAME}.req_state_var({CONTRACT_HANDLE}, name, *indices))
                    if is_encrypted:
                        val = CipherValue(val)
                    {STATE_VALUES_NAME}[loc] = val
                    return val

        '''))

    @staticmethod
    def get_state_value(idf: Identifier, val_type: AnnotatedTypeName, indices: List[str]) -> str:
        is_encrypted = bool(val_type.old_priv_text)
        name_str = f"'{idf.name}'"
        constr = ''
        if val_type.is_address():
            constr = ', val_constructor=AddressValue'
        val_str = f"{GET_STATE}({', '.join([name_str] + indices)}, is_encrypted={is_encrypted}{constr})"
        return val_str

    @staticmethod
    def set_state_value(idf: Identifier, indices: List[str]):
        idxvals = ''.join([f'[{{{idx}}}]' for idx in indices])
        return f"{STATE_VALUES_NAME}[f'{idf.name}{idxvals}']"

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

        in_var_decl = '' if has_in else f'{cfg.zk_in_name} = []'

        if has_out:
            out_var_decl = f'{cfg.zk_out_name}: List[Optional[Union[int, CipherValue]]] = [None for _ in range({circuit.public_out_array[1]})]'
        else:
            out_var_decl = f'{cfg.zk_out_name} = []'

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
        end_body_comment_str = '## END Simulate body'

        # Add out__, in__ and proof to actual argument list (when required)
        add_pub_arg_str = ''

        if has_out:
            add_pub_arg_str += f'\nactual_params.append({cfg.zk_out_name})\n'
        if circuit.requires_verification():
            add_pub_arg_str += dedent(f'''
            # Generate proof
            priv_arg_list = [{PRIV_VALUES_NAME}[arg] for arg in [{", ".join([f"'{s}'" for s in circuit.secret_param_names])}]]
            self._{ast.name}_check_proof(priv_arg_list, {cfg.zk_in_name}, {cfg.zk_out_name})
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
            out_var_decl,
            enc_param_comment_str,
            enc_param_str,
            actual_params_assign_str,
            begin_body_comment_str,
            body_str,
            end_body_comment_str,
            add_pub_arg_str,
            invoke_transact_str
        ] if s)
        return code

    def build_proof_check_fct(self) -> str:
        circuit = self.current_circ
        stmts = [f"({', '.join(circuit.secret_param_names)}, ) = {'tuple(priv_args)'}",
                 f"print(f'Circuit arguments: {{list(map(str, priv_args + {cfg.zk_in_name} + {cfg.zk_out_name}))}}')"]
        assert_str = 'assert {0} == {1}, f"check failed for lhs={{{0}}} and rhs={{{1}}}"'
        for stmt in circuit.phi:
            if isinstance(stmt, ExpressionToLocAssignment):
                with CircuitComputation(self):
                    stmts.append(f'{stmt.lhs.name}: int = {self.visit(stmt.expr.implicitly_converted(TypeName.uint_type()))}')
            elif isinstance(stmt, EncConstraint):
                cipher_str = self.py.visit(stmt.cipher.get_loc_expr())
                enc_str = f'(CipherValue(0) if {cipher_str}.val == 0 else {CRYPTO_OBJ_NAME}.enc({self.py_plain.visit(stmt.plain.get_loc_expr())}, {self.py.visit(stmt.pk.get_loc_expr())}, {self.py.visit(stmt.rnd.get_loc_expr())})[0])'
                stmts.append(assert_str.format(enc_str, cipher_str))
            else:
                assert isinstance(stmt, EqConstraint)
                stmts.append(assert_str.format(self.py.visit(stmt.tgt.get_loc_expr()), self.py.visit(stmt.val.get_loc_expr())))
        stmts.append('print(\'Proof soundness verified\')')

        params = f'self, priv_args: List, {cfg.zk_in_name}: List, {cfg.zk_out_name}: List'
        body = '\n'.join(stmts)
        return f'def _{self.current_f.name}_check_proof({params}):\n{indent(body)}\n'

    def handle_stmt(self, ast: Statement, stmt_txt: str):
        if not stmt_txt:
            return None

        out_initializations = ''
        for out_idf in self.current_outs:
            # For each out, simulate corresponding ExpressionToLocAssignment (and encrypt and store rnd if necessary)
            out_val = out_idf.corresponding_expression
            loc_str = self.visit(out_idf.get_loc_expr())
            if out_val.privacy.is_all_expr():
                s = f'{loc_str} = int({self.visit(out_val.val)})' # TODO (in the future maybe not uint)
            else:
                priv_str = 'msg.sender' if out_val.privacy.is_me_expr() else f'{self.visit(deep_copy(out_val.privacy))}'
                pk_str = f'{KEYSTORE_OBJ_NAME}.getPk(__addr)'
                with CircuitComputation(self):
                    enc_str = f'{CRYPTO_OBJ_NAME}.enc({self.visit(out_val.val)}, {pk_str})'
                s = f'__addr = {priv_str}\n' \
                    f'{loc_str}, {PRIV_VALUES_NAME}["{out_idf.get_flat_name()}_R"] = {enc_str}'

            out_initializations += f'{s}\n'
        self.current_outs: List[HybridArgumentIdf] = []

        in_decrypt = ''
        if isinstance(ast, AssignmentStatement) and isinstance(ast.lhs, IndexExpr) and isinstance(ast.lhs.arr, IdentifierExpr):
            lhsidf = ast.lhs.arr.idf
            if lhsidf.name == cfg.zk_in_name and lhsidf.corresponding_plaintext_circuit_input is not None:
                assert isinstance(lhsidf, HybridArgumentIdf)
                plain_idf = f'{PRIV_VALUES_NAME}["{lhsidf.corresponding_plaintext_circuit_input.name}"]'
                in_decrypt = f'\n'\
                    f'{plain_idf}, {PRIV_VALUES_NAME}["{lhsidf.get_flat_name()}_R"]'\
                    f' = {CRYPTO_OBJ_NAME}.dec({lhsidf.get_loc_expr().code()}, {SK_OBJ_NAME})'
                ridf = IdentifierExpr(Identifier(plain_idf), AnnotatedTypeName.uint_all())
                conv = self.visit(ridf.implicitly_converted(lhsidf.corresponding_plaintext_circuit_input.t))
                if conv != self.visit(ridf):
                    in_decrypt += f'\n{plain_idf} = {conv}'

        return f'{out_initializations}{stmt_txt}{in_decrypt}'

    def visitReturnStatement(self, ast: ReturnStatement):
        return None

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if self.current_circ.requires_verification() and isinstance(ast.func, MemberAccessExpr) and isinstance(ast.func.expr, IdentifierExpr):
            if ast.func.expr.idf.name == get_contract_instance_idf(self.current_circ.verifier_contract_type.code()).name:
                # Skip call to verifier
                return None
        elif isinstance(ast.func, BuiltinFunction) and ast.func.is_arithmetic():
            modulo = SCALAR_FIELD_NAME if self.inside_circuit else UINT256_MAX_NAME
            return f'({super().visitFunctionCallExpr(ast)}) % {modulo}'
        elif isinstance(ast.func, BuiltinFunction) and ast.func.is_comp():
            args = [f'self.comp_overflow_checked({self.visit(a)})' for a in ast.args]
            return ast.func.format_string().format(*args)

        return super().visitFunctionCallExpr(ast)

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        if ast.statement is not None and ast.idf.name == cfg.zk_out_name:
            assert isinstance(ast.idf, HybridArgumentIdf) and ast.idf.corresponding_expression is not None
            self.current_outs.append(ast.idf)

        if ast.idf.name == f'{cfg.pki_contract_name}_inst' and not ast.is_lvalue():
            return f'{KEYSTORE_OBJ_NAME}'
        elif ast.idf.name == 'msg':
            return 'msg'
        elif isinstance(ast.target, StateVariableDeclaration):
            if ast.is_rvalue():
                return self.get_state_value(ast.idf, ast.target.annotated_type, [])
            else:
                return self.set_state_value(ast.idf, [])
        else:
            return super().visitIdentifierExpr(ast)

    def visitIndexExpr(self, ast: IndexExpr):
        self.current_index.append(self.visit(ast.index))
        if isinstance(ast.arr, IdentifierExpr):
            if ast.is_rvalue() and isinstance(ast.arr.idf, HybridArgumentIdf) and ast.arr.idf.corresponding_plaintext_circuit_input is not None:
                # TODO correct?
                ret = f'{PRIV_VALUES_NAME}["{ast.arr.idf.corresponding_plaintext_circuit_input.name}"]'
            else:
                self.current_index = list(reversed(self.current_index))
                if isinstance(ast.arr.target, StateVariableDeclaration):
                    if ast.is_rvalue():
                        map_t = ast.arr.target.annotated_type
                        idx = 0
                        while idx < len(self.current_index):
                            t = map_t.type_name
                            assert isinstance(t, Mapping) or isinstance(t, Array)
                            map_t = t.value_type
                            idx += 1

                        ret = self.get_state_value(ast.arr.idf, map_t, self.current_index)
                    else:
                        ret = self.set_state_value(ast.arr.idf, self.current_index)
                else:
                    if len(self.current_index) > 1:
                        ret = ''
                    else:
                        ret = super().visitIndexExpr(ast)
            self.current_index = []
            return ret
        else:
            assert isinstance(ast.arr, IndexExpr)
            ret = self.visitIndexExpr(ast.arr)
            if ret:
                return ret
            else:
                return super().visitIndexExpr(ast)


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
