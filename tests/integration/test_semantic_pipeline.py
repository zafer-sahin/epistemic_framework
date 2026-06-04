import unittest
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister, DenialLevel
from linguistics.pragmatics import MaaniSpeechActAnalyzer
from linguistics.ilm_wad_adapter import IlmWadAdapter
from core.exceptions import DiachronicViolationError

class TestSemanticPipeline(unittest.TestCase):
    def setUp(self):
        self.lexicon = ContextualLexicon()
        self.discourse = DiscourseRegister()
        self.pragmatics = MaaniSpeechActAnalyzer(self.discourse)
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)

        # [FAZ 1] Epoch parametreleri zorunlu kılındı.
        self.lexicon.register_word("Zeydun", "Base", "Zeyd_Entity", epoch="Classical")
        self.lexicon.register_word("Daraba", "Base", "Fiil_Daraba", epoch="Classical")
        
        self.lexicon.register_word("Istiva", "Salafi", "Istiva_Literal", proposition_type="Kadiyye-i_Hamliyye", epoch="Classical")
        self.lexicon.register_word("Istiva", "Ashari", "Istiva_Metaphor", proposition_type="Kadiyye-i_Hamliyye", epoch="Classical")

    def test_polymorphic_lexicon_resolution(self):
        resolved_base = self.lexicon.resolve_id("Zeydun", "Salafi", epoch="Classical")
        self.assertEqual(resolved_base, "Zeyd_Entity")

        resolved_salafi = self.lexicon.resolve_id("Istiva", "Salafi", epoch="Classical")
        self.assertEqual(resolved_salafi, "Istiva_Literal")

        resolved_ashari = self.lexicon.resolve_id("Istiva", "Ashari", epoch="Classical")
        self.assertEqual(resolved_ashari, "Istiva_Metaphor")

        with self.assertRaises(ValueError):
            self.lexicon.resolve_id("Meçhul", "Base", epoch="Classical")

    def test_diachronic_violation_rejection(self):
        """[FAZ 1] Leksikonun seküler/MSA kelimeleri (Epoch: Modern) Z3 motoruna sızdırmasını engeller."""
        # Sistem Classical beklerken modern kelime kaydı reddedilmelidir.
        with self.assertRaises(DiachronicViolationError):
            self.lexicon.register_word("demokrasi", "Base", "Sekuler_Otorite", epoch="Modern")
            
        # Motorun IR tarafındaki Diachronic savunmasını test etmek için tensöre arkadan zerk edilir
        self.lexicon._tensor["demokrasi"] = {"Modern": {"Base": {"Kadiyye-i_Hamliyye": {"default": "Sekuler_Otorite", "context_triggers": {}}}}}
        
        with self.assertRaises(DiachronicViolationError):
            self.lexicon.resolve_id("demokrasi", "Base", epoch="Classical")
            
        with self.assertRaises(DiachronicViolationError):
            # Adaptör dışarıdan modern kelime işlemeyi tamamen reddetmelidir.
            self.adapter.generate_ir(["demokrasi"], [], "Base", epoch="Modern")

    def test_anaphoric_discourse_binding(self):
        self.discourse.add_mention("Zeydun", "Zeyd_Entity", "Base")
        resolved_id = self.discourse.resolve_pronoun("Huve", enforcement_namespace="Base")
        self.assertEqual(resolved_id, "Zeyd_Entity")
        
        self.discourse.clear_memory()
        with self.assertRaises(ValueError):
            self.discourse.resolve_pronoun("Huve", enforcement_namespace="Base")

    def test_khabari_propositional_isolation(self):
        khabari_tokens = ["Daraba", "Zeydun", "Amran"]
        deps = [("Daraba", "Zeydun", "Fail", "Marfu")]
        self.assertTrue(self.pragmatics.is_khabari(khabari_tokens, deps))
        
        inshai_tokens = ["Hal", "Daraba", "Zeydun"]
        self.assertFalse(self.pragmatics.is_khabari(inshai_tokens, deps))

    def test_muktaza_el_hal_violation(self):
        """[Faz 2] Zihin boş (Khali_al_Zihn) iken tevkîd kullanılması ihlalidir."""
        self.discourse.epistemic_state["Sail"] = DenialLevel.KHALI_AL_ZIHN
        self.discourse.active_agent = "Mujib"
        
        tokens = ["inna", "Zeydun", "Daraba"]
        # 'inna' (Harf_Tevkid) 'Zeydun' ismine modifiye olarak bağlanır
        deps = [("Zeydun", "inna", "Tevkid_Modifier", "None")]
        
        res = self.pragmatics.analyze_pragmatics(tokens, deps)
        self.assertFalse(res["is_valid"], "[İHLAL] Khali_al_Zihn durumunda tevkid kullanımına izin verildi.")
        self.assertEqual(res["type"], "MAANI_VIOLATION")

    def test_istifham_i_inkari_logic(self):
        """[Faz 2] Soru edatı (hal) ve nefy edatı (la) yan yana geldiğinde İstifham-ı İnkârî yakalanmalıdır."""
        tokens = ["hal", "la", "Daraba", "Zeydun"]
        deps = [("Daraba", "Zeydun", "Fail", "Marfu")]
        
        res = self.pragmatics.analyze_pragmatics(tokens, deps)
        self.assertTrue(res["is_valid"], "[İHLAL] İstifham-ı İnkârî mantıksal düzlemden çöpe atıldı.")
        self.assertEqual(res["type"], "Istifham_i_Inkari")
        
        ir_matrix = self.adapter.generate_ir(tokens, deps, "Base", epoch="Classical")
        self.assertEqual(ir_matrix.predicates[0].operator, "Istifham_Inkari", "[ZAFİYET] İstifham-ı İnkârî Z3 FOL operatörüne dönüştürülemedi.")

    def test_semantic_ir_matrix_generation(self):
        tokens = ["Daraba", "Zeydun"]
        dependencies = [("Daraba", "Zeydun", "Fail", "Marfu")]
        
        ir_matrix = self.adapter.generate_ir(tokens, dependencies, active_namespace="Base", epoch="Classical")
        
        self.assertTrue(ir_matrix.is_valid_for_z3)
        self.assertEqual(ir_matrix.active_namespace, "Base")
        
        predicates = ir_matrix.predicates
        self.assertEqual(predicates[0][0], "Rel_Fail")
        self.assertEqual(predicates[0][1], "Fiil_Daraba::Zeyd_Entity")
        
    def test_ast_based_sibak_trigger(self):
        """[Faz 6] İbn Teymiyye Node Relocation'ın AST yapısal doğrulaması."""
        self.lexicon.register_word("yad", "Salafi", "Sifat_Yed_Literal", epoch="Classical")
        self.lexicon.register_word("yad", "Salafi", "Sifat_Yed_Bila_Kayf", proposition_type="Kadiyye-i_Hamliyye", sibak_trigger="allah", epoch="Classical")
        
        # Senaryo 1: Rastgele token yan yanalığı, gramatikal bağ yok (Bila_Kayf Tetiklenmemeli)
        deps_random = [("Daraba", "allahu", "Fail", "Marfu"), ("Daraba", "yad", "Meful", "Mansub")]
        res_random = self.lexicon.resolve_id("yad", "Salafi", dependencies=deps_random, epoch="Classical")
        self.assertEqual(res_random, "Sifat_Yed_Literal", "[İHLAL] Rastgele yan yanalık (False-Positive) AST baypas edilerek düğüm taşıması yaptı.")
        
        # Senaryo 2: Geçerli AST lüzum bağı (Mudaf_MudafIlayh) (Bila_Kayf Tetiklenmeli)
        deps_linked = [("yad", "allahi", "Mudaf_MudafIlayh", "Majrur")]
        res_linked = self.lexicon.resolve_id("yad", "Salafi", dependencies=deps_linked, epoch="Classical")
        self.assertEqual(res_linked, "Sifat_Yed_Bila_Kayf", "[İHLAL] Yapısal AST bağı algılanamadı, hakikat taşınması başarısız oldu.")

if __name__ == '__main__':
    unittest.main()