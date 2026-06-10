import unittest
from typing import List, Tuple
from linguistics.discourse_state import DiscourseRegister, DenialLevel
from linguistics.contextual_lexicon import ContextualLexicon, LocalOntoLexSemanticClient
from linguistics.ilm_wad_adapter import IlmWadAdapter
from linguistics.sarf_parser import MorphologicalAnalysis
from core.exceptions import ContextPoisoningError

class TestDiscourseIsolation(unittest.TestCase):
    """
    [FAZ 12] Uçtan Uca (E2E) Bipartite DRT, Lexical Poisoning ve Agent-Sealed IR Test Matrisi.
    
    .. pedagojik_anlati::
        Âdâb-ı Bahs simülasyonunda Mu'aradah (Çapraz İtiraz) evresinin donanımsal 
        izolasyon testleri. Sâil'in (itiraz edenin) Mucîb'in (iddia sahibinin) ontolojik 
        hakikatini çalmasını veya bozmasını engelleyen Tahrîr-i Niza' sınırları test edilir.
    """

    def setUp(self):
        self.discourse = DiscourseRegister()
        self.lexicon = ContextualLexicon(semantic_client=LocalOntoLexSemanticClient())
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)

    def test_phantom_bypass_valid_resolution(self):
        """
        Adım 1 Testi: Sâil, Mucîb'in uzayını 'hayalet' (phantom) olarak atlar ve
        kendi mühürlediği veya Base uzayında bulunan doğru referansa (Antecedent) ulaşır.
        """
        self.discourse.set_agent("Mujib")
        self.discourse.push_scope()
        # Mucîb kendi uzayında bir Zeyd tanımlar.
        self.discourse.add_mention("zeyd", "Entity_Zeyd_Ashari", "Ashari", gender="Muzekker", number="Mufred")

        self.discourse.set_agent("Sail")
        self.discourse.push_scope()
        # Sâil Base (Ortak) uzayda bir varlık tanımlar.
        self.discourse.add_mention("racul", "Entity_Man_Base", "Base", gender="Muzekker", number="Mufred")

        # Sâil 'huve' zamirini kullandığında Mucîb'in Zeyd'ini es geçip Base uzayındaki racul'a çarpmalıdır.
        resolved_id = self.discourse.resolve_pronoun("huve", enforcement_namespace="Maturidi")
        self.assertEqual(resolved_id, "Entity_Man_Base", "Phantom Bypass başarısız: Sâil, Mucîb'in uzayını atlayamadı.")

    def test_enforcement_context_poisoning(self):
        """
        Adım 1 Testi: Sâil kasten rakibin uzayını dayatırsa (Enforcement), sistem 
        ContextPoisoningError (Bağlam Zehirlenmesi) fırlatarak motoru kilitler.
        """
        self.discourse.set_agent("Mujib")
        self.discourse.push_scope()
        self.discourse.add_mention("zeyd", "Entity_Zeyd_Ashari", "Ashari", gender="Muzekker", number="Mufred")

        self.discourse.set_agent("Sail")
        self.discourse.push_scope()

        with self.assertRaises(ContextPoisoningError) as context:
            # Sâil kasıtlı olarak Ashari uzayına sızmaya çalışıyor
            self.discourse.resolve_pronoun("huve", enforcement_namespace="Ashari")

        self.assertIn("Bağlam Zehirlenmesi", str(context.exception))
        self.assertIn("kasten rakibin", str(context.exception))
        self.assertIn("Mu'aradah çapraz izolasyonu ihlal edildi", str(context.exception))

    def test_lexical_poisoning_prevention(self):
        """
        Adım 3 Testi: Sâil, Leksikondan kelime çekerken dönen ontolojik ID, daha önce Mucîb 
        tarafından kendi uzayında mühürlenmişse Lexical Poisoning zırhı tetiklenmelidir.
        """
        # Mucîb bir varlığı Ashari uzayında ontolojik belleğe kaydeder.
        self.discourse.set_agent("Mujib")
        self.discourse.push_scope()
        self.discourse.add_mention("ruh", "Entity_Ruh_01", "Ashari")
        
        # Leksikonda bu kelime Ashari'ye aittir
        self.lexicon.register_word("ruh", "Ashari", "Entity_Ruh_01")
        
        # Sâil devreye girer
        self.discourse.set_agent("Sail")
        self.discourse.push_scope()
        
        with self.assertRaises(ContextPoisoningError) as context:
            # Sâil Maturidi uzayındayken 'ruh' kelimesini çözmek ister. Fallback Ashari ID'sini getirirse patlamalıdır.
            self.lexicon.resolve_id("ruh", active_namespace="Maturidi", discourse=self.discourse)

        self.assertIn("Lexical Poisoning", str(context.exception))
        self.assertIn("arka kapı (backdoor) eşdeğerliği engellendi", str(context.exception))

    def test_semantic_ir_agent_seal_propagation(self):
        """
        Adım 2 Testi: FOL (SemanticStatementIR) matrisine aktarım yapılırken 
        'active_agent' mührünün donanımsal olarak Z3 arayüzüne işlenmesi.
        """
        self.discourse.set_agent("Sail")
        self.discourse.push_scope()
        
        # Base uzayda bir kelime kaydı
        self.lexicon.register_word("zeyd", "Base", "Entity_Zeyd")
        
        # Kukla Sarf Verisi
        auto_lexicon = {
            "zeyd": MorphologicalAnalysis(root="zeyd", pattern="fa'l", ontologic_type="Isim_Camid")
        }
        
        dependencies: List[Tuple[str, str, str, str]] = [
            ("Kainun_Virtual", "zeyd", "Mubteda_Haber", "Marfu")
        ]
        
        # IR Üretimi
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