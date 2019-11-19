import zkay.config as cfg
from zkay.compiler.privacy.circuit_generation.circuit_constraints import CircuitStatement, CircComment, CircIndentBlock, TempVarDecl, \
    CircAssignment, EncConstraint, EqConstraint

from zkay.compiler.privacy.circuit_generation.offchain_compiler import PythonOffchainVisitor, CircuitComputation, CRYPTO_OBJ_NAME
from zkay.zkay_ast.ast import indent, TypeName


class PythonOffchainVisitorWithProofSimulation(PythonOffchainVisitor):
    def call_python_proof_simulator(self, function_name) -> str:
        return f'self._{function_name}_check_proof({cfg.zk_data_var_name}, priv_arg_list)'

    def build_proof_check_fct(self) -> str:
        circuit = self.current_circ
        pnames = ', '.join([f'{{{cfg.zk_data_var_name}["{p.name}"]}}' for p in circuit.input_idfs + circuit.output_idfs])
        stmts = [f"print(f'Circuit arguments: {{list(map(str, priv_args))}}, {pnames}')"]

        stmts += [self.visitCircuitStatement(stmt) for stmt in circuit.phi]

        stmts.append('print(\'Proof soundness verified\')')

        params = f'self, {cfg.zk_data_var_name}: Dict, priv_args: List'
        body = '\n'.join(stmts)
        return f'\ndef _{self.current_f.name}_check_proof({params}):\n{indent(body)}\n'

    def visitCircuitStatement(self, stmt: CircuitStatement):
        __assert_str = 'assert {0} == {1}, f\'check failed for lhs={{{0}}} and rhs={{{1}}}\''
        if isinstance(stmt, CircComment):
            return f'# {stmt.text}' if stmt.text else ''
        elif isinstance(stmt, CircIndentBlock):
            stmts = list(map(self.visitCircuitStatement, stmt.statements))
            return '\n'.join(stmts)
            #return f'## BEGIN {stmt.name} ##\n' + '\n'.join(stmts) + '\n' + f'##  END  {stmt.name} ##'
        elif isinstance(stmt, TempVarDecl):
            with CircuitComputation(self):
                return f'{stmt.lhs.name}: int = {self.visit(stmt.expr.implicitly_converted(TypeName.uint_type()))}'
        elif isinstance(stmt, CircAssignment):
            lhs = self.visit(stmt.lhs)
            with CircuitComputation(self):
                return f'{lhs} = {self.visit(stmt.rhs)}'
        elif isinstance(stmt, EncConstraint):
            cipher_str = self.visit(stmt.cipher.get_loc_expr())
            enc_str = f'(CipherValue() if {cipher_str} == CipherValue() else {CRYPTO_OBJ_NAME}.enc({self.visit(stmt.plain.get_loc_expr())}, {self.visit(stmt.pk.get_loc_expr())}, {self.visit(stmt.rnd.get_loc_expr())})[0])'
            return __assert_str.format(enc_str, cipher_str)
        else:
            assert isinstance(stmt, EqConstraint)
            return __assert_str.format(self.visit(stmt.tgt.get_loc_expr()), self.visit(stmt.val.get_loc_expr()))