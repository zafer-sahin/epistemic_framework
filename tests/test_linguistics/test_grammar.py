import unittest
from linguistics.sarf_parser import SarfEngine
from linguistics.tokenizer import EpistemicTokenizer
from linguistics.nahiv_ast import NahivDependencyCompiler

class TestGrammarEngine(unittest.TestCase):
    """
    Sarf, Nahiv ve Tokenizer katmanlarındaki İ'lâl, İbdâl ve Terkib
    (Alt-Ağaç) çözümleyicilerini test eden Red-Teaming (Stres) paketi.
    """
    def setUp(self):
        self.sarf = SarfEngine()
        self.tokenizer = EpistemicTokenizer()
        self.nahiv = NahivDependencyCompiler()

    def test_ilal_mutation_ecvef(self):
        """[Faz 10.1] Ecvef (Orta harfi illetli) fiillerde fonolojik geri dönüşüm (qaala -> q-w-l)."""
        morph = self.sarf._derive_morphology("qaala")
        self.assertEqual(morph.root, "qwl", "[İ'LÂL ÇÖKÜŞÜ] Ecvef fiilin illetli harfi (Vav/Ya) çözümlenemedi.")
        self.assertEqual(morph.pattern, "Fa'ala_Ecvef")

    def test_ibdal_assimilation_iftaala(self):
        """[Faz 10.1] İfta'ala babındaki İbdâl (Asimilasyon) restorasyonu (ittasala -> w-s-l)."""
        morph = self.sarf._derive_morphology("ittasala")
        self.assertEqual(morph.root, "wsl", "[İBDÂL ÇÖKÜŞÜ] Asimile olmuş 'w' harfi 't' altından çıkarılamadı.")
        self.assertEqual(morph.pattern, "Ifta'ala_Ibdal")

    def test_clitic_splitting(self):
        """[Faz 10.3] Bitişik yazılan edat ve bağlaçların (wa-, bi-) gövdeden ayrıştırılması."""
        tokens = self.tokenizer.tokenize("waqaala bizeydin")
        expected = ["wa", "qaala", "bi", "zeydin"]
        self.assertEqual(tokens, expected, "[SENTAKS İHLALİ] Clitic Splitting (Ön-ek ayrıştırma) başarısız.")

    def test_izafet_mudaf_resolution(self):
        """[Faz 10.2 & 10.4] İzafet terkibi (Mudaf'ın tenvin düşmesi) ve Nahiv AST bağlantısı."""
        tokens = ["yadu", "allahi"] # Mudaf (-u) ve Mudaf İleyh (-i)
        
        # 1. Sarf Testi (Tenvin düşmesi yamasının doğrulanması)
        lexicon = self.sarf.derive_lexicon(tokens)
        self.assertEqual(lexicon["yadu"].root, "yad")
        self.assertEqual(lexicon["allahi"].root, "allah")
        
        # 2. Nahiv Testi (Alt-Ağaç/Terkib bağlantısı)
        deps = self.nahiv.suggest_dependencies(tokens, lexicon)
        
        # Beklenen: ('yadu', 'allahi', 'Mudaf_MudafIlayh', 'Majrur')
        has_izafet = any(rel == 'Mudaf_MudafIlayh' for amil, mamul, rel, irab in deps)
        self.assertTrue(has_izafet, "[NAHİV ÇÖKÜŞÜ] Terkib-i İzafî (İsim Tamlaması) alt-ağacı (AST) kurulamadı.")

if __name__ == '__main__':
    unittest.main()