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
        # [DÜZELTME]: 'x' değişkeni Forall niceleyicisi (Quantifier) ile scope içine alınarak bağlı değişken (Bound Variable) yapıldı.
        expr_str = "Forall([x], Inadi(Fail_Muhtar(x), Mecbur(x)))"
        z3_ast = self.builder.parse(expr_str)
        self.solver.add(z3_ast)
        
        # [Z3 ASSERTION]: İnadi (XOR) şartına göre bir varlığın aynı anda hem Fail_Muhtar hem Mecbur olması 
        # (Zıtların Cem'i) ontolojik olarak imkansızdır (Müstahil).
        conflict_expr = self.builder.parse("Exists([y], And(Fail_Muhtar(y), Mecbur(y)))")
        self.solver.add(conflict_expr)
        
        # Testin UNSAT dönmesi, Z3 motorunun İnadi (XOR) operatörünü başarılı şekilde işlediğini kanıtlar.
        result = self.solver.check()
        self.assertEqual(result, z3.unsat, "[ZAFİYET] İnadi Şartiyye (Cem'i Mânia) ihlali Z3 tarafından engellenemedi.")

if __name__ == '__main__':
    unittest.main()