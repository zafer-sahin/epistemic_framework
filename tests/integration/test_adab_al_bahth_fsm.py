import unittest
from pathlib import Path
from unittest import mock
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
    """
    [FAZ 4 ve FAZ 5] Cürcânî Diyalektiği Sonlu Durum Makinesi (FSM) Test Süiti.
    
    .. pedagojik_anlati::
        Bu test matrisi, Âdâb-ı Bahs münazara kurallarının Kripke uzayında nasıl 
        davrandığını doğrular. Tahrîr-i Niza', Men', Nakz ve Mu'aradah saldırılarının 
        Z3 motorundaki ontolojik yansımaları (Counter-Model ve Stalemate) sınanır.
        Ayrıca Faz 4.1 Bipartite DRT bağlam yalıtımı, FSM nöbet değişimleriyle entegre test edilir.
    """
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
        """
        .. mantik_kurali:: Diyalektik Nöbet Değişimi
        İddia, Tahrîr ve Delil adımları arasında Sâil ve Mucîb'in DRT yığıtlarındaki 
        nöbet değişiminin (Agent Transition) katı kurallara uyması test edilir.
        """
        with self.assertRaises(ValueError):
            # Da'vâ (İddia) olmadan delil sunulamaz.
            self.engine.submit_evidence(["Forall([x], Implies(S(x), M(x)))"])
            
        claim_res = self.engine.submit_claim("Forall([x], Implies(S(x), P(x)))")
        self.assertEqual(self.engine.current_state, "ISOLATING_CONTENTION")
        self.assertEqual(self.engine.discourse.active_agent, "Sail", "İddia sonrası Tahrîr için nöbet Sâil'e geçmelidir.")
        
        with self.assertRaises(ValueError):
            # Tahrîr-i Niza' (Kavramsal Senkronizasyon) yapılmadan delil sunulamaz.
            self.engine.submit_evidence(["Forall([x], Implies(S(x), M(x)))"])
            
        tahrir_res = self.engine.tahrir_i_niza(musellemat=["S"], niza_terms=["P"])
        self.assertEqual(self.engine.current_state, "AWAITING_EVIDENCE")
        self.assertEqual(self.engine.discourse.active_agent, "Mujib", "Tahrîr sonrası delil yükümlülüğü Mucîb'e aittir.")
        self.assertEqual(tahrir_res["status"], "CONTENTION_ISOLATED")

    def test_tahrir_complex_fol_injection(self):
        """[Faz 4.2] Tahrîr-i Niza' aşamasında kompleks FOL müsellemâtının Z3'e mutlak aksiyom olarak zerk edilmesi."""
        self.engine.submit_claim("Exists([x], Nami(x))")
        
        complex_musellemat = ["Forall([x], Implies(Cemad(x), Cism(x)))", "Cemad"]
        self.engine.tahrir_i_niza(musellemat=complex_musellemat, niza_terms=["Nami"])
        
        res = self.engine.submit_evidence(["Exists([y], Cemad(y))"])
        self.assertEqual(res["status"], "EVIDENCE_LOGGED", "[SENTAKS İHLALİ] Kompleks FOL müsellemât Z3 tarafından işlenemedi.")

    def test_curcani_nakz_counter_model_refutation(self):
        """
        .. felsefe_notu:: Nakz ve Fâsid İstidlâl
        Mucîb'in öncülleri doğru kabul edilse bile, neticenin yanlış olabildiği bir 
        Kripke Counter-Model (Karşı-Model) ispatlanarak Mülâzama'nın (Lüzum Bağı) çökertilmesi.
        """
        self.engine.submit_claim("Forall([x], Implies(Cemad(x), Nami(x)))")
        self.engine.tahrir_i_niza(musellemat=["Cemad", "Cism"], niza_terms=["Nami"]) 
        
        premises = [
            "Exists([x], And(Cemad(x), Cism(x)))",
            "Exists([x], And(Cism(x), Nami(x)))"
        ]
        
        ev_result = self.engine.submit_evidence(premises)
        self.assertEqual(ev_result["status"], "EVIDENCE_LOGGED")
        self.assertEqual(self.engine.discourse.active_agent, "Sail", "Delil sunulduktan sonra saldırı nöbeti Sâil'e geçmelidir.")
        
        attack_result = self.engine.attack_evidence(attack_type="Nakz")
        
        self.assertEqual(attack_result["status"], "NAKZ_SUCCESS")
        self.assertEqual(self.engine.current_state, "RESOLVED")
        self.assertIn("counter_model_extract", attack_result)

    def test_fsm_muaradah_stalemate_generation(self):
        """
        [Faz 4.3] Mu'aradah saldırısı testi.
        Karşı-iddia müsellemât, delil ve ontolojiyle birlikte sınanır; saldırı münazarayı sonuçlandırır.
        """
        self.engine.submit_claim("Forall([x], Implies(S(x), P(x)))")
        self.engine.tahrir_i_niza(musellemat=["S"], niza_terms=["P"])
        self.engine.submit_evidence(["Forall([x], Implies(S(x), M(x)))", "Forall([x], Implies(M(x), P(x)))"])

        # Sâil Mu'aradah yapar: delili men' etmeden iddianın hilâfını ileri sürer
        result = self.engine.attack_evidence("Muaradah", target_premise="Forall([x], Implies(S(x), Not(P(x))))")
        
        self.assertIn(result["status"], ["STALEMATE", "MUARADAH_FAILED"])
        self.assertEqual(self.engine.current_state, "RESOLVED")

    def test_cross_school_muaradah_reports_conflict_reason(self):
        """[Faz 5] Orkestratör üzerinden Mu'aradah: çapraz-ekol çarpışmasında çatışmanın gerekçesi raporlanır."""
        self.lexicon.register_word("cevher", "Base", "Cevher")
        self.lexicon.register_word("cism", "Base", "Cism")
        self.lexicon.register_word("zeyd", "Base", "Zeyd_Entity")
        self.lexicon.register_word("nam", "Base", "Nami")
        
        mujib_ir = SemanticStatementIR(
            active_namespace="Ashari", 
            active_agent="Mujib",
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
            self.assertTrue(result["conflict"]["axioms"], "Çatışmanın dayandığı aksiyomlar raporlanmadı.")

    def _yed_okumalarini_kaydet(self):
        """REPL ile aynı 'yad' kayıtları: Selefî bilâ-keyf, Eş'arî literal ve mecaz okumaları."""
        self.lexicon.register_word("yad", "Salafi", "Sifat_Yed_Literal")
        self.lexicon.register_word("yad", "Salafi", "Sifat_Yed_Bila_Kayf", proposition_type="Kadiyye-i_Hamliyye", sibak_trigger="allah")
        self.lexicon.register_word("yad", "Ashari", "Sifat_Yed_Literal", proposition_type="Kadiyye-i_Hamliyye")
        self.lexicon.register_word("yad", "Ashari", "Sifat_Yed_Metaphor", proposition_type="Metaphor_Fallback")

    def _cozumle(self, cumle):
        tokens = self.tokenizer.tokenize(cumle)
        morph = self.sarf.derive_lexicon(tokens)
        return tokens, morph, self.nahiv.suggest_dependencies(tokens, morph)

    def _mucib_iddiasi(self, cumle, namespace):
        tokens, morph, deps = self._cozumle(cumle)
        self.discourse.set_agent("Mujib")
        mujib_ir = self.adapter.generate_ir(tokens, deps, namespace, morph)
        self.discourse.set_agent("Sail")
        return mujib_ir

    def test_cross_school_muaradah_accepts_salafi_bila_kayf_reading(self):
        """Selefî profilin tutarlı sonucu (SAT_BILA_KAYF), Sâil'in karşı delili olarak geçersiz sayılmamalı."""
        self._yed_okumalarini_kaydet()
        tokens, morph, deps = self._cozumle("yadu allahi")
        mujib_ir = self._mucib_iddiasi("yadu allahi", "Ashari")

        sail_ir = self.adapter.generate_ir(tokens, deps, "Salafi", morph)
        self.assertEqual(SalafiUsul().execute_dag(sail_ir, self.l1, self.l2, self.l3)["status"], "SAT_BILA_KAYF")

        result = self.orchestrator.execute_cross_school_muaradah(
            mujib_ir, AshariUsul(), tokens, deps, SalafiUsul(), morph
        )

        self.assertIn(result["status"], ["MUARADAH_SUCCESS", "MUARADAH_INEFFECTIVE", "MUJIB_INVALID"], result.get("message"))

    def test_cross_school_muaradah_injects_sails_own_reading(self):
        """Çapraz zerkte Sâil'in kendi usûlündeki okuması kullanılmalı; cümlesi Mucîb'in sözlüğüyle yeniden okunmamalı."""
        self._yed_okumalarini_kaydet()
        tokens, morph, deps = self._cozumle("yadu allahi")
        mujib_ir = self._mucib_iddiasi("yadu allahi", "Ashari")

        result = self.orchestrator.execute_cross_school_muaradah(
            mujib_ir, AshariUsul(), tokens, deps, SalafiUsul(), morph
        )

        okuma = str(result.get("sail_reading"))
        self.assertIn("Sifat_Yed_Bila_Kayf", okuma, "Selefî okuması karşılaştırmaya girmedi.")
        self.assertNotIn("Sifat_Yed_Literal", okuma, "Sâil'in cümlesi Mucîb'in (Eş'arî) sözlüğüyle yeniden okundu.")

    def test_cross_school_muaradah_uses_sails_tevil_reading(self):
        """Te'vil uygulayan bir ekolün Sâil'i, karşılaştırmaya te'vil sonrası okumasıyla girmeli."""
        self._yed_okumalarini_kaydet()
        tokens, morph, deps = self._cozumle("yadu allahi")
        mujib_ir = self._mucib_iddiasi("yadu allahi", "Salafi")

        result = self.orchestrator.execute_cross_school_muaradah(
            mujib_ir, SalafiUsul(), tokens, deps, AshariUsul(), morph
        )

        okuma = str(result.get("sail_reading"))
        self.assertIn("Kudret", okuma, "Eş'arî Sâil'in te'vil sonrası okuması karşılaştırmaya girmedi.")
        self.assertNotIn("Sifat_Yed_Literal", okuma)

    def test_cross_school_muaradah_rejects_sail_reading_that_stays_contradictory(self):
        """Sâil'in okuması kendi usûlünde (te'vil denendikten sonra da) çelişkili kalıyorsa karşı delil sayılmaz."""
        tokens, morph, deps = self._cozumle("cemadun")
        mujib_ir = SemanticStatementIR(active_namespace="Salafi", active_agent="Mujib", predicates=[("Cemad", "Cemad", 1)], is_valid_for_z3=True)
        sail_usul = AshariUsul()
        celiskili = {"status": "FALLBACK_TRIGGERED", "message": "Z3 Çelişkisi.", "unsat_core": "", "l2_context": "PROCEED_LITERAL"}

        with mock.patch.object(sail_usul, "execute_dag", return_value=celiskili):
            result = self.orchestrator.execute_cross_school_muaradah(
                mujib_ir, SalafiUsul(), tokens, deps, sail_usul, morph
            )

        self.assertEqual(result["status"], "MUARADAH_FAILED", result.get("message"))

    def test_tahsil_i_hasil_rejection(self):
        """[Faz 4] Tautoloji içeren (Z3'te kendi içinde ispatlı) aksiyomların Da'vâ olarak reddi."""
        tautology_claim = "Forall([x_env], Or(Cism(x_env), Not(Cism(x_env))))"
        response = self.engine.submit_claim(tautology_claim)
        
        self.assertEqual(response["status"], "TAHSIL_I_HASIL")
        self.assertEqual(self.engine.current_state, "RESOLVED")

    def test_recursive_men_stack_operation(self):
        """
        [Faz 4] Rekürsif 'Men' saldırısı ve Kripke Scope (Yığıt) yönetimi.
        Sâil'in hedef öncülü reddetmesi durumunda, o öncülün yeni bir Da'vâ'ya dönüşmesi süreci.
        """
        main_claim = "Forall([x_env], Implies(Cemad(x_env), Nami(x_env)))"
        self.engine.submit_claim(main_claim)
        self.engine.tahrir_i_niza(["Cevher"], ["Cemad", "Nami"])
        
        p1 = "Forall([x_env], Implies(Cemad(x_env), Hayvan(x_env)))"
        p2 = "Forall([x_env], Implies(Hayvan(x_env), Nami(x_env)))"
        self.engine.submit_evidence([p1, p2])
        
        men_response = self.engine.attack_evidence("Men", target_premise=p1)
        
        self.assertEqual(men_response["status"], "MEN_ON_PREMISE")
        self.assertEqual(len(self.engine.claim_stack), 1)
        self.assertEqual(self.engine.active_claim, p1, "Men' edilen öncül yeni bir Da'vâ'ya dönüşmelidir.")
        self.assertEqual(self.engine.current_state, "ISOLATING_CONTENTION")
        self.assertEqual(self.engine.discourse.active_agent, "Sail", "Yeni Da'vâ için Tahrîr nöbeti Sâil'e geçmelidir.")
        
        self.engine.tahrir_i_niza([], ["Cemad", "Hayvan"])
        sub_p1 = "Forall([x_env], Implies(Cemad(x_env), Insan(x_env)))"
        sub_p2 = "Forall([x_env], Implies(Insan(x_env), Hayvan(x_env)))"
        self.engine.submit_evidence([sub_p1, sub_p2])
        
        # Sâil Nakz yapar, ancak Lüzum bağı sağlam olduğu için İlzam edilir (Mucîb kazanır).
        nakz_response = self.engine.attack_evidence("Nakz")
        
        self.assertEqual(nakz_response["status"], "SUB_CLAIM_PROVEN")
        self.assertEqual(len(self.engine.claim_stack), 0, "Alt iddia ispatlanınca yığıt temizlenmelidir.")
        self.assertEqual(self.engine.active_claim, main_claim, "Orijinal Da'vâ'ya dönülmelidir.")
        self.assertEqual(self.engine.current_state, "AWAITING_ATTACK")

    def test_mukabere_self_contradiction(self):
        """[Faz 4] Mucîb'in kendi sunduğu öncüllerin çelişmesi (UNSAT öngörüsü / Mukabere)."""
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