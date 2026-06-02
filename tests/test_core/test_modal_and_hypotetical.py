import unittest
import z3
from core.logic_parser import Z3ExpressionBuilder

class TestModalLogicEngine(unittest.TestCase):
    def setUp(self):
        self.builder = Z3ExpressionBuilder()
        self.solver = z3.Solver()

    def test_kripke_semantics_world_and_time_injection(self):
        """[Faz 1] N-Ary yüklemlere otonom olarak 'WorldSort' ve 'TimeSort' parametresi enjeksiyonu."""
        expr_str = "Forall([x], Insan(x))"
        z3_ast = self.builder.parse(expr_str)
        ast_str = str(z3_ast)
        self.assertTrue("w_base" in ast_str, "[MODAL ÇÖKÜŞ] Olası Dünyalar (WorldSort) Z3 değişkenine zerk edilemedi.")
        self.assertTrue("t_base" in ast_str, "[MODAL ÇÖKÜŞ] Zaman Düzlemi (TimeSort) Z3 değişkenine zerk edilemedi.")

    def test_temporal_modal_consistency(self):
        """[Faz 1 Red-Teaming] Zeyd aynı dünyada farklı zaman dilimlerinde zıt eylemler yapabilir (SAT), ancak aynı anda yapamaz (UNSAT)."""
        w1 = z3.Const('w1', self.builder.WorldSort)
        t1 = z3.Const('t1', self.builder.TimeSort)
        t2 = z3.Const('t2', self.builder.TimeSort)
        zeyd = z3.Const('Zeyd', self.builder.EntitySort)
        
        Kaim = self.builder.get_or_create_predicate('Kaim', 1)
        Celisik_Kaim = self.builder.get_or_create_predicate('Celisik_Kaim', 1)
        
        # Yatay Dışlama Kuralı (Aynı dünyada ve zamanda hem Kaim hem Celisik_Kaim olunamaz)
        w_var = z3.Const('w_var', self.builder.WorldSort)
        t_var = z3.Const('t_var', self.builder.TimeSort)
        x_var = z3.Const('x_var', self.builder.EntitySort)
        disjoint_axiom = z3.ForAll([w_var, t_var, x_var], 
                                   z3.Not(z3.And(Kaim(w_var, t_var, x_var), Celisik_Kaim(w_var, t_var, x_var))))
        self.solver.add(disjoint_axiom)

        # Senaryo 1: Farklı zamanlarda (t1, t2) zıt eylemler -> SAT beklenir
        self.solver.push()
        self.solver.add(Kaim(w1, t1, zeyd))
        self.solver.add(Celisik_Kaim(w1, t2, zeyd))
        self.assertEqual(self.solver.check(), z3.sat, "Farklı zaman dilimlerinde (t1, t2) tutarlı olan ontolojik durum SAT dönmelidir.")
        self.solver.pop()

        # Senaryo 2: Aynı zamanda (t1) zıt eylemler -> UNSAT (Çelişki) beklenir
        self.solver.push()
        self.solver.add(Kaim(w1, t1, zeyd))
        self.solver.add(Celisik_Kaim(w1, t1, zeyd))
        self.assertEqual(self.solver.check(), z3.unsat, "Aynı zaman diliminde (t1) zıt eylemler araz kuralları gereği anında UNSAT dönmelidir.")
        self.solver.pop()

    def test_inadi_mutually_exclusive_operator(self):
        """[Faz 1.1] İnadi Şartiyye (Hulüvv ve Cem'i Mânia) XOR mantıksal operatörü."""
        expr_str = "Forall([x], Inadi(Fail_Muhtar(x), Mecbur(x)))"
        z3_ast = self.builder.parse(expr_str)
        self.solver.add(z3_ast)
        
        # İnadi (XOR) şartına göre bir varlığın aynı anda hem Fail_Muhtar hem Mecbur olması ontolojik olarak imkansızdır (Müstahil).
        conflict_expr = self.builder.parse("Exists([y], And(Fail_Muhtar(y), Mecbur(y)))")
        self.solver.add(conflict_expr)
        
        result = self.solver.check()
        self.assertEqual(result, z3.unsat, "[ZAFİYET] İnadi Şartiyye (Cem'i Mânia) ihlali Z3 tarafından engellenemedi.")