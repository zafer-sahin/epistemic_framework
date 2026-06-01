import unittest
from linguistics.ilm_wad_adapter import SemanticStatementIR
from schools.maturidi_usul import MaturidiUsul
from schools.salafi_usul import SalafiUsul
# (Diğer importlar repl.py'daki gibi eklenecektir)

class TestDefeasibilityEngine(unittest.TestCase):
    def setUp(self):
        # Orkestratör ve tüm alt bileşenler (l1, l2, l3, adapter) başlatılır.
        pass

    def test_autonomous_tevil_recovery(self):
        """[Faz 3.2] Z3 UNSAT sonrasında orkestratörün Metaphor_Fallback ile kurtarma (SAT) işlemi."""
        # 'Yedullah' tamlaması Eş'ari/Maturidi usulünde literal bağlamda Z3 UNSAT verecektir.
        # Sistem bunu tespit edip, kelimenin 'Kudret' (Metaphor) karşılığını çekip 2. denemede SAT döndürmelidir.
        result = self.orchestrator.process_statement(self.tokens, self.ast, MaturidiUsul(), self.morph)
        self.assertTrue(result.get("tevil_applied"), "[ÇÖKÜŞ] Defeasibility döngüsü tetiklenmedi.")
        self.assertEqual(result["status"], "SAT", "[MANTIK HATASI] Te'vil sonrası Z3 SAT üretemedi.")

    def test_l2_blocked_nodes_dsl(self):
        """[Faz 3.3] Maturidi Usulü'ndeki 'Tekvin' spesifik DSL düğüm blokesi."""
        # İçinde 'Tekvin' ontolojik ID'si barındıran bir IR matrisinin te'vil edilmeye çalışılması durumu
        result = self.orchestrator.process_statement(self.tekvin_tokens, self.tekvin_ast, MaturidiUsul(), self.morph)
        self.assertEqual(result["status"], "REJECTED_BY_USUL", "[OTORİTE İHLALİ] Yasaklı düğüm te'vile uğradı.")
        
    def test_zero_transformation_salafi(self):
        """[Faz 3.3] Selefi Usulü'nün (allow_tevil=False) mutlak literalizm kısıtı."""
        result = self.orchestrator.process_statement(self.tokens, self.ast, SalafiUsul(), self.morph)
        self.assertEqual(result["status"], "NAKZ", "[OTORİTE İHLALİ] Selefi usulünde te'vil (geri çekilme) yapıldı.")