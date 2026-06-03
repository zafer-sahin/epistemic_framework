import unittest
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister, DenialLevel
from linguistics.pragmatics import MaaniSpeechActAnalyzer
from linguistics.ilm_wad_adapter import IlmWadAdapter

class TestSemanticPipeline(unittest.TestCase):
    def setUp(self):
        self.lexicon = ContextualLexicon()
        self.discourse = DiscourseRegister()
        self.pragmatics = MaaniSpeechActAnalyzer(self.discourse)
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)

        self.lexicon.register_word("Zeydun", "Base", "Zeyd_Entity")
        self.lexicon.register_word("Daraba", "Base", "Fiil_Daraba")
        
        self.lexicon.register_word("Istiva", "Salafi", "Istiva_Literal", proposition_type="Kadiyye-i_Hamliyye")
        self.lexicon.register_word("Istiva", "Ashari", "Istiva_Metaphor", proposition_type="Kadiyye-i_Hamliyye")

    def test_polymorphic_lexicon_resolution(self):
        resolved_base = self.lexicon.resolve_id("Zeydun", "Salafi")
        self.assertEqual(resolved_base, "Zeyd_Entity")

        resolved_salafi = self.lexicon.resolve_id("Istiva", "Salafi")
        self.assertEqual(resolved_salafi, "Istiva_Literal")

        resolved_ashari = self.lexicon.resolve_id("Istiva", "Ashari")
        self.assertEqual(resolved_ashari, "Istiva_Metaphor")

        with self.assertRaises(ValueError):
            self.lexicon.resolve_id("Meçhul", "Base")

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
        
        ir_matrix = self.adapter.generate_ir(tokens, deps, "Base")
        self.assertEqual(ir_matrix.predicates[0].operator, "Istifham_Inkari", "[ZAFİYET] İstifham-ı İnkârî Z3 FOL operatörüne dönüştürülemedi.")

    def test_semantic_ir_matrix_generation(self):
        tokens = ["Daraba", "Zeydun"]
        dependencies = [("Daraba", "Zeydun", "Fail", "Marfu")]
        
        ir_matrix = self.adapter.generate_ir(tokens, dependencies, active_namespace="Base")
        
        self.assertTrue(ir_matrix.is_valid_for_z3)
        self.assertEqual(ir_matrix.active_namespace, "Base")
        
        predicates = ir_matrix.predicates
        self.assertEqual(predicates[0][0], "Rel_Fail")
        self.assertEqual(predicates[0][1], "Fiil_Daraba::Zeyd_Entity")

if __name__ == '__main__':
    unittest.main()