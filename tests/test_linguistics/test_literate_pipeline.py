import unittest
from linguistics.contextual_lexicon import ContextualLexicon, LocalOntoLexSemanticClient
from linguistics.discourse_state import DiscourseRegister, DenialLevel
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.ilm_wad_adapter import IlmWadAdapter
from linguistics.sarf_parser import SarfEngine, LocalOntoLexGraphClient
from core.exceptions import ContextPoisoningError

class TestLiteratePipeline(unittest.TestCase):
    """
    Faz 9 ve Faz 10 E2E Entegrasyon, Bilişsel Yük Yönetimi ve OntoLex Geçişi Regresyon Testi.
    Amacı: 
    1. (Faz 9) Parçalanan private fonksiyonların Z3 Semantic IR matrisini eksiksiz üretmesi.
    2. (Faz 10) OntoLex graf istemcisinin Sarf (Morfoloji) kurallarını dışarıdan hatasız sağlaması.
    3. (Faz 10) Gayri Munsarif (Diptote) kelimelerin Nahiv motorunda SMT çökmesini engellemesi.
    4. (Faz 10) İhtilafsız Base kelimelerin SemanticClient (RDF) üzerinden otonom çözümlenmesi (Fallback).
    """
    
    def setUp(self):
        # [FAZ 10] Dışsal OntoLex Graf ve Semantik İstemcileri (Mock yerine gerçek simülatörler)
        self.semantic_client = LocalOntoLexSemanticClient()
        self.graph_client = LocalOntoLexGraphClient()
        
        # Bağımlılık Enjeksiyonu (Dependency Injection)
        self.lexicon = ContextualLexicon(semantic_client=self.semantic_client)
        self.sarf = SarfEngine(graph_client=self.graph_client)
        
        self.discourse = DiscourseRegister()
        self.nahiv = NahivDependencyCompiler()
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)
        
        self.epoch = "Classical"

    def test_end_to_end_epistemic_and_dynamic_logic(self):
        """
        Senaryo: "inne zeyden fi el_dar fa daraba"
        Beklenen IR: Epistemic_Necessity -> (Zarf-ı Mustakar -> LocatedIn) -> Dynamic_Transition -> Fiil(Fail: huve)
        """
        tokens = ["inne", "zeyd", "fi", "el_dar", "fa", "daraba"]
        
        # [FAZ 10] Sarf motoru OntoLex grafından verileri çeker
        morph_lexicon = self.sarf.derive_lexicon(tokens)
        
        self.discourse.update_epistemic_state("Sail", DenialLevel.MUNKIR)
        
        ast = self.nahiv.suggest_dependencies(tokens, morph_lexicon)
        
        has_inne_amel = any(rel == 'Amel_Inne_Ism' and amil == 'inne' for amil, mamul, rel, _ in ast)
        has_zarf_mustakar = any(rel == 'Muteallak_Mekan' and amil == 'Kainun_Virtual' for amil, mamul, rel, _ in ast)
        has_dynamic_logic = any(rel == 'Rel_Fa_Fuzaiyye' for _, _, rel, _ in ast)
        
        self.assertTrue(has_inne_amel, "AST Hatası: _resolve_inne_scope private metodu çöktü.")
        self.assertTrue(has_zarf_mustakar, "AST Hatası: _resolve_mutaallak_spatial_logic private metodu çöktü.")
        self.assertTrue(has_dynamic_logic, "AST Hatası: _resolve_fa_fuzaiyye private metodu çöktü.")

        ir_result = self.adapter.generate_ir(tokens, ast, "Ashari", morph_lexicon, epoch=self.epoch)
        
        self.assertTrue(ir_result.is_valid_for_z3, "Pragmatics Hatası: İstifham veya Muktazâ el-Hâl modülü hatalı filtreleme yaptı.")
        
        ir_str = str(ir_result.predicates)
        
        self.assertIn("Epistemic_Necessity", ir_str, "Adaptör Hatası: _wrap_with_pragmatic_modalities sarmalamayı başaramadı.")
        self.assertIn("LocatedIn", ir_str, "Adaptör Hatası: _resolve_mutaallak_spatial_logic Kripke uzay matrisini üretemedi.")
        self.assertIn("Dynamic_Transition", ir_str, "Adaptör Hatası: _resolve_rabita_and_dynamic_logic nedenselliği kuramadı.")
        
    def test_gayri_munsarif_diptote_semantic_shift_prevention(self):
        """
        [FAZ 10 E2E BARIYER TESTİ]
        Senaryo: "fi ahmed" (Ahmed'in içinde / Ahmed alanında).
        Ahmed kelimesi vezn-i fiil ve alem illetlerinden dolayı Gayri Munsarif'tir (Diptote). 
        Harf-i cer ("fi") gelmesine rağmen son harekesi fetha (-a) kalır.
        Sarf motoru, dışsal OntoLex grafını tarayarak "is_diptote=True" bilgisini Nahiv motoruna bildirmelidir.
        Nahiv motoru sondaki "a" sesine aldanıp kelimeyi "Mansub" (Nesne) YAPMAMALI, 
        cer durumunu koruyarak SMT tarafındaki Agent/Patient çökmesini engellemelidir.
        """
        tokens = ["fi", "ahmed"]
        morph_lexicon = self.sarf.derive_lexicon(tokens)
        
        self.assertTrue(morph_lexicon["ahmed"].is_diptote, "OntoLex Hatası: İlleteyn analizi Gayri Munsarif düğümünü bulamadı.")
        
        ast = self.nahiv.suggest_dependencies(tokens, morph_lexicon)
        
        # Nahiv motorunun fetha (-a) override kuralını işletip işletmediği test edilir
        is_correctly_majrur = any(
            amil == 'fi' and mamul == 'ahmed' and rel == 'Mecrur_Diptote_Override' 
            for amil, mamul, rel, _ in ast
        )
        
        # LOGIC_FAILURE barikatı: Eğer Nahiv motoru bunu Mansub zannederse SMT patlar.
        self.assertTrue(is_correctly_majrur, "LOGIC_FAILURE: Nahiv motoru Gayri Munsarif (Diptote) override işlemini yapamadı. Z3 Semantic Shift riski: YÜKSEK.")

    def test_ontolex_semantic_fallback_resolution(self):
        """
        [FAZ 10] Otonom Semantik Graf Çözümlemesi.
        Senaryo: "zeydun daribun"
        ContextualLexicon içinde "zeydun" veya "daribun" için açık bir register_word kaydı YOKTUR.
        Sistemin çökmek yerine, IOntoLexSemanticClient üzerinden Base ontology ID'lerini (Insan, Bats)
        otonom olarak çekmesi (Fallback) test edilir.
        """
        tokens = ["zeydun", "daribun"]
        morph_lexicon = self.sarf.derive_lexicon(tokens)
        ast = self.nahiv.suggest_dependencies(tokens, morph_lexicon)
        
        # Sözlüğün yerel tensörü tamamen boş olduğunu kanıtla
        self.assertNotIn("zeydun", self.lexicon._tensor, "Yerel tensörde kayıt olmamalıdır, graf kullanılmalıdır.")
        self.assertNotIn("daribun", self.lexicon._tensor, "Yerel tensörde kayıt olmamalıdır, graf kullanılmalıdır.")
        
        ir_result = self.adapter.generate_ir(tokens, ast, "Base", morph_lexicon, epoch=self.epoch)
        ir_str = str(ir_result.predicates)
        
        self.assertIn("Insan", ir_str, "OntoLex Semantic Fallback Hatası: 'zeydun' düğümü RDF üzerinden çözülemedi.")
        self.assertIn("Bats", ir_str, "OntoLex Semantic Fallback Hatası: 'daribun' düğümü RDF üzerinden çözülemedi.")

    def test_context_poisoning_isolation(self):
        """
        Senaryo: Mu'aradah çapraz sorgusunda, Mucîb'in mühürlediği bir varlığa dışarıdan 
        bir namespace dayatılması (Enforcement) durumunda Sistemin anında durdurulması.
        """
        self.discourse.set_agent("Mujib")
        self.discourse.push_scope()
        self.discourse.add_mention("zeyd", "Entity_Zeyd_01", "Ashari", gender="Muzekker", number="Mufred")
        
        with self.assertRaises(ContextPoisoningError) as context:
            self.discourse.resolve_pronoun("huve", enforcement_namespace="Maturidi")
            
        self.assertIn("Bağlam Zehirlenmesi", str(context.exception))
        self.assertIn("çapraz izolasyonu ihlal edildi", str(context.exception))

if __name__ == '__main__':
    unittest.main()