import unittest
import z3
import networkx as nx
from linguistics.discourse_state import DiscourseRegister, DenialLevel
from core.exceptions import ContextPoisoningError
from core.models import BaseOntology, EpistemicEntity, PorphyrianTree, TermModel
from core.logic_engine import AristotelianSolver
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.sarf_parser import MorphologicalAnalysis
from core.layer3_smt import Layer3SMTCircuitBreaker
from linguistics.ilm_wad_adapter import SemanticStatementIR, NestedPredicate

class TestTemporalModalIsolation(unittest.TestCase):
    def setUp(self):
        # Ontoloji ve SMT Çözücü Hazırlığı
        self.ontology = BaseOntology(
            Logical_Components={
                "Terms": {
                    "S": { "symbol": "S", "ar": "el-Haddü'l-Asgar" },
                    "P": { "symbol": "P", "ar": "el-Haddü'l-Ekber" },
                    "M": { "symbol": "M", "ar": "el-Haddü'l-Evsat" },
                    "A": { "symbol": "A", "ar": "el-Mukaddem" },
                    "C": { "symbol": "C", "ar": "et-Tâli" },
                    "B": { "symbol": "B", "ar": "el-Alternatif" }
                },
                "Premises": {
                    "Major": { "ar": "el-Mukaddimetü'l-Kübrâ" },
                    "Minor": { "ar": "el-Mukaddimetü'l-Suğrâ" },
                    "Conclusion": { "ar": "en-Netîce" }
                }
            },
            Syllogism_Moods={},
            Porphyrian_Tree=PorphyrianTree(
                roots={
                    "Base": EpistemicEntity(
                        ontologic_id="Mawjud",
                        terms={"ar": "Mawjud"},
                        modal_status="Mumkin",
                        children=[
                            EpistemicEntity(
                                ontologic_id="Wajib_al_Wujud",
                                terms={"ar": "Allah"},
                                modal_status="Wajib",
                                children=[]
                            ),
                            EpistemicEntity(
                                ontologic_id="Mumkin_al_Wujud",
                                terms={"ar": "Mahlukat"},
                                modal_status="Mumkin",
                                children=[]
                            )
                        ]
                    ),
                    "Secular": EpistemicEntity(
                        ontologic_id="Material_Entity",
                        terms={"ar": "Nature"},
                        modal_status="Mumkin",
                        children=[]
                    )
                }
            )
        )
        self.solver = AristotelianSolver(self.ontology, active_namespace="Base")
        self.nahiv = NahivDependencyCompiler()
        self.register = DiscourseRegister()

    def test_context_sealing_and_poisoning(self):
        """Söylem Belleğinde (DiscourseRegister) Mu'aradah Çapraz İzolasyon Testi"""
        self.register.set_agent("Mujib")
        self.register.add_mention(word="Allah", ontologic_id="Wajib_al_Wujud", active_namespace="Base")
        
        self.register.set_agent("Sail")
        self.register.add_mention(word="Nature", ontologic_id="Material_Entity", active_namespace="Secular")
        
        with self.assertRaises(ContextPoisoningError) as context:
            self.register.resolve_pronoun("huve", enforcement_namespace="Base")
            
        self.assertIn("LOGIC_FAILURE_PROBABILITY: HIGH - Context Poisoning", str(context.exception))
        
    def test_kalamic_causality_axiom(self):
        """Mümkün Varlığın, aynı Kripke dünyasında bir Zorunlu Varlığa bağlanma zorunluluğunun (SAT) testi"""
        w_test = z3.Const('w_test', self.solver.builder.WorldSort)
        tz_test = z3.Const('tz_test', self.solver.builder.TimeSortZati)
        tv_test = z3.Const('tv_test', self.solver.builder.TimeSortVasfi)
        
        mumkin_pred = self.solver.builder.get_or_create_predicate("Mumkin_al_Wujud", arity=1)
        wajib_pred = self.solver.builder.get_or_create_predicate("Wajib_al_Wujud", arity=1)
        x_obj = z3.Const('x_obj', self.solver.builder.EntitySort)
        
        self.solver.solver.push()
        self.solver.solver.add(mumkin_pred(w_test, tz_test, tv_test, x_obj))
        
        y_obj = z3.Const('y_obj', self.solver.builder.EntitySort)
        self.solver.solver.add(z3.ForAll([y_obj], z3.Not(wajib_pred(w_test, tz_test, tv_test, y_obj))))
        
        result, _ = self.solver.check_consistency()
        self.assertFalse(result, "[MANTIK ÇÖKÜŞÜ] Kelâmî Nedensellik (Kalamic Causality) Kripke dünyasında korunamadı. Mümkün varlık, Zorunlu varlık olmadan SAT döndürdü.")
        self.solver.solver.pop()

    def test_nahiv_temporal_trigger_extraction(self):
        """Nahiv AST üzerinden Vasfî Zaman (Meşrûta-i Âmme) tetikleyicisi 'Rel_Hal' bağımlılığının tespiti"""
        tokens = ["jaa", "zeydun", "rakiban"]
        lexicon = {
            "jaa": MorphologicalAnalysis(original_word="jaa", root="cyy", pattern="faala", ontologic_type="Fiil", thematic_role="Action"),
            "zeydun": MorphologicalAnalysis(original_word="zeydun", root="zyd", pattern="faal", ontologic_type="Ism", thematic_role="Agent"),
            "rakiban": MorphologicalAnalysis(original_word="rakiban", root="rkb", pattern="fail", ontologic_type="Ism", thematic_role="Patient")
        }
        
        deps = self.nahiv.suggest_dependencies(tokens, lexicon)
        ast_graph = self.nahiv.build_ast(tokens, deps)
        
        conditions = self.nahiv.extract_temporal_conditions(ast_graph)
        
        self.assertIn("zeydun", conditions)
        self.assertEqual(conditions["zeydun"], "rakiban", "[SÖZDİZİM İHLALİ] Vasfî zaman tetikleyicisi (Rel_Hal) Nahiv AST ağacından doğru şekilde izole edilemedi.")

    def test_layer3_deontic_time_lock(self):
        """Fıkhî (Deontik) kipliklerin sadece Vasfî Zamana kilitlenmesi (TimeSortVasfi) ve varoluşsal yokluk testleri"""
        l3_breaker = Layer3SMTCircuitBreaker(self.solver)
        
        ir_matrix = SemanticStatementIR(
            active_namespace="Base",
            is_valid_for_z3=True,
            predicates=[
                NestedPredicate(
                    operator="Haram_Fiqh",
                    args=[("Zina", "x_actor", 1)]
                )
            ]
        )
        
        # execute_sat_check Z3 state'ini push/pop ile temizlediği için burada sadece matrisin kendi tutarlılığı ölçülür.
        result = l3_breaker.execute_sat_check(ir_matrix)
        self.assertEqual(result["status"], "SAT", "[Z3 SMT ÇÖKÜŞÜ] Deontik (Haram_Fiqh) matrisi Kripke uzayında çözümlenemedi.")
        
        self.solver.solver.push()
        zina_pred = self.solver.builder.get_or_create_predicate("Zina", arity=1)
        w_viol = z3.Const('w_vaz', self.solver.builder.WorldSort)
        tz_viol = z3.Const('tz_vaz', self.solver.builder.TimeSortZati)
        tv_viol = z3.Const('tv_vaz', self.solver.builder.TimeSortVasfi)
        x_viol = z3.Const('x_viol', self.solver.builder.EntitySort)
        
        # Sızıntı testini simüle etmek için Haram kuralı izole test state'ine (push block) tekrar zerk edilmelidir.
        haram_constraint = l3_breaker._build_z3_expr(
            NestedPredicate(operator="Haram_Fiqh", args=[("Zina", "x_viol", 1)]), 
            w_viol, tz_viol, tv_viol
        )
        self.solver.solver.add(haram_constraint)
        
        # Kural devredeyken vasfî zamanda eylemin gerçekleştiği iddia ediliyor.
        self.solver.solver.add(zina_pred(w_viol, tz_viol, tv_viol, x_viol))
        
        final_result = self.solver.solver.check()
        self.assertEqual(final_result, z3.unsat, "[ONTOLOJİK SIZINTI] Haram (Nehiy) kılınmış eylemin Vasfî Zamanda vuku bulması Z3 motoru tarafından engellenemedi.")
        self.solver.solver.pop()

if __name__ == '__main__':
    unittest.main()