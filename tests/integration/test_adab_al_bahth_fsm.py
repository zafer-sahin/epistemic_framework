import unittest
from schools.taftazani.adab_al_bahth import AdabAlBahthEngine
from schools.ashari_usul import AshariUsul
from schools.salafi_usul import SalafiUsul

class TestDialecticsFSM(unittest.TestCase):
    def setUp(self):
        # Motor init işlemleri
        pass

    def test_fsm_sequential_integrity(self):
        """[Faz 4.2] FSM'nin AWAITING_CLAIM -> AWAITING_EVIDENCE -> AWAITING_ATTACK sıralaması ihlali koruması."""
        engine = AdabAlBahthEngine(self.solver, self.discourse)
        
        # İddia yokken delil sunulamaz
        with self.assertRaises(ValueError):
            engine.submit_evidence(["Forall([x], Implies(S(x), M(x)))"])
            
        engine.submit_claim("Forall([x], Implies(S(x), P(x)))")
        self.assertEqual(engine.current_state, "AWAITING_EVIDENCE", "FSM durum geçişi başarısız.")

    def test_cross_school_muaradah_stalemate(self):
        """[Faz 4.3] Çapraz Usûl (Muaradah) Z3 Push/Pop izolasyonu."""
        # Mucib (Eş'ari) kendi uzayında SAT olan bir önerme üretir.
        # Sail (Selefi), kendi uzayında SAT olan zıt bir önerme üretir.
        # Orchestrator.execute_cross_school_muaradah bu iki IR matrisini Z3 üzerinde çarpıştırmalıdır.
        result = self.orchestrator.execute_cross_school_muaradah(
            mujib_ir, AshariUsul(), sail_ir, SalafiUsul()
        )
        self.assertEqual(result["status"], "MUARADAH_SUCCESS", "[DİYALEKTİK ÇÖKÜŞ] Çapraz ekol çarpışması Stalemate (UNSAT) yaratamadı.")