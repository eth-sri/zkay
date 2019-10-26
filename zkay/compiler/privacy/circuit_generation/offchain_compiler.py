from datetime import datetime
from textwrap import dedent
from typing import Dict, List, Optional

from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper, HybridArgumentIdf
from zkay.compiler.privacy.transformer.zkay_transformer import pki_contract_name, proof_param_name
from zkay.zkay_ast.ast import ContractDefinition, SourceUnit, ConstructorOrFunctionDefinition, \
    ConstructorDefinition, AssignmentStatement, indent, FunctionCallExpr, IdentifierExpr, \
    StateVariableDeclaration, Statement, MemberAccessExpr, IndexExpr, Parameter, Mapping, Array, TypeName
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


class PythonOffchainVisitor(PythonCodeVisitor):
    def __init__(self, circuits: List[CircuitHelper]):
        super().__init__(False)
        self.circuits: Dict[ConstructorOrFunctionDefinition, CircuitHelper] = {cg.fct: cg for cg in circuits}

        self.current_f: Optional[ConstructorOrFunctionDefinition] = None
        self.current_params: Optional[List[Parameter]] = None
        self.current_circ: Optional[CircuitHelper] = None
        self.current_index: List[str] = []
        self.current_outs: List[HybridArgumentIdf] = []

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
        from typing import Dict, List, Optional, Union, Any
        from zkay.transaction import Runtime, CipherValue, AddressValue


        ''') + ctrcs + (dedent(f'''
        def deploy(*args):
            return {self.visit(ast.contracts[0].idf)}.deploy(os.path.dirname(os.path.realpath(__file__)), *args)


        def help():
            print('\\n'.join([f"{{f[0]}}{{inspect.signature(f[1])}}" for f in inspect.getmembers({self.visit(ast.contracts[0].idf)}, inspect.isfunction)]))

        ''') if len(ast.contracts) == 1 else '') + dedent('''
        if __name__ == '__main__':
            code.interact(local=locals())
        ''')

    def generate_constructors(self, ast: ContractDefinition) -> str:
        # Priv values: private function args plaintext, locally decrypted plaintexts, encryption randomness
        # State values: if key not in dict -> pull value from chain on read, otherwise retrieve cached value
        name = self.visit(ast.idf)

        if not ast.constructor_definitions:
            deploy_cmd = f'c.conn.deploy(project_dir, {ast.idf.name}, [], [])'
        else:
            deploy_cmd = f'c.constructor(*constructor_args, *[str(vc.val) for vc in c.conn.pki_verifier_addresses(project_dir)])'

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

            @staticmethod
            def connect(project_dir: str, address: str) -> '{name}':
                c = {name}(project_dir)
                # TODO connect
                return c

            @staticmethod
            def deploy(project_dir: str, *constructor_args) -> '{name}':
                c = {name}(project_dir)
                c.contract_handle = {deploy_cmd}
                return c

            def get_state(self, name: str, *indices):
                return {CONN_OBJ_NAME}.req_state_var({CONTRACT_HANDLE}, name, False, *indices)

        '''))

    def visitContractDefinition(self, ast: ContractDefinition):
        constr = self.visit_list(ast.constructor_definitions)
        fcts = self.visit_list(ast.function_definitions)

        return f'class {self.visit(ast.idf)}:\n' \
               f'{self.generate_constructors(ast)}' \
               f'{indent(constr)}\n' \
               f'{indent(fcts)}\n'

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        with CircuitContext(self, ast):
            return super().visitConstructorOrFunctionDefinition(ast)

    def visitParameter(self, ast: Parameter):
        t = 'Any' if ast.original_type is None else self.visit(ast.original_type.type_name)
        return f'{self.visit(ast.idf)}: {t}'

    def handle_function_params(self, params: List[Parameter]):
        return super().handle_function_params(self.current_params)

    def handle_function_body(self, ast: ConstructorOrFunctionDefinition):
        circuit = self.current_circ
        all_params = ', '.join([f'{self.visit(param.idf)}' for param in self.current_params])
        has_in = self.current_circ.in_name_factory.count > 0
        has_out = self.current_circ.out_name_factory.count > 0

        preamble = f'''\
            {STATE_VALUES_NAME}.clear()
            {PRIV_VALUES_NAME}.clear()

            msg = lambda: None
            msg.sender = {CONN_OBJ_NAME}.my_address
        '''

        in_var_decl = '' if has_in else f'{CircuitHelper.in_base_name} = None'

        if has_out:
            out_var_decl = f'{CircuitHelper.out_base_name}: List[Optional[Union[int, CipherValue]]] = [None for _ in range({circuit.out_name_factory.count})]'
        else:
            out_var_decl = f'{CircuitHelper.out_base_name} = None'

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
            add_pub_arg_str += f'\nactual_params.append({CircuitHelper.out_base_name})\n'
        if circuit.requires_verification():
            add_pub_arg_str += dedent(f'''
            # Generate proof
            priv_arg_list = [{PRIV_VALUES_NAME}[arg] for arg in [{", ".join([f"'{s.name}'" for s in circuit.s])}]]
            proof = {PROVER_OBJ_NAME}.generate_proof({PROJECT_DIR_NAME}, {CONTRACT_NAME}, '{ast.name}', priv_arg_list, {CircuitHelper.in_base_name}, {CircuitHelper.out_base_name})
            actual_params.append(proof)''')

        should_encrypt = ", ".join([str(bool(p.annotated_type.old_priv_text)) for p in self.current_f.parameters])
        if isinstance(ast, ConstructorDefinition):
            invoke_transact_str = f'''
            # Deploy contract
            return {CONN_OBJ_NAME}.deploy({PROJECT_DIR_NAME}, {CONTRACT_NAME}, actual_params, [{should_encrypt}])
            '''
        else:
            invoke_transact_str = f'''
            # Invoke public transaction
            return {CONN_OBJ_NAME}.transact({CONTRACT_HANDLE}, '{ast.name}', actual_params, [{should_encrypt}])
            '''

        # TODO simulate proof circuit for debugging (so we can check locally if / where the circuit fails)
        code = '\n'.join(dedent(s) for s in filter(bool, [
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
        ]))
        return code

    def handle_stmt(self, ast: Statement, stmt_txt: str):
        if not stmt_txt:
            return None

        out_initializations = ''
        for out_idf in self.current_outs:
            # For each out, simulate corresponding ExpressionToLocAssignment (and encrypt and store rnd if necessary)
            out_val = out_idf.corresponding_expression
            loc_str = self.visit(out_idf.get_loc_expr())
            if out_val.privacy.is_all_expr():
                s = f'{loc_str} = {self.visit(out_val.val)}'
            else:
                priv_str = 'msg.sender' if out_val.privacy.is_me_expr() else f'{self.visit(deep_copy(out_val.privacy))}'
                pk_str = f'{KEYSTORE_OBJ_NAME}.getPk({priv_str})'
                enc_str = f'{CRYPTO_OBJ_NAME}.enc({self.visit(out_val.val)}, {pk_str})'
                s = f'{loc_str}, {PRIV_VALUES_NAME}["{out_idf.get_flat_name()}_R"] = {enc_str}'

            out_initializations += f'{s}\n'
        self.current_outs: List[HybridArgumentIdf] = []

        in_decrypt = ''
        if isinstance(ast, AssignmentStatement) and isinstance(ast.lhs, IndexExpr) and isinstance(ast.lhs.arr, IdentifierExpr):
            lhsidf = ast.lhs.arr.idf
            if lhsidf.name == CircuitHelper.in_base_name and lhsidf.corresponding_plaintext_circuit_input is not None:
                in_decrypt = f'\n'\
                    f'{PRIV_VALUES_NAME}["{lhsidf.corresponding_plaintext_circuit_input.name}"], {PRIV_VALUES_NAME}["{lhsidf.get_flat_name()}_R"]'\
                    f' = {CRYPTO_OBJ_NAME}.dec({lhsidf.get_loc_expr().code()}, {SK_OBJ_NAME})'

        return f'{out_initializations}{stmt_txt}{in_decrypt}'

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if self.current_circ.verifier_contract is not None and \
                isinstance(ast.func, MemberAccessExpr) and isinstance(ast.func.expr, IdentifierExpr) and \
                ast.func.expr.idf.name == self.current_circ.verifier_contract.state_variable_idf.name:
            # Skip call to verifier
            return None
        else:
            return super().visitFunctionCallExpr(ast)

    def visitIdentifierExpr(self, ast: IdentifierExpr):
        if ast.statement is not None and ast.idf.name == CircuitHelper.out_base_name:
            assert isinstance(ast.idf, HybridArgumentIdf) and ast.idf.corresponding_expression is not None
            self.current_outs.append(ast.idf)

        if ast.idf.name == f'{pki_contract_name}_inst' and not ast.is_lvalue():
            return f'{KEYSTORE_OBJ_NAME}'
        elif ast.idf.name == 'msg':
            return 'msg'
        elif isinstance(ast.target, StateVariableDeclaration):
            if ast.is_rvalue():
                t = ast.target.annotated_type
                is_encrypted = bool(t.old_priv_text)
                req = f'{CONN_OBJ_NAME}.req_state_var({CONTRACT_HANDLE}, "{ast.idf.name}", {is_encrypted})'
                if t.type_name == TypeName.address_type() or t.type_name == TypeName.address_payable_type():
                    req = f'AddressValue({req})'
                return f'{STATE_VALUES_NAME}.get("{ast.idf.name}", {req})'
            else:
                return f'{STATE_VALUES_NAME}["{ast.idf.name}"]'
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
                idxvals = ''.join([f'[{{{idx}}}]' for idx in self.current_index])
                if isinstance(ast.arr.target, StateVariableDeclaration):
                    if ast.is_rvalue():
                        map_t = ast.arr.target.annotated_type
                        idx = 0
                        while idx < len(self.current_index):
                            t = map_t.type_name
                            assert isinstance(t, Mapping) or isinstance(t, Array)
                            map_t = t.value_type
                            idx += 1

                        is_encrypted = bool(map_t.old_priv_text)
                        req = f'{CONN_OBJ_NAME}.req_state_var({CONTRACT_HANDLE}, "{ast.arr.idf.name}", {is_encrypted}, {", ".join(self.current_index)})'
                        if map_t.type_name == TypeName.address_type() or map_t.type_name == TypeName.address_payable_type():
                            req = f'AddressValue({req})'
                        ret = f'{STATE_VALUES_NAME}.get(f"{ast.arr.idf.name}{idxvals}", {req})'
                    else:
                        ret = f'{STATE_VALUES_NAME}[f"{ast.arr.idf.name}{idxvals}"]'
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
        self.v.current_params = [p for p in self.f.parameters if p.idf.name != CircuitHelper.out_base_name and p.idf.name != proof_param_name]

    def __exit__(self, t, value, traceback):
        self.v.current_f = None
        self.v.current_circ = None
        self.v.current_params = None
