import unittest
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister, DenialLevel
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.ilm_wad_adapter import IlmWadAdapter
from linguistics.sarf_parser import MorphologicalAnalysis
from core.exceptions import ContextPoisoningError

class TestLiteratePipeline(unittest.TestCase):
    """
    Faz 8 E2E Entegrasyon ve Bilişsel Yük Yönetimi (Chunking) Regresyon Testi.
    Amacı: Parçalanan (Chunked) private fonksiyonların Z3 Semantic IR matrisini 
    eksiksiz üretip üretmediğini ve Literal Programming adaptasyonunun sistemin 
    deterministik doğasını bozup bozmadığını denetlemektir.
    """
    
    def setUp(self):
        self.lexicon = ContextualLexicon()
        self.discourse = DiscourseRegister()
        self.nahiv = NahivDependencyCompiler()
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)
        
        # Test Uzayı: Selefi (Bila_Kayf) ve Ashari
        self.epoch = "Classical"
        
        self.lexicon.register_word("zeyd", "Base", "Entity_Zeyd_01")
        self.lexicon.register_word("dar", "Base", "Entity_House_01")
        self.lexicon.register_word("darab", "Base", "Fiil_Strike_01")
        
        # Sarf Sözlüğü (Mock) 
        self.auto_lexicon = {
            "inne": MorphologicalAnalysis(original_word="inne", root="inne", pattern="Harf_Inne", ontologic_type="Harf_Inne"),
            "zeyd": MorphologicalAnalysis(original_word="zeyd", root="zeyd", pattern="Alem/Camid_Munevven", ontologic_type="Ism", irab="Mansub", thematic_role=None),
            "fi": MorphologicalAnalysis(original_word="fi", root="fi", pattern="Harf", ontologic_type="Harf_Cer"),
            "el_dar": MorphologicalAnalysis(original_word="el_dar", root="dar", pattern="Alem/Camid_Mudaf", ontologic_type="Ism", irab="Majrur", thematic_role=None),
            "fa": MorphologicalAnalysis(original_word="fa", root="fa", pattern="Harf", ontologic_type="Harf_Atif"),
            "daraba": MorphologicalAnalysis(original_word="daraba", root="darab", pattern="Fa'ala", ontologic_type="Fiil", hidden_pronoun="huve")
        }

    def test_end_to_end_epistemic_and_dynamic_logic(self):
        """
        Senaryo: "inne zeyden fi el_dar fa daraba"
        (Şüphesiz Zeyd evdedir, [bunun üzerine / nedensel olarak] vurdu).
        Beklenen IR: Epistemic_Necessity -> (Zarf-ı Mustakar -> LocatedIn) -> Dynamic_Transition -> Fiil(Fail: huve)
        """
        tokens = ["inne", "zeyd", "fi", "el_dar", "fa", "daraba"]
        
        self.discourse.update_epistemic_state("Sail", DenialLevel.MUNKIR)
        
        ast = self.nahiv.suggest_dependencies(tokens, self.auto_lexicon)
        
        has_inne_amel = any(rel == 'Amel_Inne_Ism' and amil == 'inne' for amil, mamul, rel, _ in ast)
        has_zarf_mustakar = any(rel == 'Muteallak_Mekan' and amil == 'Kainun_Virtual' for amil, mamul, rel, _ in ast)
        has_dynamic_logic = any(rel == 'Rel_Fa_Fuzaiyye' for _, _, rel, _ in ast)
        
        self.assertTrue(has_inne_amel, "AST Hatası: _resolve_inne_scope private metodu çöktü.")
        self.assertTrue(has_zarf_mustakar, "AST Hatası: _resolve_mutaallak_spatial_logic private metodu çöktü.")
        self.assertTrue(has_dynamic_logic, "AST Hatası: _resolve_fa_fuzaiyye private metodu çöktü.")

        ir_result = self.adapter.generate_ir(tokens, ast, "Ashari", self.auto_lexicon, epoch=self.epoch)
        
        self.assertTrue(ir_result.is_valid_for_z3, "Pragmatics Hatası: İstifham veya Muktazâ el-Hâl modülü hatalı filtreleme yaptı.")
        
        ir_str = str(ir_result.predicates)
        
        self.assertIn("Epistemic_Necessity", ir_str, "Adaptör Hatası: _wrap_with_pragmatic_modalities sarmalamayı başaramadı.")
        self.assertIn("LocatedIn", ir_str, "Adaptör Hatası: _resolve_mutaallak_spatial_logic Kripke uzay matrisini üretemedi.")
        self.assertIn("Dynamic_Transition", ir_str, "Adaptör Hatası: _resolve_rabita_and_dynamic_logic nedenselliği (Modus Ponens) kuramadı.")
        
    def test_context_poisoning_isolation(self):
        """
        Senaryo: Mu'aradah çapraz sorgusunda, Mucîb'in mühürlediği bir varlığa dışarıdan (Maturidi) 
        bir namespace dayatılması (Enforcement) durumunda Sistemin anında durdurulması 
        (Fail-Safe / Context Poisoning) test edilir.
        """
        # Mucîb kendi uzayında (Ashari) bir Zeyd yaratır ve mühürler
        self.discourse.set_agent("Mujib")
        self.discourse.push_scope()
        self.discourse.add_mention("zeyd", "Entity_Zeyd_01", "Ashari", gender="Muzekker", number="Mufred")
        
        # [LOGIC FIX]: resolve_pronoun sadece aktif aktörün yığıtında çalışır. 
        # Bu nedenle aktör değiştirmeden, doğrudan yabancı (Maturidi) namespace dayatması 
        # yapılarak _verify_context_sealing bariyeri test edilmelidir.
        with self.assertRaises(ContextPoisoningError) as context:
            self.discourse.resolve_pronoun("huve", enforcement_namespace="Maturidi")
            
        self.assertIn("Bağlam Zehirlenmesi", str(context.exception))
        self.assertIn("çapraz izolasyonu ihlal edildi", str(context.exception))

if __name__ == '__main__':
    unittest.main()