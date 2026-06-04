import unittest
import z3
from pathlib import Path

from core.models import OntologyLoader, EpistemicEntity, TermModel
from core.logic_engine import AristotelianSolver
from core.layer3_smt import Layer3SMTCircuitBreaker
from linguistics.sarf_parser import SarfEngine
from linguistics.tokenizer import EpistemicTokenizer
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister
from linguistics.ilm_wad_adapter import IlmWadAdapter

class TestVazNeviPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        loader = OntologyLoader()
        cls.ontology = loader.load(Path("data/base_ontology.json"))
        
    def setUp(self):
        self.tokenizer = EpistemicTokenizer()
        self.sarf = SarfEngine()
        self.nahiv = NahivDependencyCompiler()
        self.lexicon = ContextualLexicon()
        self.discourse = DiscourseRegister()
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)
        
        self.solver = AristotelianSolver(self.ontology)
        self.l3 = Layer3SMTCircuitBreaker(self.solver, timeout_ms=3000)

        # [FAZ 1] Epoch parametresi ile senkronizasyon
        self.lexicon.register_word("Zeyd", "Base", "Zeyd_Entity", epoch="Classical")
        self.lexicon.register_word("drb", "Base", "Kavram_Vuran", epoch="Classical")

    def test_sarf_thematic_role_extraction(self):
        morph_data = self.sarf._derive_morphology("daribun")
        self.assertEqual(morph_data.pattern, "Fâ'ilun", "[SENTAKS İHLALİ] Vezin tespiti hatalı.")
        self.assertEqual(morph_data.thematic_role, "Agent", "[SEMANTİK ÇÖKÜŞ] Vaz' Nev'î (Kalıpsal Rol) çıkartılamadı.")

    def test_ilm_wad_ir_injection(self):
        tokens = ["zeydun", "daribun"]
        morph_lexicon = self.sarf.derive_lexicon(tokens)
        dependencies = self.nahiv.suggest_dependencies(tokens, morph_lexicon)
        
        ir_matrix = self.adapter.generate_ir(tokens, dependencies, "Base", morph_lexicon, epoch="Classical")
        
        has_agent_role = any(
            isinstance(pred, tuple) and pred[0] == "Role_Agent" and pred[1] == "Kavram_Vuran" 
            for pred in ir_matrix.predicates
        )
        self.assertTrue(has_agent_role, "[BELLEK HATASI] Role_Agent yüklemi IR matrisine zerk edilemedi.")

    def test_z3_structural_entailment_axiom(self):
        tokens = ["zeydun", "daribun"]
        morph_lexicon = self.sarf.derive_lexicon(tokens)
        dependencies = self.nahiv.suggest_dependencies(tokens, morph_lexicon)
        ir_matrix = self.adapter.generate_ir(tokens, dependencies, "Base", morph_lexicon, epoch="Classical")

        self.l3.core_solver.solver.push()
        try:
            self.l3._inject_structural_axioms()
            
            w_base = z3.Const('w_base', self.l3.core_solver.builder.WorldSort)
            tz_base = z3.Const('tz_base', self.l3.core_solver.builder.TimeSortZati)
            tv_base = z3.Const('tv_base', self.l3.core_solver.builder.TimeSortVasfi)
            
            for item in ir_matrix.predicates:
                self.l3.core_solver.solver.add(self.l3._build_z3_expr(item, w_base, tz_base, tv_base))
            
            self.assertEqual(self.l3.core_solver.solver.check(), z3.sat)

            y_var = z3.Const('y_var', self.l3.core_solver.builder.EntitySort)
            role_action = self.l3.core_solver.builder.get_or_create_predicate("Role_Action", arity=1)
            
            no_action_axiom = z3.ForAll([w_base, tz_base, tv_base, y_var], z3.Not(role_action(w_base, tz_base, tv_base, y_var)))
            self.l3.core_solver.solver.add(no_action_axiom)

            result = self.l3.core_solver.solver.check()
            self.assertEqual(
                result, 
                z3.unsat, 
                "[KRİTİK ZAFİYET] Z3 motoru, failin (Agent) olduğu bir evrende eylemin (Action) yokluğunu onayladı. Mülâzama koptu."
            )
        finally:
            self.l3.core_solver.solver.pop()

if __name__ == '__main__':
    unittest.main()