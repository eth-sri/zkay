from typing import Dict, List, Set

from zkay.config import cfg
from zkay.transaction.crypto.params import CryptoParams
from zkay.zkay_ast.ast import AST, AnnotatedTypeName, ConstructorOrFunctionDefinition, EnumDefinition, \
    Expression, IdentifierDeclaration, SourceUnit, StructDefinition
from zkay.zkay_ast.homomorphism import Homomorphism
from zkay.zkay_ast.visitor.visitor import AstVisitor


class UsedHomomorphismsVisitor(AstVisitor):

    def __init__(self):
        super().__init__(traversal='node-or-children')

    def visitChildren(self, ast) -> Set[Homomorphism]:
        all_homs = set()
        for c in ast.children():
            all_homs |= self.visit(c)
        return all_homs

    def visitAnnotatedTypeName(self, ast: AnnotatedTypeName) -> Set[Homomorphism]:
        return {ast.homomorphism} if ast.is_private() else set()

    def visitExpression(self, ast: Expression) -> Set[Homomorphism]:
        if ast.annotated_type is not None and ast.annotated_type.is_private():
            return {ast.annotated_type.homomorphism} | self.visitChildren(ast)
        else:
            return self.visitChildren(ast)

    def visitIdentifierDeclaration(self, ast: IdentifierDeclaration) -> Set[Homomorphism]:
        return self.visitChildren(ast)  # Visits annotated type of identifier (and initial value expression)

    def visitConstructorOrFunctionDefinition(self, ast: ConstructorOrFunctionDefinition) -> Set[Homomorphism]:
        return self.visitChildren(ast)  # Parameter and return types are children; don't bother with 'function type'

    def visitEnumDefinition(self, ast: EnumDefinition):
        return set()  # Neither the enum type nor the types of the enum values can be private

    def visitStructDefinition(self, ast: StructDefinition):
        return self.visitChildren(ast)  # Struct types are never private, but they may have private members

    def visitSourceUnit(self, ast: SourceUnit):
        used_homs = self.visitChildren(ast)
        # Now all constructors or functions have been visited and we can do some post-processing
        # If some function f calls some function g, and g uses crypto-backend c, f also uses crypto-backend c
        # We have to do this for all transitively called functions g, being careful around recursive function calls
        all_fcts = sum([c.constructor_definitions + c.function_definitions for c in ast.contracts], [])
        self.compute_transitive_homomorphisms(all_fcts)
        for f in all_fcts:
            f.used_crypto_backends = self.used_crypto_backends(f.used_homomorphisms)
        return used_homs

    def compute_transitive_homomorphisms(self, fcts: List[ConstructorOrFunctionDefinition]):
        callers: Dict[ConstructorOrFunctionDefinition, List[ConstructorOrFunctionDefinition]] = {}
        for f in fcts:
            callers[f] = []
        for f in fcts:
            for g in f.called_functions:
                if g.used_homomorphisms is None:
                    # Called function not analyzed, (try to) make sure this is a built-in like transfer, send
                    assert not g.requires_verification and not g.body.statements
                    continue
                callers[g].append(f)

        dirty = set(fcts)
        while dirty:
            f = dirty.pop()
            if not f.used_homomorphisms:
                continue

            # Add all of f's used homomorphisms to all of its callers g.
            # If this added a new homomorphism to g, mark g as dirty (if not already).
            for g in callers[f]:
                if f == g:
                    continue
                old_len = len(g.used_homomorphisms)
                g.used_homomorphisms |= f.used_homomorphisms
                if len(g.used_homomorphisms) > old_len:
                    dirty.add(g)

    def visitAST(self, ast: AST) -> Set[Homomorphism]:
        # Base case, make sure we don't miss any annotated types
        if hasattr(ast, 'annotated_type'):
            raise ValueError(f'Unhandled AST element of type {ast.__class__.__name__} with annotated type')
        return self.visitChildren(ast)

    def visit(self, ast):
        all_homs = super().visit(ast)
        if hasattr(ast, 'used_homomorphisms'):
            ast.used_homomorphisms = all_homs
        if hasattr(ast, 'used_crypto_backends'):
            ast.used_crypto_backends = self.used_crypto_backends(all_homs)
        return all_homs

    @staticmethod
    def used_crypto_backends(used_homs: Set[Homomorphism]) -> List[CryptoParams]:
        # Guarantee consistent order
        result = []
        for hom in Homomorphism:
            if hom in used_homs:
                crypto_backend = cfg.get_crypto_params(hom)
                if crypto_backend not in result:
                    result.append(crypto_backend)
        return result
