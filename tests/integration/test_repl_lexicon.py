import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

"""
.. felsefe_notu:: REPL Sözlüğü ve Porphyrios Ağacı
    Air-gap, IR'deki her kavramın ortak ontolojide (Porphyrios Ağacı) bulunmasını şart koşar.
    Sözlükte ağaçta olmayan bir kimliğe bağlanan kelime, geçtiği her cümleyi reddettirir.
    Ağaç küllîlerden (cins, nev') oluşur; şahıslar (cüz'î) onun düğümü değildir. Bu yüzden
    'Zeyd', nev'i olan İnsan ile temsil edilir.
"""


def _repl_kur():
    """REPL'i açılış mesajlarını bastırarak kurar."""
    from repl import EpistemicShell
    with redirect_stdout(io.StringIO()):
        return EpistemicShell()


def _kayitli_kimlikler(lexicon) -> set:
    """Sözlük tensöründeki bütün kayıtların ontolojik kimlikleri."""
    kimlikler = set()
    for donemler in lexicon.dump_tensor().values():
        for uzaylar in donemler.values():
            for onerme_turleri in uzaylar.values():
                for kayit in onerme_turleri.values():
                    if kayit["default"]:
                        kimlikler.add(kayit["default"])
                    kimlikler.update(kayit["context_triggers"].values())
    return kimlikler


class TestReplSozlugu(unittest.TestCase):
    def setUp(self):
        self.shell = _repl_kur()

    def test_repl_lexicon_registers_only_ontology_concepts(self):
        """Ağaçta olmayan bir kimliğe bağlanan kelime, geçtiği her cümleyi air-gap'e takar."""
        disarida = sorted(_kayitli_kimlikler(self.shell.lexicon) - self.shell.l1.entity_map.keys())
        self.assertEqual(disarida, [], "REPL sözlüğü ortak ontolojide olmayan kimliklere bağlanıyor.")

    def test_sentence_about_zeyd_becomes_a_claim(self):
        """'nami zeydun' (Zeyd nâmîdir) air-gap'e takılmadan Mucîb'in iddiası olmalı."""
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.shell.onecmd("parse_sentence nami zeydun")
        self.assertIsNotNone(self.shell.last_ir, "'zeyd' içeren cümle REPL'de reddedildi.")
        self.assertIn("Insan", str(self.shell.last_ir.predicates))


if __name__ == "__main__":
    unittest.main()
