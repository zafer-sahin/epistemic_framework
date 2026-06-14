import unittest
from linguistics.sarf_parser import SarfEngine
from linguistics.tokenizer import EpistemicTokenizer
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister
from linguistics.ilm_wad_adapter import IlmWadAdapter

class TestGrammarEngine(unittest.TestCase):
    """
    Sarf, Nahiv ve Tokenizer katmanlarındaki İ'lâl, İbdâl ve Terkib
    (Alt-Ağaç) çözümleyicilerini test eden Red-Teaming (Stres) paketi.
    [FAZ 1 ENTEGRASYONU]: Gayri Munsarif (Diptotes) i'rab koruması ve sentaktik rol (Meful kayması) testleri eklendi.
    [FAZ 2 ENTEGRASYONU]: Edilgen Fiil (Mebnî lil-Meçhul) ve Nâib Fâil Semantik İntikal testleri eklendi.
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

    def test_diptote_morphological_flag(self):
        """[FAZ 1] Gayri Munsarif kelimelerin morfolojik üreticide (SarfEngine) doğru işaretlenmesi."""
        # 'makkata' kelimesi fetha ile biter (Meful gibi görünür) ancak diptote havuzundadır.
        morph = self.sarf._derive_morphology("makkata")
        self.assertTrue(morph.hpsg.is_diptote, "[MORFOLOJİ ÇÖKÜŞÜ] Gayri Munsarif (Diptote) kelime tespit edilemedi.")
        self.assertEqual(morph.pattern, "Gayri_Munsarif")
        self.assertEqual(morph.root, "makkat")

        # Standart bir Triptote kelimesinin bayrak almadığının doğrulanması
        morph_normal = self.sarf._derive_morphology("zeydan")
        self.assertFalse(morph_normal.hpsg.is_diptote, "[MORFOLOJİ ÇÖKÜŞÜ] Standart kelime yanlışlıkla Diptote işaretlendi.")

    def test_diptote_semantic_shift_prevention(self):
        """[FAZ 1] Gayri Munsarif kelimelerin Nahiv (Sentaks) katmanında yanlışlıkla Meful (Patient) atanmasının engellenmesi."""
        # Cümle: "fî makkata" (Mekke'de). 'makkata' fetha ile bitmesine rağmen harf-i cerden dolayı Majrur olmalıdır.
        tokens = ["fi", "makkata"]
        lexicon = self.sarf.derive_lexicon(tokens)
        deps = self.nahiv.suggest_dependencies(tokens, lexicon)
        
        # Fi harfi kapalı kümedir, AST'de amil-mamul bağı yerine İlm-i Ma'ani katmanında çözülür,
        # Ancak Nahiv katmanının 'makkata'yı otonom olarak 'Meful' (Mansub) ilan etmemesi gerekir.
        is_meful = any(rel == 'Meful' for amil, mamul, rel, irab in deps)
        self.assertFalse(is_meful, "[SEMANTİK KAYMA İHLALİ] Gayri Munsarif kelime (fetha bitişli) yanlışlıkla Meful (Patient) olarak atandı.")

        # İzafet Testi: "rabbu makkata" (Mekke'nin Rabbi). 'makkata' fetha ile bitse de Mudaf_Ilayh olmalıdır.
        tokens_izafet = ["rabbu", "makkata"]
        lexicon_izafet = self.sarf.derive_lexicon(tokens_izafet)
        
        # [FAZ 1 HPSG UYUMU]: İlm-i Nahiv kuralı gereği Özel İsimler (Alem) doğası gereği Ma'rife'dir (Belirli).
        # HPSG matrisinde bu durum tescillenerek Nahiv motorunun İzafet kilidi açılır.
        lexicon_izafet["makkata"].hpsg.is_definite = True
        
        deps_izafet = self.nahiv.suggest_dependencies(tokens_izafet, lexicon_izafet)
        
        has_izafet = any(rel == 'Mudaf_MudafIlayh' and mamul == 'makkata' for amil, mamul, rel, irab in deps_izafet)
        self.assertTrue(has_izafet, "[NAHİV ÇÖKÜŞÜ] Gayri Munsarif kelimenin fetha alması, İzafet (Tamlama) zincirini kopardı.")

    def test_mebni_lil_mechul_semantic_shift_and_virtual_agent(self):
        """
        [FAZ 2 ENTEGRASYONU] Edilgen Fiil (Mebnî lil-Meçhul) E2E Semantik İntikal Testi.
        'Duriba Zeydun' (Zeyd vuruldu) önermesinde Zeyd'in Kripke uzayında eyleyen (Role_Agent) 
        olarak değil, eyleme maruz kalan (Role_Patient) olarak Z3'e aktarıldığını ve failsiz eylem 
        safsatasının önüne geçmek için varoluşsal sanal fail (Exists_Virtual_Agent) kapsülünün 
        üretildiğini doğrular.
        """
        # 1. Ortam Hazırlığı
        lexicon = ContextualLexicon()
        discourse = DiscourseRegister()
        adapter = IlmWadAdapter(lexicon, discourse)
        
        # Sözlüğe manuel kayıt (Mocking Lexicon)
        lexicon.register_word("zeyd", "Base", "Zeyd_Entity")
        lexicon.register_word("drb", "Base", "Fiil_Daraba")

        # 2. Boru Hattı (Pipeline) Çalıştırma
        tokens = self.tokenizer.tokenize("duriba zeydun")
        auto_lexicon = self.sarf.derive_lexicon(tokens)
        deps = self.nahiv.suggest_dependencies(tokens, auto_lexicon)
        
        # 3. İlm-i Vaz' Adaptörü ile Semantik IR Üretimi
        ir_matrix = adapter.generate_ir(tokens, deps, active_namespace="Base", auto_lexicon=auto_lexicon, epoch="Classical")
        
        # 4. Red-Teaming Denetimleri
        # a) Zeyd'in 'Role_Patient' (Edilgen/Meful) rolünü alıp almadığı kontrolü
        has_role_patient = any(
            isinstance(p, tuple) and p[0] == "Role_Patient" and p[1] == "Zeyd_Entity"
            for p in ir_matrix.predicates
        )
        self.assertTrue(has_role_patient, "[SEMANTİK ÇÖKÜŞ] Naib Fail (Zeyd) 'Role_Patient' (Eyleme maruz kalan) olarak Z3'e aktarılamadı.")
        
        # b) Zeyd'in yanlışlıkla 'Role_Agent' (Eyleyen) rolünü ALMADIĞI kontrolü (Semantic Shift Koruması)
        has_role_agent_zeyd = any(
            isinstance(p, tuple) and p[0] == "Role_Agent" and p[1] == "Zeyd_Entity"
            for p in ir_matrix.predicates
        )
        self.assertFalse(has_role_agent_zeyd, "[SEMANTİK KAYMA İHLALİ] Naib Fail (Zeyd) yanlışlıkla eylemi yapan (Role_Agent) olarak işaretlendi!")

        # c) Failsiz Eylem Zırhı: Varoluşsal Sanal Fail (Exists_Virtual_Agent) kapsülünün varlığı
        has_virtual_agent_capsule = any(
            hasattr(p, 'operator') and p.operator == "Exists_Virtual_Agent"
            for p in ir_matrix.predicates
        )
        self.assertTrue(has_virtual_agent_capsule, "[ONTOLOJİK BOŞLUK] Edilgen fiilde failsiz eylem safsatasını önleyen 'Exists_Virtual_Agent' kapsülü bulunamadı.")

if __name__ == '__main__':
    unittest.main()