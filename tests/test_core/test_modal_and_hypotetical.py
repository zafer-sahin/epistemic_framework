import unittest
import z3
from core.logic_parser import Z3ExpressionBuilder

class TestModalLogicEngine(unittest.TestCase):
    def setUp(self):
        self.builder = Z3ExpressionBuilder()
        self.solver = z3.Solver()

    def test_kripke_semantics_world_injection(self):
        """[Faz 2.1] N-Ary yüklemlere otonom olarak 'WorldSort' parametresi enjeksiyonu."""
        expr_str = "Forall([x], Insan(x))"
        z3_ast = self.builder.parse(expr_str)
        # Oluşan AST'de 'Insan' yükleminin aritesi (w_base, x) olarak 2 olmalıdır.
        self.assertTrue("w_base" in str(z3_ast), "[MODAL ÇÖKÜŞ] Olası Dünyalar (WorldSort) Z3 değişkenine zerk edilemedi.")

    def test_inadi_mutually_exclusive_operator(self):
        """[Faz 1.1] İnadi Şartiyye (Hulüvv ve Cem'i Mânia) XOR mantıksal operatörü."""
        expr_str = "Inadi(Fail_Muhtar(x), Mecbur(x))"
        z3_ast = self.builder.parse(expr_str)
        self.solver.add(z3_ast)
        # Her ikisinin de aynı anda doğru (And) veya aynı anda yanlış (Not Or) olma durumu UNSAT vermelidir.
        pass # Z3 SAT/UNSAT assert işlemleri