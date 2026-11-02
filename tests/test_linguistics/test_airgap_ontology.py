import unittest
from core.exceptions import DiachronicViolationError
from linguistics.contextual_lexicon import ContextualLexicon, StrictAirGapValidator
from linguistics.sarf_parser import SarfEngine
from linguistics.tokenizer import EpistemicTokenizer
from linguistics.ilm_wad_adapter import IlmWadAdapter
from linguistics.discourse_state import DiscourseRegister

class TestAirGappedOntology(unittest.TestCase):
    """
    [FAZ 11] Air-Gapped Ontology & Double Conversion İzolasyon Testleri.
    Sistemin seküler, istatistiksel veya modern (MSA) kütüphanelerden (WordNet, BabelNet vb.)
    gelen ontolojik sızıntıları donanımsal olarak reddettiğini doğrular.
    """

    def setUp(self):
        self.lexicon = ContextualLexicon()
        self.tokenizer = EpistemicTokenizer()
        self.discourse = DiscourseRegister()
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)

    # ---------------------------------------------------------
    # 1. CORE VALIDATOR TESTLERİ
    # ---------------------------------------------------------
    def test_strict_validator_rejects_secular_epochs(self):
        """Zaman damgasının (Epoch) 'Classical' dışında bir değere ayarlanmasını engeller."""
        with self.assertRaises(DiachronicViolationError) as context:
            StrictAirGapValidator.validate_epoch("Modern_Standard_Arabic")
        self.assertIn("Classical", str(context.exception))
        self.assertIn("reddedildi", str(context.exception))

    def test_strict_validator_rejects_secular_namespaces(self):
        """WordNet, NLTK gibi Batılı ontoloji uzaylarının Z3'e sızmasını engeller."""
        poisonous_namespaces = ["wordnet", "nltk", "spacy", "english", "babelnet"]
        for ns in poisonous_namespaces:
            with self.assertRaises(DiachronicViolationError):
                StrictAirGapValidator.validate_namespace(ns)

    def test_strict_validator_rejects_secular_provenance(self):
        """Ontolojik ID içerisindeki istatistiksel imza sızıntılarını yakalar."""
        poisonous_ids = ["wn:001244", "synset:run.v.01", "lemma:go", "en_treebank_node"]
        for pid in poisonous_ids:
            with self.assertRaises(DiachronicViolationError):
                StrictAirGapValidator.validate_provenance(pid)

    # ---------------------------------------------------------
    # 2. LEXICON (İLM-İ VAZ') SIZINTI TESTLERİ
    # ---------------------------------------------------------
    def test_lexicon_registration_airgap(self):
        """Leksikona dışsal bir dilde veya uzayda kelime kaydedilmesini engeller."""
        with self.assertRaises(DiachronicViolationError):
            self.lexicon.register_word(
                word="god", 
                namespace="wordnet", 
                ontologic_id="wn:deity", 
                epoch="Modern"
            )

    def test_lexicon_resolution_airgap(self):
        """AST'den gelen bir düğümün seküler bir uzayda çözümlenmesini kilitler."""
        # Geçerli kayıt
        self.lexicon.register_word("zeyd", "Ashari", "Entity_Zeyd")
        
        with self.assertRaises(DiachronicViolationError):
            self.lexicon.resolve_id("zeyd", active_namespace="babelnet")

    # ---------------------------------------------------------
    # 3. SARF (MORFOLOJİ) VE TOKENIZER TESTLERİ
    # ---------------------------------------------------------
    def test_tokenizer_epoch_lock(self):
        """Tokenizer'ın regex tabanlı modern ayrıştırma yapmasını kilitler."""
        with self.assertRaises(DiachronicViolationError):
            self.tokenizer.tokenize("ve-innema", epoch="MSA")

    def test_sarf_engine_epoch_lock(self):
        """Sarf motorunun başlatılma (init) anında Air-Gap kontrolü yaptığını doğrular."""
        # SarfEngine init anında StrictAirGapValidator.validate_epoch("Classical") çağırır.
        # Dışsal bir manipülasyonla bu aşılırsa bile derivasyon reddedilmelidir.
        engine = SarfEngine()
        self.assertIsNotNone(engine)
        
        # Olasılıksal stemmer hatası (İ'lâl sınırı aşımı)
        with self.assertRaises(ValueError) as context:
            engine._apply_ontolex_rules("tooshort", rule=type("MockRule", (), {"positions": [10, 20]})())
        self.assertIn("Olasılıksal Stemmer kullanımı yasaktır", str(context.exception))

    # ---------------------------------------------------------
    # 4. ADAPTER (Z3 IR GENERATOR) TESTLERİ
    # ---------------------------------------------------------
    def test_adapter_ir_generation_airgap(self):
        """FOL Matrisine (IR) giden yolda çift-dönüşüm mühürünü test eder."""
        tokens = ["zeydun", "kaimun"]
        dependencies = [("Kainun_Virtual", "zeydun", "Mubteda_Haber", "Marfu")]
        
        # Yanlış epoch ile Z3 matrisi üretme girişimi
        with self.assertRaises(DiachronicViolationError):
            self.adapter.generate_ir(tokens, dependencies, active_namespace="Ashari", epoch="Secular")
            
        # Yanlış namespace ile Z3 matrisi üretme girişimi
        with self.assertRaises(DiachronicViolationError):
            self.adapter.generate_ir(tokens, dependencies, active_namespace="wordnet", epoch="Classical")

    def test_adapter_provenance_lock_success(self):
        """Meşru (Classical) bir girişin provenance_locked=True bayrağı ile çıktığını doğrular."""
        self.lexicon.register_word("zeydun", "Ashari", "Entity_Zeydun", epoch="Classical")
        self.lexicon.register_word("kaimun", "Ashari", "Predicate_Kaim", epoch="Classical")
        
        tokens = ["zeydun", "kaimun"]
        dependencies = [("Kainun_Virtual", "zeydun", "Mubteda_Haber", "Marfu")]
        
        ir_result = self.adapter.generate_ir(tokens, dependencies, active_namespace="Ashari", epoch="Classical")
        
        self.assertTrue(ir_result.is_valid_for_z3)
        self.assertTrue(ir_result.provenance_locked, "Z3 Matrisi donanımsal mühür (provenance_locked) taşımıyor!")

if __name__ == '__main__':
    unittest.main()