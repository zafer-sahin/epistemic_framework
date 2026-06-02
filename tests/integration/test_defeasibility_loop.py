import unittest
from pathlib import Path
from core.models import OntologyLoader, EpistemicEntity, TermModel
from core.logic_engine import AristotelianSolver
from core.layer1_graph import Layer1HeuristicGraph
from core.layer2_rules import Layer2RuleEngine
from core.layer3_smt import Layer3SMTCircuitBreaker
from core.epistemic_orchestrator import EpistemicOrchestrator
from linguistics.tokenizer import EpistemicTokenizer
from linguistics.sarf_parser import SarfEngine
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister
from linguistics.ilm_wad_adapter import IlmWadAdapter
from schools.maturidi_usul import MaturidiUsul
from schools.salafi_usul import SalafiUsul

class TestDefeasibilityEngine(unittest.TestCase):
    def setUp(self):
        loader = OntologyLoader()
        self.ontology = loader.load(Path("data/base_ontology.json"))
        self.solver = AristotelianSolver(self.ontology)
        self.tokenizer = EpistemicTokenizer()
        self.sarf = SarfEngine()
        self.nahiv = NahivDependencyCompiler()
        self.lexicon = ContextualLexicon()
        self.discourse = DiscourseRegister()
        
        self.lexicon.register_word("yad", "Salafi", "Sifat_Yed_Literal")
        
        # Mâtürîdî uzayında literal anlam Kadiyye-i_Hamliyye, mecaz anlam Metaphor_Fallback olarak ayrıştırılmalıdır.
        self.lexicon.register_word("yad", "Maturidi", "Sifat_Yed_Literal", proposition_type="Kadiyye-i_Hamliyye")
        self.lexicon.register_word("yad", "Maturidi", "Sifat_Yed_Metaphor", proposition_type="Metaphor_Fallback")
        
        self.lexicon.register_word("allah", "Base", "Wajib_al_Wujud")
        self.lexicon.register_word("tekvin", "Maturidi", "Tekvin")
        
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)
        self.l1 = Layer1HeuristicGraph(self.ontology)
        
        # [MOCK L1 GRAPH] Karîne-i Mânia algılanması için LCA yerine Modal Uyuşmazlık matrisi enjekte edilir
        self.l1.entity_map["Wajib_al_Wujud"] = EpistemicEntity(
            ontologic_id="Wajib_al_Wujud", terms=TermModel(ar="Allah"), modal_status="Wajib", husn_u_mucerred=True
        )
        self.l1.entity_map["Sifat_Yed_Literal"] = EpistemicEntity(
            ontologic_id="Sifat_Yed_Literal", terms=TermModel(ar="Yed"), modal_status="Mumkin", husn_u_mucerred=False
        )
        self.l1.entity_map["Tekvin"] = EpistemicEntity(
            ontologic_id="Tekvin", terms=TermModel(ar="Tekvin"), modal_status="Mumkin", husn_u_mucerred=False
        )

        self.l2 = Layer2RuleEngine()
        self.l3 = Layer3SMTCircuitBreaker(self.solver, timeout_ms=3000)
        
        # [MOCK L3 Z3] Z3'ün Literal bağlamda çelişki (UNSAT) üretmesini simüle ediyoruz
        original_sat_check = self.l3.execute_sat_check
        def mock_sat_check(ir_matrix):
            for pred in ir_matrix.predicates:
                if isinstance(pred, tuple) and "Sifat_Yed_Literal" in pred[1]:
                    return {"status": "UNSAT", "message": "AXIOM_DISJOINT_Wajib_al_Wujud_AND_Sifat_Yed_Literal"}
            return original_sat_check(ir_matrix)
        self.l3.execute_sat_check = mock_sat_check

        self.orchestrator = EpistemicOrchestrator(self.adapter, self.l1, self.l2, self.l3)

        sentence = "yadu allahi"
        self.tokens = self.tokenizer.tokenize(sentence)
        self.morph = self.sarf.derive_lexicon(self.tokens)
        self.ast = self.nahiv.suggest_dependencies(self.tokens, self.morph)

        tekvin_sentence = "tekvinu allahi"
        self.tekvin_tokens = self.tokenizer.tokenize(tekvin_sentence)
        self.tekvin_morph = self.sarf.derive_lexicon(self.tekvin_tokens)
        self.tekvin_ast = self.nahiv.suggest_dependencies(self.tekvin_tokens, self.tekvin_morph)

    def test_autonomous_tevil_recovery(self):
        """[Faz 3.2] Z3 UNSAT sonrasında orkestratörün Metaphor_Fallback ile kurtarma (SAT) işlemi."""
        result = self.orchestrator.process_statement(self.tokens, self.ast, MaturidiUsul(), self.morph)
        self.assertTrue(result.get("tevil_applied"), "[ÇÖKÜŞ] Defeasibility döngüsü tetiklenmedi.")
        self.assertEqual(result["status"], "SAT", "[MANTIK HATASI] Te'vil sonrası Z3 SAT üretemedi.")

    def test_l2_blocked_nodes_dsl(self):
        """[Faz 3.3] Maturidi Usulü'ndeki 'Tekvin' spesifik DSL düğüm blokesi."""
        result = self.orchestrator.process_statement(self.tekvin_tokens, self.tekvin_ast, MaturidiUsul(), self.tekvin_morph)
        self.assertEqual(result["status"], "REJECTED_BY_USUL", "[OTORİTE İHLALİ] Yasaklı düğüm te'vile uğradı.")
        
    def test_zero_transformation_salafi(self):
        """[Faz 3.3] Selefi Usulü'nün (allow_tevil=False) mutlak literalizm kısıtı."""
        result = self.orchestrator.process_statement(self.tokens, self.ast, SalafiUsul(), self.morph)
        # Selefi kural motoru "allow_tevil=False" olduğu için direkt BLOCK atar ve usûl reddi döner
        self.assertEqual(result["status"], "REJECTED_BY_USUL", "[OTORİTE İHLALİ] Selefi usulünde te'vil (geri çekilme) yapıldı.")

if __name__ == '__main__':
    unittest.main()