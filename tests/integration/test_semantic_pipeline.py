import unittest
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister
from linguistics.pragmatics import PragmaticsFilter
from linguistics.ilm_wad_adapter import IlmWadAdapter

class TestSemanticPipeline(unittest.TestCase):
    def setUp(self):
        self.lexicon = ContextualLexicon()
        self.discourse = DiscourseRegister()
        self.pragmatics = PragmaticsFilter()
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)

        self.lexicon.register_word("Zeydun", "Base", "Zeyd_Entity")
        self.lexicon.register_word("Daraba", "Base", "Fiil_Daraba")
        
        # [LOGIC FIX]: 3D Leksikon imza uyuşmazlığı çözüldü
        self.lexicon.register_word("Istiva", "Salafi", "Istiva_Literal", proposition_type="Kadiyye-i_Hamliyye")
        self.lexicon.register_word("Istiva", "Ashari", "Istiva_Metaphor", proposition_type="Kadiyye-i_Hamliyye")

    def test_polymorphic_lexicon_resolution(self):
        """[BRQ-02] Polimorfik isim alanı ve kalıtım (fallback) doğrulaması."""
        resolved_base = self.lexicon.resolve_id("Zeydun", "Salafi")
        self.assertEqual(resolved_base, "Zeyd_Entity")

        resolved_salafi = self.lexicon.resolve_id("Istiva", "Salafi")
        self.assertEqual(resolved_salafi, "Istiva_Literal")

        resolved_ashari = self.lexicon.resolve_id("Istiva", "Ashari")
        self.assertEqual(resolved_ashari, "Istiva_Metaphor")

        with self.assertRaises(ValueError):
            self.lexicon.resolve_id("Meçhul", "Base")

    def test_anaphoric_discourse_binding(self):
        """[BRQ-04] Söylem belleği ve zamir (Anafora) çözümlemesi doğrulaması."""
        self.discourse.add_mention("Zeydun", "Zeyd_Entity")
        
        resolved_id = self.discourse.resolve_pronoun("Huve")
        self.assertEqual(resolved_id, "Zeyd_Entity")
        
        self.assertIsNone(self.discourse.resolve_pronoun("Kalem"))
        
        self.discourse.clear_memory()
        with self.assertRaises(ValueError):
            self.discourse.resolve_pronoun("Huve")

    def test_khabari_propositional_isolation(self):
        khabari_tokens = ["Daraba", "Zeydun", "Amran"]
        self.assertTrue(self.pragmatics.is_khabari(khabari_tokens))
        
        inshai_tokens = ["Hal", "Daraba", "Zeydun"]
        self.assertFalse(self.pragmatics.is_khabari(inshai_tokens))

    def test_semantic_ir_matrix_generation(self):
        tokens = ["Daraba", "Zeydun"]
        dependencies = [("Daraba", "Zeydun", "Fail", "Marfu")]
        
        ir_matrix = self.adapter.generate_ir(tokens, dependencies, active_namespace="Base")
        
        self.assertTrue(ir_matrix.is_valid_for_z3)
        self.assertEqual(ir_matrix.active_namespace, "Base")
        
        predicates = ir_matrix.predicates
        self.assertEqual(len(predicates), 3)
        
        self.assertEqual(predicates[0][0], "Rel_Fail")
        # [LOGIC FIX]: '_' yerine '::' separasyonu ile test uyumlandırıldı
        self.assertEqual(predicates[0][1], "Fiil_Daraba::Zeyd_Entity")

    def test_anaphoric_ir_injection(self):
        self.discourse.add_mention("Zeydun", "Zeyd_Entity")
        
        tokens = ["Daraba", "Huve"]
        dependencies = [("Daraba", "Huve", "Fail", "Marfu")]
        
        ir_matrix = self.adapter.generate_ir(tokens, dependencies, active_namespace="Base")
        
        predicates = ir_matrix.predicates
        # [LOGIC FIX]: '_' yerine '::' separasyonu ile test uyumlandırıldı
        self.assertEqual(predicates[0][1], "Fiil_Daraba::Zeyd_Entity")

if __name__ == '__main__':
    unittest.main()