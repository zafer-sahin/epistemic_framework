import unittest
from pathlib import Path
from core.models import OntologyLoader
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
from schools.ashari_usul import AshariUsul

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
        
        # [FAZ 6] İbn Teymiyye AST Tabanlı Node Relocation Leksikon Yapılandırması
        self.lexicon.register_word("yad", "Salafi", "Sifat_Yed_Literal")
        self.lexicon.register_word("yad", "Salafi", "Sifat_Yed_Bila_Kayf", proposition_type="Kadiyye-i_Hamliyye", sibak_trigger="allah")
        
        # [FAZ 3] Ma'nâ el-Ma'nâ Leksikon Yapılandırması
        self.lexicon.register_word("yad", "Maturidi", "Sifat_Yed_Literal", proposition_type="Kadiyye-i_Hamliyye")
        self.lexicon.register_word("yad", "Maturidi", "Sifat_Yed_Metaphor", proposition_type="Metaphor_Fallback")
        self.lexicon.register_word("yad", "Ashari", "Sifat_Yed_Literal", proposition_type="Kadiyye-i_Hamliyye")
        self.lexicon.register_word("yad", "Ashari", "Sifat_Yed_Metaphor", proposition_type="Metaphor_Fallback")
        
        self.lexicon.register_word("allah", "Base", "Wajib_al_Wujud")
        self.lexicon.register_word("tekvin", "Maturidi", "Tekvin")
        
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)
        self.l1 = Layer1HeuristicGraph(self.ontology)
        self.l2 = Layer2RuleEngine()
        self.l3 = Layer3SMTCircuitBreaker(self.solver, timeout_ms=3000)

        self.orchestrator = EpistemicOrchestrator(self.adapter, self.l1, self.l2, self.l3)

        self.sentence = "yadu allahi"
        self.tokens = self.tokenizer.tokenize(self.sentence)
        self.morph = self.sarf.derive_lexicon(self.tokens)
        self.ast = self.nahiv.suggest_dependencies(self.tokens, self.morph)

        self.tekvin_sentence = "tekvinu allahi"
        self.tekvin_tokens = self.tokenizer.tokenize(self.tekvin_sentence)
        self.tekvin_morph = self.sarf.derive_lexicon(self.tekvin_tokens)
        self.tekvin_ast = self.nahiv.suggest_dependencies(self.tekvin_tokens, self.tekvin_morph)

    def test_autonomous_tevil_recovery_with_mana_bridge(self):
        """[Faz 3] Z3 UNSAT sonrasında orkestratörün Ma'nâ el-Ma'nâ köprüsünü ispatlayarak kurtarma (SAT) işlemi."""
        self.discourse.clear_memory()
        result = self.orchestrator.process_statement(self.tokens, self.ast, MaturidiUsul(), self.morph)
        
        self.assertTrue(result.get("tevil_applied"), "[ÇÖKÜŞ] Defeasibility döngüsü tetiklenmedi.")
        self.assertEqual(result["status"], "SAT", "[MANTIK HATASI] Te'vil sonrası Z3 SAT üretemedi.")
        self.assertIn("İlm-i Beyân Çıkarımı", result["message"], "[SEMANTİK ZAFİYET] Ma'nâ el-Ma'nâ (Alâka) köprüsü Z3'e ispatlatılmadı.")

    def test_l2_blocked_nodes_dsl(self):
        """[Faz 3.3] Maturidi Usulü'ndeki 'Tekvin' spesifik DSL düğüm blokesi."""
        self.discourse.clear_memory()
        result = self.orchestrator.process_statement(self.tekvin_tokens, self.tekvin_ast, MaturidiUsul(), self.tekvin_morph)
        self.assertEqual(result["status"], "REJECTED_BY_USUL", "[OTORİTE İHLALİ] Yasaklı düğüm te'vile uğradı.")
        
    def test_ibn_teymiyye_bila_kayf_relocation(self):
        """[Faz 6] Selefî Usulü'nün (allow_tevil=False) AST tabanlı Bila-Kayf hakikat taşıması kuralı."""
        self.discourse.clear_memory()
        result = self.orchestrator.process_statement(self.tokens, self.ast, SalafiUsul(), self.morph)
        
        self.assertEqual(result["status"], "SAT_BILA_KAYF", "[OTORİTE İHLALİ] İbn Teymiyye hakikat taşınması (Bila-Kayf) mekanizması çalışmadı.")
        self.assertEqual(result["l2_context"], "BILA_KAYF_NODE_RELOCATION", "L2 otoritesi yanlış karar mekanizması işletti.")

if __name__ == '__main__':
    unittest.main()