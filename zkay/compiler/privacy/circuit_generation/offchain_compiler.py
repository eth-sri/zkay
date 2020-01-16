from contextlib import contextmanager
from datetime import datetime
from textwrap import dedent
from typing import Dict, List, Optional

from zkay.compiler.privacy.circuit_generation.circuit_helper import CircuitHelper, HybridArgumentIdf
from zkay.config import cfg
from zkay.zkay_ast.ast import ContractDefinition, SourceUnit, ConstructorOrFunctionDefinition, \
    indent, FunctionCallExpr, IdentifierExpr, BuiltinFunction, \
    StateVariableDeclaration, MemberAccessExpr, IndexExpr, Parameter, TypeName, AnnotatedTypeName, Identifier, \
    ReturnStatement, EncryptionExpression, MeExpr, Expression, LabeledBlock, CipherText, Key, Array, \
    AddressTypeName, StructTypeName, HybridArgType, CircuitInputStatement, AddressPayableTypeName, NumberTypeName, \
    CircuitComputationStatement, VariableDeclarationStatement, LocationExpr, PrimitiveCastExpr, IntTypeName, EnumDefinition, EnumTypeName
from zkay.zkay_ast.visitor.python_visitor import PythonCodeVisitor

PROJECT_DIR_NAME = 'self.project_dir'
PROVER_OBJ_NAME = 'self.prover'
CRYPTO_OBJ_NAME = 'self.crypto'
CONN_OBJ_NAME = 'self.conn'
KEYSTORE_OBJ_NAME = 'self.keystore'
SELF_ADDR = 'self.user_addr'
GET_SK = f'{KEYSTORE_OBJ_NAME}.sk({SELF_ADDR})'
GET_PK = f'{KEYSTORE_OBJ_NAME}.pk({SELF_ADDR})'
PRIV_VALUES_NAME = 'self.current_priv_values'
ALL_PRIV_VALUES_NAME = 'self.all_priv_values'
STATE_VALUES_NAME = 'self.state_values'
CONTRACT_NAME = 'self.contract_name'
CONTRACT_HANDLE = 'self.contract_handle'
GET_STATE = 'self.get_state'
IS_EXTERNAL_CALL = 'self.is_external'

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
        contracts = self.visit_list(ast.contracts)
        is_payable = ast.contracts[0].constructor_definitions and ast.contracts[0].constructor_definitions[0].is_payable
        val_param = ', value=0' if is_payable else ''
        val_arg = ', value=value' if is_payable else ''

        return dedent(f'''\
        ###########################################
        ## THIS CODE WAS GENERATED AUTOMATICALLY ##
        ## Creation Time: {datetime.now().strftime('%H:%M:%S %d-%b-%Y')}   ##
        ###########################################

        import os
        import code
        import inspect
        from enum import Enum
        from typing import Dict, List, Tuple, Optional, Union, Any, Callable

        from zkay import my_logging
        from zkay.transaction.types import CipherValue, AddressValue, RandomnessValue, PublicKeyValue
        from zkay.transaction.offchain import {SCALAR_FIELD_NAME}, ContractSimulator, FunctionCtx, RequireException


        ''') + contracts + (dedent(f'''
        def deploy(*args, user: str = ContractSimulator.my_address().val{val_param}):
            return {self.visit(ast.contracts[0].idf)}.deploy(os.path.dirname(os.path.realpath(__file__)), *args, user=user{val_arg})


        def connect(address: str, *, user: str = ContractSimulator.my_address().val):
            return {self.visit(ast.contracts[0].idf)}.connect(os.path.dirname(os.path.realpath(__file__)), address, user=user)


        def create_dummy_accounts(count: int) -> Tuple:
            return ContractSimulator.create_dummy_accounts(count)


        def help():
            ContractSimulator.help(inspect.getmembers({self.visit(ast.contracts[0].idf)}, inspect.isfunction))


        me = ContractSimulator.my_address().val
        ''') if len(ast.contracts) == 1 else '') + dedent('''
        if __name__ == '__main__':
            log_file = my_logging.get_log_file(filename='transactions', parent_dir="", include_timestamp=True, label=None)
            my_logging.prepare_logger(log_file)
            ContractSimulator.init_key_pair(me)
            code.interact(local=locals())
        ''')

    def generate_constructors(self, ast: ContractDefinition) -> str:
        # Priv values: private function args plaintext, locally decrypted plaintexts, encryption randomness
        # State values: if key not in dict -> pull value from chain on read, otherwise retrieve cached value
        name = self.visit(ast.idf)

        is_payable = ast.constructor_definitions and ast.constructor_definitions[0].is_payable
        val_param = ', value=0' if is_payable else ''
        val_arg = ', value=value' if is_payable else ''

        if not ast.constructor_definitions:
            deploy_cmd = f'c.conn.deploy(project_dir, c.user_addr, \'{ast.idf.name}\', [], []{val_arg})'
        else:
            deploy_cmd = f'c.constructor(*constructor_args{val_arg})'

        return indent(dedent(f'''\
            def __init__(self, project_dir: str, user_addr: AddressValue):
                super().__init__(project_dir, user_addr)
                {CONTRACT_NAME} = '{ast.idf.name}'

            @staticmethod
            def connect(project_dir: str, address: str, *, user: str) -> '{name}':
                c = {name}(project_dir, AddressValue(user))
                c.contract_handle = c.conn.connect(project_dir, '{ast.idf.name}', AddressValue(address))
                return c

            @staticmethod
            def deploy(project_dir: str, *constructor_args, user: str{val_param}) -> '{name}':
                c = {name}(project_dir, AddressValue(user))
                c.contract_handle = {deploy_cmd}
                return c

        '''))

    @staticmethod
    def get_priv_value(idf: str):
        return f'{PRIV_VALUES_NAME}["{idf}"]'

    def get_loc_value(self, arr: Identifier, indices: List[str]) -> str:
        if isinstance(arr, HybridArgumentIdf) and arr.arg_type == HybridArgType.PRIV_CIRCUIT_VAL and not arr.name.startswith('tmp'):
            return self.get_priv_value(arr.name)
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
            is_encrypted = val_type.zkay_type.is_private()
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
            idxvals = ', '.join([f'str({idx})' for idx in indices])
            fstr = '[{}]' * len(indices)
            return f"{STATE_VALUES_NAME}['{idf.idf.name}{fstr}'.format({idxvals})]"
        else:
            return self.get_loc_value(idf.idf, indices)

    def visitContractDefinition(self, ast: ContractDefinition):
        enums = self.visit_list(ast.enum_definitions, '\n\n')
        constr = self.visit_list(ast.constructor_definitions, '\n\n')
        fcts = self.visit_list(ast.function_definitions, '\n\n')
        return f'class {self.visit(ast.idf)}(ContractSimulator):\n' + \
               (f'{indent(enums)}\n\n' if enums else '') + \
               f'{self.generate_constructors(ast)}' + \
               (f'{indent(constr)}\n' if constr else '') + \
               (f'{indent(fcts)}\n' if fcts else '')

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition):
        with self.circuit_ctx(ast):
            return super().visitConstructorOrFunctionDefinition(ast)

    def visitParameter(self, ast: Parameter):
        if ast.original_type is None:
            t = 'Any'
        elif ast.original_type.is_address():
            if ast.parent.can_be_external:
                t = 'str'
            else:
                t = 'AddressValue'
        else:
            t = self.visit(ast.original_type.type_name)
        return f'{self.visit(ast.idf)}: {t}'

    def handle_function_params(self, ast: ConstructorOrFunctionDefinition, params: List[Parameter]):
        param_str = super().handle_function_params(ast, self.current_params)
        if ast.is_payable:
            param_str += ', *, value: int = 0'
        return param_str

    @staticmethod
    def do_if_external(ast: ConstructorOrFunctionDefinition, extern_elems: Optional[List[str]] = None, intern_elems: Optional[List[str]] = None):
        extern_s = ('\n'.join(dedent(s) for s in extern_elems if s) if extern_elems else '').strip()
        intern_s = ('\n'.join(dedent(s) for s in intern_elems if s) if intern_elems else '').strip()
        if ast.can_be_external:
            if extern_s:
                ret = f'if {IS_EXTERNAL_CALL}:\n' + indent(extern_s)
                if intern_s:
                    ret += f'\nelse:\n' + indent(intern_s)
                return ret
            elif intern_s:
                return f'if not {IS_EXTERNAL_CALL}:\n' + indent(intern_s)
        else:
            return intern_s

    def handle_function_body(self, ast: ConstructorOrFunctionDefinition):
        preamble_str = 'msg = self.current_msg\n' \
                       'block = self.current_block\n' \
                       'tx = self.current_tx\n'
        circuit = self.current_circ

        all_params = ', '.join([f'{self.visit(param.idf)}' for param in self.current_params])
        if ast.can_be_external:
            address_params = [self.visit(param.idf) for param in self.current_params if
                              param.original_type.is_address()]
            if address_params:
                assign_addr_str = f"{', '.join(address_params)} = {', '.join([f'AddressValue({p})' for p in address_params])}"
                preamble_str += f'\n{self.do_if_external(ast, [assign_addr_str])}\n'

        if ast.can_be_external and circuit:
            # Encrypt parameters and add private circuit inputs (plain + randomness)
            enc_param_str = ''
            for arg in self.current_params:
                if arg.original_type is not None and arg.original_type.is_private():
                    sname = self.visit(arg.idf)
                    enc_param_str += f'{self.get_priv_value(arg.idf.name)} = {sname}\n'
                    enc_param_str += f'{sname}, {self.get_priv_value(f"{arg.idf.name}_R")} = {CRYPTO_OBJ_NAME}.enc({sname}, {GET_PK})\n'
            enc_param_comment_str = '\n# Encrypt parameters' if enc_param_str else ''
            enc_param_str = enc_param_str[:-1] if enc_param_str else ''

            actual_params_assign_str = f"actual_params = [{all_params}]"

            out_var_decl_str = f'{cfg.zk_out_name}: List[int] = [0 for _ in range({circuit.out_size_trans})]'
            out_var_decl_str += f'\nactual_params.append({cfg.zk_out_name})'

            pre_body_code = self.do_if_external(ast, [
                enc_param_comment_str,
                enc_param_str,
                actual_params_assign_str,
                out_var_decl_str
            ])
        elif ast.can_be_external:
            pre_body_code = f'actual_params = [{all_params}]'
        else:
            pre_body_code = ''

        # Simulate public contract to compute in_values (state variable values are pulled from blockchain if necessary)
        # (out values are also computed when encountered, by locally evaluating and encrypting
        # the corresponding private expressions)
        body_str = self.visit(ast.body).strip()

        out_var_serialize_str = ''
        sec_var_serialize_str = ''
        if circuit is not None:
            for out_idf in circuit.output_idfs:
                out_var_serialize_str += f'\n{self.visit(out_idf.serialized_loc)} = '
                if isinstance(out_idf.t, Array):
                    out_var_serialize_str += f'{self.visit(out_idf.get_loc_expr())}[:]'
                else:
                    out_var_serialize_str += f'[int({self.visit(out_idf.get_loc_expr())})]'
            if out_var_serialize_str:
                out_var_serialize_str = f'\n# Serialize output values{out_var_serialize_str}'
            if circuit.sec_idfs:
                offset = 0
                for sec_idf in circuit.sec_idfs:
                    if isinstance(sec_idf.t, Array):
                        sec_var_serialize_str += f'\n{ALL_PRIV_VALUES_NAME}[self.current_all_index + {offset}:self.current_all_index + {offset + sec_idf.t.size_in_uints}] = {PRIV_VALUES_NAME}.get("{sec_idf.name}", {self.get_default_value(sec_idf.t)})[:]'
                    else:
                        sec_var_serialize_str += f'\n{ALL_PRIV_VALUES_NAME}[self.current_all_index + {offset}] = {PRIV_VALUES_NAME}.get("{sec_idf.name}", {self.get_default_value(sec_idf.t)})'
                    offset += sec_idf.t.size_in_uints

        body_code = '\n'.join(dedent(s) for s in [
            f'\n## BEGIN Simulate body',
            body_str,
            '## END Simulate body',
            out_var_serialize_str,
            sec_var_serialize_str,
        ] if s) + '\n'

        # Add proof to actual argument list (when required)
        generate_proof_str = ''
        if ast.can_be_external and circuit:
            generate_proof_str += '\n'.join(['\n#Generate proof',
                                             f"proof = {PROVER_OBJ_NAME}.generate_proof({PROJECT_DIR_NAME}, {CONTRACT_NAME}, '{ast.name}', {ALL_PRIV_VALUES_NAME}, {cfg.zk_in_name}, {cfg.zk_out_name})",
                                             'actual_params.append(proof)'])

        should_encrypt = ", ".join([str(p.annotated_type.declared_type is not None and p.annotated_type.declared_type.is_private()) for p in self.current_f.parameters])
        if ast.is_constructor:
            invoke_transact_str = f'''
            # Deploy contract
            return {CONN_OBJ_NAME}.deploy({PROJECT_DIR_NAME}, {SELF_ADDR}, {CONTRACT_NAME}, actual_params, [{should_encrypt}]{", value=value" if ast.is_payable else ""})
            '''
        elif circuit or ast.has_side_effects:
            invoke_transact_str = f'''
            # Invoke public transaction
            return {CONN_OBJ_NAME}.transact({CONTRACT_HANDLE}, {SELF_ADDR}, '{ast.name}', actual_params, [{should_encrypt}]{", value=value" if ast.is_payable else ""})
            '''
        elif ast.return_parameters:
            lambda_params = []
            ret_args = []
            for idx, retparam in enumerate(ast.return_parameters):
                t = retparam.annotated_type.type_name
                constr = '{}'
                if isinstance(t, AddressTypeName) or isinstance(t, AddressPayableTypeName):
                    constr = 'AddressValue({})'
                elif isinstance(t, CipherText):
                    constr = 'CipherValue({})'
                elif isinstance(t, Key):
                    constr = 'PublicKeyValue({})'
                lambda_params.append(f'_{idx}')
                ret_args.append(constr.format(f'_{idx}'))
            lambda_str = f'(lambda {", ".join(lambda_params)}: {", ".join(ret_args)})({{}})'

            invoke_transact_str = f'''
            # Call pure/view function and return value
            return {lambda_str.format(f"{CONN_OBJ_NAME}.call({CONTRACT_HANDLE}, {SELF_ADDR}, '{ast.name}', *actual_params)")}
            '''
        else:
            invoke_transact_str = ''

        post_body_code = self.do_if_external(ast, [
            generate_proof_str,
            invoke_transact_str
        ], [f'return {", ".join([f"{cfg.return_var_name}_{idx}" for idx in range(len(ast.return_parameters))])}' if ast.is_function and ast.requires_verification else None])

        code = '\n\n'.join(s.strip() for s in [
            f'assert not {IS_EXTERNAL_CALL}' if not ast.can_be_external else None,
            dedent(preamble_str),
            pre_body_code,
            body_code,
            post_body_code
        ] if s)

        return f'with FunctionCtx(self, {circuit.priv_in_size_trans if circuit else -1}{", value=value" if ast.is_payable else ""}):\n' + indent(code)

    def visitReturnStatement(self, ast: ReturnStatement):
        if not ast.function.requires_verification:
            return self.do_if_external(ast.function, None, [super().visitReturnStatement(ast)])
        else:
            return None

    def visitCircuitInputStatement(self, ast: CircuitInputStatement):
        in_decrypt = ''
        in_idf = ast.lhs.member
        assert isinstance(in_idf, HybridArgumentIdf)
        if in_idf.corresponding_priv_expression is not None:
            plain_idf_name = self.get_priv_value(in_idf.corresponding_priv_expression.idf.name)
            in_decrypt += f'\n{plain_idf_name}, {self.get_priv_value(f"{in_idf.name}_R")}' \
                          f' = {CRYPTO_OBJ_NAME}.dec({self.visit(in_idf.get_loc_expr())}, {GET_SK})'
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
            s = f'{self.visit(out_idf.get_loc_expr())}, {self.get_priv_value(f"{out_idf.name}_R")}'
        else:
            s = f'{self.visit(out_idf.get_loc_expr())}'
        with self.circuit_computation(follow_private=True):
            s = f'{s} = {self.visit(out_val)}'
        out_initializations += f'{s}\n'
        return out_initializations

    def visitLabeledBlock(self, ast: LabeledBlock):
        return None

    def visitEncryptionExpression(self, ast: EncryptionExpression):
        priv_str = 'msg.sender' if isinstance(ast.privacy, MeExpr) else self.visit(ast.privacy.clone())
        plain = self.visit(ast.expr)
        return f'{CRYPTO_OBJ_NAME}.enc({plain}, {KEYSTORE_OBJ_NAME}.getPk({priv_str}))'

    def visitFunctionCallExpr(self, ast: FunctionCallExpr):
        if isinstance(ast.func, BuiltinFunction) and ast.func.is_arithmetic():
            if ast.annotated_type is not None:
                elem_bitwidth = ast.annotated_type.type_name.elem_bitwidth
                if isinstance(ast.annotated_type.type_name, NumberTypeName) and ast.annotated_type.type_name.signed:
                    raise NotImplementedError('TODO signed addition simulation')  # TODO
            else:
                elem_bitwidth = 256
            if self.inside_circuit and elem_bitwidth == 256:
                modulo = SCALAR_FIELD_NAME
            else:
                modulo = f'(1 << {elem_bitwidth})'
            return f'({super().visitFunctionCallExpr(ast)}) % {modulo}'
        elif isinstance(ast.func, BuiltinFunction) and ast.func.is_comp():
            args = [f'self.comp_overflow_checked({self.visit(a)})' for a in ast.args]
            return ast.func.format_string().format(*args)
        elif ast.is_cast:
            return self.handle_cast(ast.args[0], ast.func.target.annotated_type.type_name)
        elif isinstance(ast.func, LocationExpr) and ast.func.target is not None and ast.func.target.requires_verification:
            f = self.visit(ast.func)
            a = self.visit_list(ast.args, ', ')
            return f'self._call({ast.sec_start_offset}, self.{f}, {a})'

        return super().visitFunctionCallExpr(ast)

    def visitPrimitiveCastExpr(self, ast: PrimitiveCastExpr):
        return self.handle_cast(ast.expr, ast.elem_type)

    def handle_cast(self, expr: Expression, t: TypeName):
        if not t.is_primitive_type():
            raise NotImplementedError()
        signed = isinstance(t, IntTypeName)
        enum = self.visit_list(t.target.qualified_name, sep='.') if isinstance(t, EnumTypeName) else None
        num_bits = t.elem_bitwidth
        return f'self.cast({self.visit(expr)}, {num_bits}{f", signed={bool(signed)}" if signed else ""}{f", enum={enum}" if enum is not None else ""})'

    def visitMemberAccessExpr(self, ast: MemberAccessExpr):
        assert not isinstance(ast.target, StateVariableDeclaration), "State member accesses not handled"

        if isinstance(ast.expr.target, EnumDefinition):
            return f'{self.visit_list(ast.expr.target.qualified_name, sep=".")}.{self.visit(ast.member)}'

        if ast.member.name == 'length' and isinstance(ast.expr.target.annotated_type.type_name, Array):
            return f'len({self.visit(ast.expr)})'

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

    def visitVariableDeclarationStatement(self, ast: VariableDeclarationStatement):
        if ast.variable_declaration.idf.name == cfg.zk_data_var_name:
            c = self.circuits[ast.function]
            s = ''
            for idx, val in enumerate(c.internal_zk_data_struct.members):
                s += f"'{val.idf.name}': {self.get_default_value(val.annotated_type.type_name)},"
                s += '\n' if idx % 4 == 3 else ' '
            return f'{cfg.zk_data_var_name}: Dict = {{\n' + indent(s) + '}'
        else:
            return super().visitVariableDeclarationStatement(ast)

    def visitCipherText(self, _):
        return 'CipherValue'

    def visitKey(self, _):
        return 'PublicKeyValue'

    def visitRandomness(self, _):
        return 'RandomnessValue'

    @contextmanager
    def circuit_ctx(self, ast: ConstructorOrFunctionDefinition):
        self.current_f = ast
        self.current_circ = self.circuits.get(ast, None)
        if self.current_circ and self.current_f.can_be_external:
            self.current_params = [p for p in ast.parameters if p.idf.name != cfg.zk_out_name and p.idf.name != cfg.proof_param_name]
        else:
            self.current_params = ast.parameters.copy()
        yield
        self.current_f, self.current_circ, self.current_params = None, None, None

    @contextmanager
    def circuit_computation(self, follow_private: bool = False):
        assert not self.inside_circuit
        self.inside_circuit = True
        old_fp = self.follow_private
        self.follow_private = follow_private
        yield
        assert self.inside_circuit
        self.inside_circuit = False
        self.follow_private = old_fp
