import unittest
import z3
from core.logic_parser import Z3ExpressionBuilder

class TestModalLogicEngine(unittest.TestCase):
    def setUp(self):
        self.builder = Z3ExpressionBuilder()
        self.solver = z3.Solver()

    def test_kripke_semantics_world_and_time_injection(self):
        """[Faz 4] N-Ary yüklemlere otonom olarak 'WorldSort', 'TimeSortZati' ve 'TimeSortVasfi' parametresi enjeksiyonu."""
        expr_str = "Forall([x], Insan(x))"
        z3_ast = self.builder.parse(expr_str)
        ast_str = str(z3_ast)
        self.assertTrue("w_base" in ast_str, "[MODAL ÇÖKÜŞ] Olası Dünyalar (WorldSort) Z3 değişkenine zerk edilemedi.")
        self.assertTrue("t_zati_base" in ast_str, "[MODAL ÇÖKÜŞ] Zâtî Zaman Düzlemi (TimeSortZati) Z3 değişkenine zerk edilemedi.")
        self.assertTrue("t_vasfi_base" in ast_str, "[MODAL ÇÖKÜŞ] Vasfî Zaman Düzlemi (TimeSortVasfi) Z3 değişkenine zerk edilemedi.")

    def test_temporal_modal_consistency(self):
        """[Faz 4 Red-Teaming] Zeyd aynı dünyada ve zâtî zamanda, farklı vasfî zaman dilimlerinde zıt eylemler yapabilir (SAT), ancak aynı vasfî anda yapamaz (UNSAT)."""
        w1 = z3.Const('w1', self.builder.WorldSort)
        tz1 = z3.Const('tz1', self.builder.TimeSortZati)
        tv1 = z3.Const('tv1', self.builder.TimeSortVasfi)
        tv2 = z3.Const('tv2', self.builder.TimeSortVasfi)
        zeyd = z3.Const('Zeyd', self.builder.EntitySort)
        
        Kaim = self.builder.get_or_create_predicate('Kaim', 1)
        Celisik_Kaim = self.builder.get_or_create_predicate('Celisik_Kaim', 1)
        
        # Yatay Dışlama Kuralı (Aynı dünyada, aynı zâtî ve vasfî zamanda hem Kaim hem Celisik_Kaim olunamaz)
        w_var = z3.Const('w_var', self.builder.WorldSort)
        tz_var = z3.Const('tz_var', self.builder.TimeSortZati)
        tv_var = z3.Const('tv_var', self.builder.TimeSortVasfi)
        x_var = z3.Const('x_var', self.builder.EntitySort)
        
        disjoint_axiom = z3.ForAll([w_var, tz_var, tv_var, x_var], 
                                   z3.Not(z3.And(Kaim(w_var, tz_var, tv_var, x_var), Celisik_Kaim(w_var, tz_var, tv_var, x_var))))
        self.solver.add(disjoint_axiom)

        # Senaryo 1: Farklı vasfî zamanlarda (tv1, tv2) zıt arazlar -> SAT beklenir
        self.solver.push()
        self.solver.add(Kaim(w1, tz1, tv1, zeyd))
        self.solver.add(Celisik_Kaim(w1, tz1, tv2, zeyd))
        self.assertEqual(self.solver.check(), z3.sat, "Farklı vasfî zaman dilimlerinde (tv1, tv2) tutarlı olan ontolojik durum SAT dönmelidir.")
        self.solver.pop()

        # Senaryo 2: Aynı vasfî zamanda (tv1) zıt arazlar -> UNSAT (Çelişki) beklenir
        self.solver.push()
        self.solver.add(Kaim(w1, tz1, tv1, zeyd))
        self.solver.add(Celisik_Kaim(w1, tz1, tv1, zeyd))
        self.assertEqual(self.solver.check(), z3.unsat, "Aynı vasfî zaman diliminde (tv1) zıt eylemler araz kuralları gereği anında UNSAT dönmelidir.")
        self.solver.pop()

    def test_inadi_mutually_exclusive_operator(self):
        """[Faz 1.1] İnadi Şartiyye (Hulüvv ve Cem'i Mânia) XOR mantıksal operatörü."""
        expr_str = "Forall([x], Inadi(Fail_Muhtar(x), Mecbur(x)))"
        z3_ast = self.builder.parse(expr_str)
        self.solver.add(z3_ast)
        
        conflict_expr = self.builder.parse("Exists([y], And(Fail_Muhtar(y), Mecbur(y)))")
        self.solver.add(conflict_expr)
        
        result = self.solver.check()
        self.assertEqual(result, z3.unsat, "[ZAFİYET] İnadi Şartiyye (Cem'i Mânia) ihlali Z3 tarafından engellenemedi.")