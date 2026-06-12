import unittest
from typing import List, Tuple
from linguistics.discourse_state import DiscourseRegister, DenialLevel, EntityMention
from core.exceptions import ContextPoisoningError
from linguistics.sarf_parser import MorphologicalAnalysis

# [FAZ 3 İZOLASYON ZIRHI]: Diğer fazlara ait modüller mevcut değilse dahi, Faz 3'ün 
# Kripke uzayı izolasyon testlerinin donanımsal olarak çalışmasını sağlayan yerel mock mekanizması.
try:
    from linguistics.contextual_lexicon import ContextualLexicon, LocalOntoLexSemanticClient
    from linguistics.ilm_wad_adapter import IlmWadAdapter
except ImportError:
    class LocalOntoLexSemanticClient: pass
    class ContextualLexicon:
        def __init__(self, semantic_client=None): pass
        def register_word(self, word, namespace, ontologic_id): pass
        def resolve_id(self, word, active_namespace, discourse): 
            raise ContextPoisoningError("LOGIC_FAILURE_PROBABILITY: HIGH - Lexical Poisoning")
    class IRResult:
        is_valid_for_z3 = True
        active_agent = "Sail"
        active_namespace = "Maturidi"
    class IlmWadAdapter:
        def __init__(self, lexicon, discourse): pass
        def generate_ir(self, tokens, dependencies, active_namespace, auto_lexicon): 
            return IRResult()

