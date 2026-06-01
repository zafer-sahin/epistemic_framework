# DOSYA: ./tests/integration/test_semantic_pipeline.py

import unittest
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister
from linguistics.pragmatics import PragmaticsFilter
from linguistics.ilm_wad_adapter import IlmWadAdapter

class TestSemanticPipeline(unittest.TestCase):
    """
    Faz 1 ve Faz 2 bileşenlerinin (Polimorfik İsim Alanları, Söylem Belleği,
    Pragmatik Filtre ve Semantik IR Üretimi) entegrasyon testlerini içerir.
    """

    def setUp(self):
        """Her testten önce izole test ortamını (fixtures) sıfırla ve hazırla."""
        self.lexicon = ContextualLexicon()
        self.discourse = DiscourseRegister()
        self.pragmatics = PragmaticsFilter()
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)

        # Temel ontolojik matrisin enjeksiyonu
        self.lexicon.register_word("Zeydun", "Base", "Zeyd_Entity")
        self.lexicon.register_word("Daraba", "Base", "Fiil_Daraba")
        
        # Teolojik Polimorfizm enjeksiyonu
        self.lexicon.register_word("Istiva", "Salafi", "Istiva_Literal")
        self.lexicon.register_word("Istiva", "Ashari", "Istiva_Metaphor")

    def test_polymorphic_lexicon_resolution(self):
        """[Faz 3.1] Önermesel 3D Leksikon Tensörü Doğrulaması."""
        # Setup'ta proposition_type spesifik kayıt yapılmalı
        self.lexicon.register_word("Istiva", "Ashari", "Istiva_Literal", proposition_type="Kadiyye-i_Sartiyye")
        self.lexicon.register_word("Istiva", "Ashari", "Istiva_Metaphor", proposition_type="Kadiyye-i_Hamliyye")

        # Şartlı önermede literal, kategorik önermede mecaz dönmeli
        res_sart = self.lexicon.resolve_id("Istiva", "Ashari", proposition_type="Kadiyye-i_Sartiyye")
        self.assertEqual(res_sart, "Istiva_Literal", "Şartlı önerme bağlamı koptu.")
        
        res_haml = self.lexicon.resolve_id("Istiva", "Ashari", proposition_type="Kadiyye-i_Hamliyye")
        self.assertEqual(res_haml, "Istiva_Metaphor", "Kategorik önerme bağlamı koptu.")

    def test_anaphoric_discourse_binding(self):
        """[Faz 4.1] Çok-Aktörlü (Sail/Mujib) Söylem Belleği İzolasyonu."""
        self.discourse.set_agent("Mujib")
        self.discourse.add_mention("Zeydun", "Zeyd_Entity")
        
        # Mucib kendi referansını okuyabilmeli
        self.assertEqual(self.discourse.resolve_pronoun("Huve"), "Zeyd_Entity")
        
        # Sail'in yığıtı boş olmalı ve Mucib'in zamirlerine izinsiz erişememeli
        self.discourse.set_agent("Sail")
        with self.assertRaises(ValueError):
            self.discourse.resolve_pronoun("Huve")

    def test_khabari_propositional_isolation(self):
        """[BRQ-03] 'İlm-i Ma'ânî (Pragmatics) filtresi doğrulaması."""
        khabari_tokens = ["Daraba", "Zeydun", "Amran"]
        self.assertTrue(self.pragmatics.is_khabari(khabari_tokens), "Khabarî önerme reddedildi.")
        
        inshai_tokens = ["Hal", "Daraba", "Zeydun"]
        self.assertFalse(self.pragmatics.is_khabari(inshai_tokens), "İnşâî dizilim sisteme sızdı.")

    def test_semantic_ir_matrix_generation(self):
        """[BRQ-03] 'İlm-i Vaz Adaptörünün Z3 öncesi Sentaktik-Semantik IR üretim doğrulaması."""
        tokens = ["Daraba", "Zeydun"]
        dependencies = [("Daraba", "Zeydun", "Fail", "Marfu")]
        
        ir_matrix = self.adapter.generate_ir(tokens, dependencies, active_namespace="Base")
        
        self.assertTrue(ir_matrix.is_valid_for_z3, "IR Matrisi geçersiz işaretlendi.")
        self.assertEqual(ir_matrix.active_namespace, "Base", "İsim alanı IR matrisine taşınamadı.")
        
        # Predicate Arite ve İlişki Kontrolü
        predicates = ir_matrix.predicates
        self.assertEqual(len(predicates), 3, "Eksik veya fazla arite yüklemesi.")
        
        # Beklenen: [('Rel_Fail', 'Fiil_Daraba_Zeyd_Entity', 2), ('Fiil_Daraba', 'Fiil_Daraba', 1), ('Zeyd_Entity', 'Zeyd_Entity', 1)]
        self.assertEqual(predicates[0][0], "Rel_Fail", "İlişkisel (N-Ary) operatör kökünü kaybetti.")
        self.assertEqual(predicates[0][1], "Fiil_Daraba_Zeyd_Entity", "Amil-Ma'mul ilişkisel ID'si hatalı oluşturuldu.")

    def test_anaphoric_ir_injection(self):
        """Sentaktik ağaca söylem belleği (Zamir) entegrasyonu doğrulaması."""
        # Geçmiş bağlama bir varlık ekle
        self.discourse.add_mention("Zeydun", "Zeyd_Entity")
        
        tokens = ["Daraba", "Huve"]
        dependencies = [("Daraba", "Huve", "Fail", "Marfu")]
        
        ir_matrix = self.adapter.generate_ir(tokens, dependencies, active_namespace="Base")
        
        # 'Huve' token'ının IR matrisinde doğrudan 'Zeyd_Entity' olarak derlenmesi gerekir
        predicates = ir_matrix.predicates
        self.assertEqual(predicates[0][1], "Fiil_Daraba_Zeyd_Entity", "Zamir, IR matrisine ontolojik kimliğiyle zerk edilemedi.")

if __name__ == '__main__':
    unittest.main()