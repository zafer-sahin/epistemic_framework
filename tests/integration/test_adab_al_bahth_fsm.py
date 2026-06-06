import unittest
from pathlib import Path
import z3
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

    def test_fsm_sequential_integrity_and_tahrir(self):
        with self.assertRaises(ValueError):
            self.engine.submit_evidence(["Forall([x], Implies(S(x), M(x)))"])
            
        claim_res = self.engine.submit_claim("Forall([x], Implies(S(x), P(x)))")
        self.assertEqual(self.engine.current_state, "ISOLATING_CONTENTION")
        
        with self.assertRaises(ValueError):
            self.engine.submit_evidence(["Forall([x], Implies(S(x), M(x)))"])
            
        tahrir_res = self.engine.tahrir_i_niza(musellemat=["S"], niza_terms=["P"])
        self.assertEqual(self.engine.current_state, "AWAITING_EVIDENCE")
        self.assertEqual(tahrir_res["status"], "CONTENTION_ISOLATED")

    def test_tahrir_complex_fol_injection(self):
        """[Faz 5 Refaktör] Tahrîr-i Niza' aşamasında kompleks FOL müsellemâtının Z3'e mutlak aksiyom olarak zerk edilmesi."""
        self.engine.submit_claim("Exists([x], Nami(x))")
        
        complex_musellemat = ["Forall([x], Implies(Cemad(x), Cism(x)))", "Cemad"]
        self.engine.tahrir_i_niza(musellemat=complex_musellemat, niza_terms=["Nami"])
        
        res = self.engine.submit_evidence(["Exists([y], Cemad(y))"])
        self.assertEqual(res["status"], "EVIDENCE_LOGGED", "[SENTAKS İHLALİ] Kompleks FOL müsellemât Z3 tarafından işlenemedi.")

    def test_curcani_nakz_counter_model_refutation(self):
        self.engine.submit_claim("Forall([x], Implies(Cemad(x), Nami(x)))")
        self.engine.tahrir_i_niza(musellemat=["Cemad", "Cism"], niza_terms=["Nami"]) 
        
        premises = [
            "Exists([x], And(Cemad(x), Cism(x)))",
            "Exists([x], And(Cism(x), Nami(x)))"
        ]
        
        ev_result = self.engine.submit_evidence(premises)
        self.assertEqual(ev_result["status"], "EVIDENCE_LOGGED")
        
        attack_result = self.engine.attack_evidence(attack_type="Nakz")
        
        self.assertEqual(attack_result["status"], "NAKZ_SUCCESS")
        self.assertEqual(self.engine.current_state, "RESOLVED")
        self.assertIn("counter_model_extract", attack_result)

    def test_cross_school_muaradah_dynamic_weight_optimization(self):
        """[Faz 5 Refaktör] Mu'aradah çapraz-ekol çarpışmasında ontolojik derinliğe göre dinamik ağırlık cezası ölçümü."""
        self.lexicon.register_word("cevher", "Base", "Cevher")
        self.lexicon.register_word("cism", "Base", "Cism")
        self.lexicon.register_word("zeyd", "Base", "Zeyd_Entity")
        self.lexicon.register_word("nam", "Base", "Nami")
        
        mujib_ir = SemanticStatementIR(
            active_namespace="Ashari", 
            predicates=[("Cevher", "Cevher", 1), ("Zeyd_Entity", "Zeyd_Entity", 1), ("Rel_Mubteda_Haber", "Cevher::Zeyd_Entity", 2)], 
            is_valid_for_z3=True
        )
        
        sail_tokens = ["cismun", "nami"]
        sail_morph = self.sarf.derive_lexicon(sail_tokens)
        sail_deps = self.nahiv.suggest_dependencies(sail_tokens, sail_morph)
        
        result = self.orchestrator.execute_cross_school_muaradah(
            mujib_ir, AshariUsul(), sail_tokens, sail_deps, SalafiUsul(), sail_morph
        )
        
        self.assertIn(result["status"], ["MUARADAH_SUCCESS", "MUARADAH_INEFFECTIVE"])
        if result["status"] == "MUARADAH_SUCCESS":
            self.assertIn("ontolojik ağırlık maliyetiyle", result["message"])

    def test_tahsil_i_hasil_rejection(self):
        """[Faz 5] Tautoloji içeren (Z3'te kendi içinde ispatlı) aksiyomların reddi."""
        tautology_claim = "Forall([x_env], Or(Cism(x_env), Not(Cism(x_env))))"
        response = self.engine.submit_claim(tautology_claim)
        
        self.assertEqual(response["status"], "TAHSIL_I_HASIL")
        self.assertEqual(self.engine.current_state, "RESOLVED")

    def test_recursive_men_stack_operation(self):
        """[Faz 5] Rekürsif 'Men' saldırısı ve yığıt (stack) yönetimi."""
        # İddia: Her Cemad Nami'dir. (Ontolojide geçersiz olduğu için Tahsîl-i Hâsıl'a takılmaz)
        main_claim = "Forall([x_env], Implies(Cemad(x_env), Nami(x_env)))"
        self.engine.submit_claim(main_claim)
        self.engine.tahrir_i_niza(["Cevher"], ["Cemad", "Nami"])
        
        # Yanıltıcı delil
        p1 = "Forall([x_env], Implies(Cemad(x_env), Hayvan(x_env)))"
        p2 = "Forall([x_env], Implies(Hayvan(x_env), Nami(x_env)))"
        self.engine.submit_evidence([p1, p2])
        
        men_response = self.engine.attack_evidence("Men", target_premise=p1)
        
        self.assertEqual(men_response["status"], "MEN_ON_PREMISE")
        self.assertEqual(len(self.engine.claim_stack), 1)
        self.assertEqual(self.engine.active_claim, p1)
        self.assertEqual(self.engine.current_state, "ISOLATING_CONTENTION")
        
        self.engine.tahrir_i_niza([], ["Cemad", "Hayvan"])
        sub_p1 = "Forall([x_env], Implies(Cemad(x_env), Insan(x_env)))"
        sub_p2 = "Forall([x_env], Implies(Insan(x_env), Hayvan(x_env)))"
        self.engine.submit_evidence([sub_p1, sub_p2])
        
        nakz_response = self.engine.attack_evidence("Nakz")
        
        self.assertEqual(nakz_response["status"], "SUB_CLAIM_PROVEN")
        self.assertEqual(len(self.engine.claim_stack), 0)
        self.assertEqual(self.engine.active_claim, main_claim)
        self.assertEqual(self.engine.current_state, "AWAITING_ATTACK")

    def test_mukabere_self_contradiction(self):
        """[Faz 5] Mucîb'in kendi öncüllerinin çelişmesi durumu (UNSAT öngörüsü)."""
        claim = "Forall([x_env], Implies(Cemad(x_env), Hayvan(x_env)))"
        self.engine.submit_claim(claim)
        self.engine.tahrir_i_niza([], ["Cemad"])
        
        # Z3'ün boş küme (vacuously true) ile kaçmasını engellemek için varoluşsal bir çelişki sunuyoruz.
        p1 = "Exists([x_env], And(Cemad(x_env), Cism(x_env)))"
        p2 = "Forall([x_env], Not(Cism(x_env)))"
        
        response = self.engine.submit_evidence([p1, p2])
        
        self.assertEqual(response["status"], "MUKABERE")
        self.assertEqual(self.engine.current_state, "RESOLVED")

if __name__ == '__main__':
    unittest.main()