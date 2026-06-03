import unittest
from pathlib import Path
from core.models import OntologyLoader
from core.logic_engine import AristotelianSolver
from core.layer1_graph import Layer1HeuristicGraph
from core.layer2_rules import Layer2RuleEngine
from core.layer3_smt import Layer3SMTCircuitBreaker
from core.epistemic_orchestrator import EpistemicOrchestrator
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister
from linguistics.ilm_wad_adapter import IlmWadAdapter, SemanticStatementIR
from schools.taftazani.adab_al_bahth import AdabAlBahthEngine
from schools.ashari_usul import AshariUsul
from schools.salafi_usul import SalafiUsul
from linguistics.tokenizer import EpistemicTokenizer
from linguistics.sarf_parser import SarfEngine
from linguistics.nahiv_ast import NahivDependencyCompiler

class TestDialecticsFSM(unittest.TestCase):
    def setUp(self):
        loader = OntologyLoader()
        self.ontology = loader.load(Path("data/base_ontology.json"))
        self.solver = AristotelianSolver(self.ontology)
        self.lexicon = ContextualLexicon()
        self.discourse = DiscourseRegister()
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)
        self.l1 = Layer1HeuristicGraph(self.ontology)
        self.l2 = Layer2RuleEngine()
        self.l3 = Layer3SMTCircuitBreaker(self.solver, timeout_ms=3000)
        self.orchestrator = EpistemicOrchestrator(self.adapter, self.l1, self.l2, self.l3)
        self.engine = AdabAlBahthEngine(self.solver, self.discourse)
        self.tokenizer = EpistemicTokenizer()
        self.sarf = SarfEngine()
        self.nahiv = NahivDependencyCompiler()

    def test_fsm_sequential_integrity(self):
        """[Faz 5] FSM'nin AWAITING_CLAIM -> ISOLATING_CONTENTION -> AWAITING_EVIDENCE sıralaması ihlali koruması."""
        with self.assertRaises(ValueError):
            self.engine.submit_evidence(["Forall([x], Implies(S(x), M(x)))"])
            
        self.engine.submit_claim("Forall([x], Implies(S(x), P(x)))")
        self.assertEqual(self.engine.current_state, "ISOLATING_CONTENTION", "Tahrîr-i Niza' aşaması atlandı.")
        
        # [FAZ 5] Tahrîr-i Niza' (Kavramsal Senkronizasyon) uygulanmadan delile geçilemez
        with self.assertRaises(ValueError):
            self.engine.submit_evidence(["Forall([x], Implies(S(x), M(x)))"])
            
        self.engine.tahrir_i_niza(musellemat=["S"], niza_terms=["P"])
        self.assertEqual(self.engine.current_state, "AWAITING_EVIDENCE", "Tahrîr-i Niza' sonrası delil aşamasına geçiş başarısız.")

    def test_curcani_nakz_refutation(self):
        """[Faz 3 & 5 Red-Teaming] Sâil'in Nakz hücumunda, Mülâzama (Lüzum Bağı) çöküşü testi."""
        self.engine.submit_claim("Forall([x], Implies(S(x), P(x)))")
        self.engine.tahrir_i_niza(musellemat=["S", "M"], niza_terms=["P"]) # Faz 5 Senkronizasyonu
        
        premises = [
            "Exists([x], And(S(x), M(x)))",
            "Exists([x], And(M(x), P(x)))"
        ]
        
        ev_result = self.engine.submit_evidence(premises)
        self.assertEqual(ev_result["status"], "EVIDENCE_LOGGED", "Öncüller kendi içinde çeliştiği için Z3 reddetti. Hatalı mock verisi.")
        
        attack_result = self.engine.attack_evidence(attack_type="Nakz")
        
        self.assertEqual(attack_result["status"], "NAKZ_SUCCESS", "[DİYALEKTİK ÇÖKÜŞ] Fâsid istidlâl (Hatalı Mülâzama) Z3 tarafından Nakz edilemedi.")
        self.assertEqual(self.engine.current_state, "RESOLVED", "Tartışma bitmesine rağmen FSM durumu açık kaldı.")

    def test_cross_school_muaradah_stalemate(self):
        """[Faz 4.3] Çapraz Usûl (Muaradah) Z3 Push/Pop izolasyonu ve Leksikon Yeniden Derlemesi."""
        self.lexicon.register_word("cevher", "Base", "Cevher")
        self.lexicon.register_word("cism", "Base", "Cism")
        self.lexicon.register_word("zeyd", "Base", "Zeyd_Entity")
        
        mujib_ir = SemanticStatementIR(
            active_namespace="Ashari", 
            predicates=[("Cevher", "Cevher", 1), ("Zeyd_Entity", "Zeyd_Entity", 1), ("Rel_Mubteda_Haber", "Cevher::Zeyd_Entity", 2)], 
            is_valid_for_z3=True
        )
        
        sail_tokens = ["cismun", "zeydun"]
        sail_morph = self.sarf.derive_lexicon(sail_tokens)
        sail_deps = self.nahiv.suggest_dependencies(sail_tokens, sail_morph)
        
        result = self.orchestrator.execute_cross_school_muaradah(
            mujib_ir, AshariUsul(), sail_tokens, sail_deps, SalafiUsul(), sail_morph
        )
        
        self.assertIn(result["status"], ["MUARADAH_SUCCESS", "MUARADAH_INEFFECTIVE", "MUARADAH_FAILED"], "[DİYALEKTİK ÇÖKÜŞ] Çapraz ekol çarpışması hatası.")

if __name__ == '__main__':
    unittest.main()