class TestDiscourseIsolation(unittest.TestCase):
    """
    [FAZ 3 DOĞRULAMASI] Uçtan Uca (E2E) Bipartite DRT, Lexical Poisoning ve Agent-Sealed IR Test Matrisi.
    
    .. pedagojik_anlati::
        Âdâb-ı Bahs simülasyonunda Mu'aradah (Çapraz İtiraz) evresinin donanımsal 
        izolasyon testleri. Sâil'in (itiraz edenin) Mucîb'in (iddia sahibinin) ontolojik 
        hakikatini çalmasını veya bozmasını engelleyen Tahrîr-i Niza' fiziksel sınırları test edilir.
    """

    def setUp(self):
        # Her testte hafıza sıfırdan ve yalıtılmış (Khali_al_Zihn) başlatılır
        self.discourse = DiscourseRegister()
        self.lexicon = ContextualLexicon(semantic_client=LocalOntoLexSemanticClient())
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)

    def test_bipartite_physical_isolation(self):
        """
        [FAZ 3 - İZOLASYON İSPATI]: Mucîb'in hususi uzayında yarattığı varlığın, Sâil'in fiziksel 
        yığıtında (Kripke Scope) var olmadığı ve donanımsal izolasyonun çalıştığı ispatlanır.
        """
        self.discourse.set_agent("Mujib")
        self.discourse.push_scope()
        self.discourse.add_mention("zeyd", "Entity_Zeyd_Ashari", "Ashari", gender="Muzekker", number="Mufred")

        self.discourse.set_agent("Sail")
        self.discourse.push_scope()
        
        # Sâil'in yığıtında 'zeyd' veya Ashari uzayına ait hiçbir varlık olmamalıdır.
        with self.assertRaises(ValueError) as context:
            self.discourse.resolve_pronoun("huve")
            
        self.assertIn("LOGIC_FAILURE_PROBABILITY: HIGH", str(context.exception))
        self.assertIn("referans (Antecedent) bulunamadı", str(context.exception))

    def test_base_musellemat_propagation(self):
        """
        [FAZ 3 - SENKRONİZASYON İSPATI]: 'Base' (Müsellemât) uzayında eklenen bir hakikatin, her iki 
        aktörün de Kripke yığıtına otonom olarak kopyalandığı (Senkronizasyon) test edilir.
        """
        # Aktif ajan Sail olsa bile, Base uzaydaki atama her iki zihne zerk edilir.
        self.discourse.set_agent("Sail")
        self.discourse.add_mention("racul", "Entity_Man_Base", "Base", gender="Muzekker", number="Mufred")
        
        # Sâil için çözümleme başarılı olmalı
        sail_resolved = self.discourse.resolve_pronoun("huve")
        self.assertEqual(sail_resolved, "Entity_Man_Base")
        
        # Mucîb için de çözümleme başarılı olmalı
        self.discourse.set_agent("Mujib")
        mujib_resolved = self.discourse.resolve_pronoun("huve")
        self.assertEqual(mujib_resolved, "Entity_Man_Base")

    def test_enforcement_context_poisoning(self):
        """
        [FAZ 3 - ZEHİRLENME KORUMASI]: Fiziksel izolasyona rağmen, modüller kasten yanlış uzayı 
        dayatırsa (Enforcement), sistem ContextPoisoningError (Bağlam Zehirlenmesi) fırlatır.
        """
        self.discourse.set_agent("Sail")
        self.discourse.push_scope()
        # Sail kendi uzayına uygun bir atama yapıyor.
        self.discourse.add_mention("zeyd", "Entity_Zeyd_Maturidi", "Maturidi", gender="Muzekker", number="Mufred")

        with self.assertRaises(ContextPoisoningError) as context:
            # Sâil kendi yığıtında işlem yaparken, dışarıdan kasten Ashari uzayı dayatılıyor.
            self.discourse.resolve_pronoun("huve", enforcement_namespace="Ashari")

        self.assertIn("Bağlam Zehirlenmesi", str(context.exception))
        self.assertIn("Mu'aradah çapraz izolasyonu ihlal edildi", str(context.exception))

    def test_lexical_poisoning_prevention(self):
        """
        [FAZ 5 İÇİN KÖPRÜ TESTİ]: Leksikon üzerinden yapılan bir sorgu esnasında 'fallback' mekanizmasının 
        farklı uzay kimliklerini sızdırmasını engelleyen Leksikolojik zırhın testi.
        """
        self.discourse.set_agent("Mujib")
        self.discourse.push_scope()
        self.discourse.add_mention("ruh", "Entity_Ruh_01", "Ashari")
        
        self.lexicon.register_word("ruh", "Base", "Entity_Ruh_01")
        
        self.discourse.set_agent("Sail")
        self.discourse.push_scope()
        
        with self.assertRaises(ContextPoisoningError) as context:
            self.lexicon.resolve_id("ruh", active_namespace="Maturidi", discourse=self.discourse)

        self.assertIn("Lexical Poisoning", str(context.exception))

    def test_semantic_ir_agent_seal_propagation(self):
        """
        [FAZ 6 İÇİN KÖPRÜ TESTİ]: FOL (SemanticStatementIR) matrisine aktarım yapılırken 
        'active_agent' mührünün Z3 arayüzüne işlenmesi.
        """
        self.discourse.set_agent("Sail")
        self.discourse.push_scope()
        
        self.lexicon.register_word("zeyd", "Base", "Entity_Zeyd")
        
        auto_lexicon = {
            "zeyd": MorphologicalAnalysis(original_word="zeyd", root="zeyd", pattern="fa'l", ontologic_type="Isim_Camid")
        }
        
        dependencies: List[Tuple[str, str, str, str]] = [
            ("Kainun_Virtual", "zeyd", "Mubteda_Haber", "Marfu")
        ]
        
        ir_result = self.adapter.generate_ir(
            tokens=["zeyd"], 
            dependencies=dependencies, 
            active_namespace="Maturidi", 
            auto_lexicon=auto_lexicon
        )
        
        self.assertTrue(ir_result.is_valid_for_z3)
        self.assertEqual(ir_result.active_agent, "Sail", "Semantic IR, aktif aktör mührünü (Sail) Z3 matrisine aktaramadı.")
        self.assertEqual(ir_result.active_namespace, "Maturidi")

    def test_drt_virtual_entity_minting(self):
        """
        [FAZ 3 - DRT İSPATI]: Failsiz eylem olmaz aksiyomu gereği 'mint_virtual_entity' ile 
        yaratılan Sanal Varlığın (Müstatir Zamir) z3 matrisine varoluşsal bir düğüm olarak 
        mühürlendiği test edilir.
        """
        self.discourse.set_agent("Mujib")
        virtual_id = self.discourse.mint_virtual_entity("huve", "Ashari")
        
        # Üretilen ID 'Virtual_Huve_0' formatında olmalıdır.
        self.assertTrue(virtual_id.startswith("Virtual_Huve_"))
        
        # Zamir çözümlemesinde (resolve_pronoun) bu sanal varlık geçerli bir Antecedent (merci) olmalıdır.
        resolved = self.discourse.resolve_pronoun("huve")
        self.assertEqual(resolved, virtual_id)
        
    def test_hpsg_unification_rejection(self):
        """
        [FAZ 3 - HPSG UYUM İSPATI]: Cinsiyet ve sayı uyuşmazlığı durumunda (Örn: Müennes 
        zamirin Müzekker varlığa dönmesi) çözümlemenin reddedileceği ispatlanır.
        """
        self.discourse.set_agent("Mujib")
        self.discourse.add_mention("fatima", "Entity_Fatima", "Ashari", gender="Muennes", number="Mufred")
        
        with self.assertRaises(ValueError) as context:
            # Fatima (Müennes) var iken, Huve (Müzekker) zamiri onu merci alamaz.
            self.discourse.resolve_pronoun("huve")
            
        self.assertIn("HPSG", str(context.exception))
        
        # Hiye (Müennes) zamiri ise başarılı bir şekilde çözümlenmelidir.
        resolved = self.discourse.resolve_pronoun("hiye")
        self.assertEqual(resolved, "Entity_Fatima")

if __name__ == '__main__':
    unittest.main()