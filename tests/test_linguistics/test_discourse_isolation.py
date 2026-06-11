import unittest
from typing import List, Tuple
from linguistics.discourse_state import DiscourseRegister, DenialLevel
from linguistics.contextual_lexicon import ContextualLexicon, LocalOntoLexSemanticClient
from linguistics.ilm_wad_adapter import IlmWadAdapter
from linguistics.sarf_parser import MorphologicalAnalysis
from core.exceptions import ContextPoisoningError

class TestDiscourseIsolation(unittest.TestCase):
    """
    [FAZ 4.1] Uçtan Uca (E2E) Bipartite DRT, Lexical Poisoning ve Agent-Sealed IR Test Matrisi.
    
    .. pedagojik_anlati::
        Âdâb-ı Bahs simülasyonunda Mu'aradah (Çapraz İtiraz) evresinin donanımsal 
        izolasyon testleri. Sâil'in (itiraz edenin) Mucîb'in (iddia sahibinin) ontolojik 
        hakikatini çalmasını veya bozmasını engelleyen Tahrîr-i Niza' fiziksel sınırları test edilir.
    """

    def setUp(self):
        self.discourse = DiscourseRegister()
        self.lexicon = ContextualLexicon(semantic_client=LocalOntoLexSemanticClient())
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)

    def test_bipartite_physical_isolation(self):
        """
        Adım 1 Testi: Mucîb'in hususi uzayında yarattığı varlığın, Sâil'in fiziksel 
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
        Adım 2 Testi: 'Base' (Müsellemât) uzayında eklenen bir hakikatin, her iki 
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
        Adım 3 Testi: Fiziksel izolasyona rağmen, modüller kasten yanlış uzayı 
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
        Adım 4 Testi: Leksikon üzerinden yapılan bir sorgu esnasında 'fallback' mekanizmasının 
        farklı uzay kimliklerini sızdırmasını engelleyen Leksikolojik zırhın testi.
        """
        self.discourse.set_agent("Mujib")
        self.discourse.push_scope()
        self.discourse.add_mention("ruh", "Entity_Ruh_01", "Ashari")
        
        self.lexicon.register_word("ruh", "Base", "Entity_Ruh_01")
        
        self.discourse.set_agent("Sail")
        self.discourse.push_scope()
        
        with self.assertRaises(ContextPoisoningError) as context:
            # Sail Maturidi uzayındayken ruh'u çözmeye çalışır. Lexicon Base üzerinden ID döner.
            # Ancak o ID 'Ashari' olarak diskurda mühürlüdür. IlmWadAdapter'in veya Leksikon'un bunu 
            # yakalayıp zehirlenmeyi önlemesi gerekir.
            # (ContextualLexicon'un resolve_id metodu içerisinde DiscourseRegister kontrolü çağrılır)
            self.lexicon.resolve_id("ruh", active_namespace="Maturidi", discourse=self.discourse)

        self.assertIn("Lexical Poisoning", str(context.exception))

    def test_semantic_ir_agent_seal_propagation(self):
        """
        Adım 5 Testi: FOL (SemanticStatementIR) matrisine aktarım yapılırken 
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

if __name__ == '__main__':
    unittest.main()