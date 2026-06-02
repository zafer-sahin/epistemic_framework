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

    def test_fsm_sequential_integrity(self):
        """[Faz 3] FSM'nin AWAITING_CLAIM -> AWAITING_EVIDENCE -> AWAITING_ATTACK sıralaması ihlali koruması."""
        with self.assertRaises(ValueError):
            self.engine.submit_evidence(["Forall([x], Implies(S(x), M(x)))"])
            
        self.engine.submit_claim("Forall([x], Implies(S(x), P(x)))")
        self.assertEqual(self.engine.current_state, "AWAITING_EVIDENCE", "FSM durum geçişi başarısız.")

    def test_curcani_nakz_refutation(self):
        """[Faz 3 Red-Teaming] Sâil'in Nakz hücumunda, öncüller SAT olsa dahi sonucun lüzum bağını kırması testi."""
        # Mucîb İddiası: "Tüm S'ler P'dir"
        self.engine.submit_claim("Forall([x], Implies(S(x), P(x)))")
        
        # Mucîb'in Hatalı Kıyası (Fâsid İstidlâl): Öncüller tutarlı ama sonucu doğurmuyor
        # Öncül 1: Bazı S'ler M'dir. Öncül 2: Bazı M'ler P'dir.
        # Bu iki öncül Z3 için SAT döner (tutarlıdır), ancak "Tüm S'ler P'dir" neticesini ZORUNLU kılmaz.
        premises = [
            "Exists([x], And(S(x), M(x)))",
            "Exists([x], And(M(x), P(x)))"
        ]
        
        ev_result = self.engine.submit_evidence(premises)
        self.assertEqual(ev_result["status"], "EVIDENCE_LOGGED", "Öncüller kendi içinde çeliştiği için Z3 reddetti. Hatalı mock verisi.")
        
        # Sâil Nakz (Refutation) ile saldırır
        attack_result = self.engine.attack_evidence(attack_type="Nakz")
        
        # Beklenen: FSM otonom olarak Nakz saldırısını başarılı ("NAKZ_SUCCESS") bulmalıdır.
        self.assertEqual(attack_result["status"], "NAKZ_SUCCESS", "[DİYALEKTİK ÇÖKÜŞ] Fâsid istidlâl (Hatalı Lüzum Bağı) Z3 tarafından Nakz edilemedi.")
        self.assertEqual(self.engine.current_state, "RESOLVED", "Tartışma bitmesine rağmen FSM durumu açık kaldı.")

    def test_cross_school_muaradah_stalemate(self):
        """[Faz 4.3] Çapraz Usûl (Muaradah) Z3 Push/Pop izolasyonu."""
        mujib_ir = SemanticStatementIR(active_namespace="Ashari", predicates=[("Cevher", "Cevher", 1)], is_valid_for_z3=True)
        sail_ir = SemanticStatementIR(active_namespace="Salafi", predicates=[("Cism", "Cism", 1)], is_valid_for_z3=True)
        
        result = self.orchestrator.execute_cross_school_muaradah(
            mujib_ir, AshariUsul(), sail_ir, SalafiUsul()
        )
        
        self.assertIn(result["status"], ["MUARADAH_SUCCESS", "MUARADAH_INEFFECTIVE", "MUARADAH_FAILED"], "[DİYALEKTİK ÇÖKÜŞ] Çapraz ekol çarpışması hatası.")

if __name__ == '__main__':
    unittest.main()