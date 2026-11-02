import unittest
from pathlib import Path

from core.exceptions import ContextPoisoningError
from core.models import OntologyLoader
from core.logic_engine import AristotelianSolver
from core.layer1_graph import Layer1HeuristicGraph
from core.layer2_rules import Layer2RuleEngine
from core.layer3_smt import Layer3SMTCircuitBreaker
from core.epistemic_orchestrator import EpistemicOrchestrator, CONSISTENT_STATUSES
from linguistics.tokenizer import EpistemicTokenizer
from linguistics.sarf_parser import SarfEngine
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.contextual_lexicon import ContextualLexicon, LocalOntoLexSemanticClient
from linguistics.discourse_state import DiscourseRegister
from linguistics.ilm_wad_adapter import IlmWadAdapter
from schools.ashari_usul import AshariUsul
from schools.maturidi_usul import MaturidiUsul
from schools.salafi_usul import SalafiUsul

"""
.. felsefe_notu:: Müsellemât ve Leksikal Zehirlenme
    Mu'âraza, iki tarafın aynı konudan söz etmesini gerektirir. Base (müsellem) uzayından
    çözülen ortak bir kavram (Örn: 'allah' -> Vâcibu'l-Vücûd), onu ilk anan tarafın ekolüne
    mühürlenmez. Ortak ontolojideki (Porphyrios Ağacı) bir kavram da, bir ekolün sözlüğünden
    çözülse bile ortaktır (Örn: Eş'arî ve Mâtürîdî için 'yed' -> Sifat_Yed_Literal). Zehirlenme
    koruması ağaçta bulunmayan, ekole özgü kimlikler ve söylemde tanıtılan varlıklar için geçerlidir.
"""


class TestSharedConceptPoisoning(unittest.TestCase):
    def setUp(self):
        ontology = OntologyLoader().load(Path("data/base_ontology.json"))
        self.discourse = DiscourseRegister()
        self.lexicon = ContextualLexicon(semantic_client=LocalOntoLexSemanticClient())
        # REPL ile aynı kayıtlar
        self.lexicon.register_word("allah", "Base", "Wajib_al_Wujud")
        self.lexicon.register_word("yad", "Salafi", "Sifat_Yed_Literal")
        self.lexicon.register_word("yad", "Salafi", "Sifat_Yed_Bila_Kayf", proposition_type="Kadiyye-i_Hamliyye", sibak_trigger="allah")
        self.lexicon.register_word("yad", "Ashari", "Sifat_Yed_Literal", proposition_type="Kadiyye-i_Hamliyye")
        self.lexicon.register_word("yad", "Ashari", "Sifat_Yed_Metaphor", proposition_type="Metaphor_Fallback")
        self.lexicon.register_word("yad", "Maturidi", "Sifat_Yed_Literal", proposition_type="Kadiyye-i_Hamliyye")
        self.lexicon.register_word("yad", "Maturidi", "Sifat_Yed_Metaphor", proposition_type="Metaphor_Fallback")

        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)
        self.tokenizer = EpistemicTokenizer()
        self.sarf = SarfEngine()
        self.nahiv = NahivDependencyCompiler()
        l3 = Layer3SMTCircuitBreaker(AristotelianSolver(ontology), timeout_ms=3000)
        self.orchestrator = EpistemicOrchestrator(self.adapter, Layer1HeuristicGraph(ontology), Layer2RuleEngine(), l3)

    def _cozumle(self, cumle: str):
        tokens = self.tokenizer.tokenize(cumle)
        morph = self.sarf.derive_lexicon(tokens)
        return tokens, morph, self.nahiv.suggest_dependencies(tokens, morph)

    def _mucib_soyler(self, cumle: str, namespace: str = "Ashari"):
        self.discourse.set_agent("Mujib")
        tokens, morph, deps = self._cozumle(cumle)
        return self.adapter.generate_ir(tokens, deps, namespace, morph)

    def test_shared_base_concept_is_usable_by_opponent(self):
        self._mucib_soyler("yadu allahi")
        self.discourse.set_agent("Sail")
        try:
            sonuc = self.lexicon.resolve_id("allah", "Salafi", discourse=self.discourse)
        except ContextPoisoningError as exc:
            self.fail(f"Mucîb'in de andığı ortak (Base) kavram, Sâil için zehirlenme sayıldı: {exc}")
        self.assertEqual(sonuc, "Wajib_al_Wujud")

    def test_school_specific_backdoor_is_still_rejected(self):
        """Ekole özgü bir anlamın kimliğini rakip ekolün kaydıyla çekmek hâlâ engellenmeli."""
        self.lexicon.register_word("ruh", "Ashari", "Onto_Ruh_Ashari")
        self._mucib_soyler("ruhun")
        self.lexicon.register_word("ruh", "Salafi", "Onto_Ruh_Ashari")
        self.discourse.set_agent("Sail")
        with self.assertRaises(ContextPoisoningError):
            self.lexicon.resolve_id("ruh", "Salafi", discourse=self.discourse)

    def test_cross_school_muaradah_on_shared_concept_is_not_poisoning(self):
        mucib_iddiasi = self._mucib_soyler("yadu allahi")
        self.discourse.set_agent("Sail")
        tokens, morph, deps = self._cozumle("yadu allahi")
        sonuc = self.orchestrator.execute_cross_school_muaradah(
            mucib_iddiasi, AshariUsul(), tokens, deps, SalafiUsul(), morph)
        self.assertNotIn("Lexical Poisoning", sonuc.get("message", ""))
        self.assertNotEqual(sonuc["status"], "ERROR", sonuc.get("message"))

    def test_shared_ontology_concept_in_both_schools_is_not_poisoning(self):
        """İki ekolün sözlüğü 'yed'i aynı ortak kavrama (Sifat_Yed_Literal) bağlıyorsa rakibin anması zehirlenme değildir."""
        self._mucib_soyler("yadu allahi")
        self.discourse.set_agent("Sail")
        try:
            sonuc = self.lexicon.resolve_id("yad", "Maturidi", discourse=self.discourse)
        except ContextPoisoningError as exc:
            self.fail(f"Ortak ontolojideki kavramı kendi sözlüğünden çözen Sâil için zehirlenme sayıldı: {exc}")
        self.assertEqual(sonuc, "Sifat_Yed_Literal")

    def test_cross_school_muaradah_between_ashari_and_maturidi_is_not_poisoning(self):
        """Eş'arî Mucîb'e karşı Mâtürîdî Sâil mu'ârazaya girebilmeli; iki ekol de 'yed'i Kudret diye te'vil eder."""
        tokens, morph, deps = self._cozumle("yadu allahi")
        self.discourse.set_agent("Mujib")
        mucib_sonucu, mucib_okumasi = self.orchestrator.evaluate_statement(tokens, deps, AshariUsul(), morph)
        self.assertIn(mucib_sonucu["status"], CONSISTENT_STATUSES, mucib_sonucu.get("message"))

        self.discourse.set_agent("Sail")
        sonuc = self.orchestrator.execute_cross_school_muaradah(
            mucib_okumasi, AshariUsul(), tokens, deps, MaturidiUsul(), morph)
        self.assertEqual(sonuc["status"], "MUARADAH_INEFFECTIVE", sonuc.get("message"))


if __name__ == "__main__":
    unittest.main()
