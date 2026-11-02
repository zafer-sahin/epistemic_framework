import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

"""
.. felsefe_notu:: Mucîb'in İddiası
    Mu'ârazada Mucîb'i, kendi usûlünün tutarlı bulduğu okuma temsil eder: te'vil uygulandıysa
    te'vil sonrası okuma. Mucîb'in kendi ekolünün reddettiği bir cümle savunulacak bir iddia değildir.
"""


def _repl_kur():
    """REPL'i açılış mesajlarını bastırarak kurar."""
    from repl import EpistemicShell
    with redirect_stdout(io.StringIO()):
        return EpistemicShell()


class TestReplMucibIddiasi(unittest.TestCase):
    def setUp(self):
        self.shell = _repl_kur()

    def _komut(self, satir: str) -> None:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.shell.onecmd(satir)

    def test_mujib_claim_is_the_tevil_reading(self):
        self._komut("parse_sentence yadu allahi")
        okuma = str(self.shell.last_ir.predicates if self.shell.last_ir else None)
        self.assertIn("Kudret", okuma, "Mucîb'in iddiası Eş'arî te'vil sonrası okuma olmalı.")
        self.assertNotIn("Sifat_Yed_Literal", okuma, "Mucîb, usûlünün te'vil ederek bıraktığı literal okumayla temsil edildi.")

    def test_sentence_rejected_by_mujibs_own_school_is_not_a_claim(self):
        self._komut("set_usul maturidi")
        self._komut("parse_sentence tekvinu allahi")
        self.assertIsNone(self.shell.last_ir, "Mucîb'in kendi usûlünün reddettiği cümle, mu'ârazada iddia olarak kullanılabiliyor.")

    def test_failed_sentence_clears_previous_claim(self):
        self._komut("parse_sentence yadu allahi")
        self._komut("parse_sentence demokrasi allahi")
        self.assertIsNone(self.shell.last_ir, "Değerlendirilemeyen yeni cümleden sonra önceki cümlenin iddiası hâlâ aktif.")


if __name__ == "__main__":
    unittest.main()
