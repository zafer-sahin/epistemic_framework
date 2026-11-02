import re
import unittest

from linguistics.tokenizer import EpistemicTokenizer
from linguistics.sarf_parser import SarfEngine, LocalOntoLexGraphClient
from linguistics.nahiv_ast import NahivDependencyCompiler
from tests.corpus.altin_korpus import BILINEN_EKSIKLER, TOKENIZER, SARF, NAHIV

"""
.. felsefe_notu:: Altın Korpusun Sınanması
    Korpustaki her örnek ayrı bir testtir. `bilinen_eksik` ile işaretli örnekler beklenen hata sayılır;
    düzeltildiklerinde "beklenmeyen başarı" verirler ve işaret korpustan kaldırılmalıdır. Sarf örnekleri
    tokenizer'dan geçmeden doğrudan sarf motoruna, nahiv örnekleri ise bütün boru hattına verilir.
"""

# Korpustaki alan adlarının MorphologicalAnalysis karşılıkları
SARF_ALANLARI = {
    "kok": "root", "tur": "ontologic_type", "cati": "voice", "kalip": "pattern", "zamir": "hidden_pronoun",
    "rol": "thematic_role", "irab": "irab", "sayi": "number", "cins": "gender", "gayri_munsarif": "is_diptote",
}


def _ad(sira: int, girdi: str) -> str:
    return f"test_{sira:02d}_{re.sub(r'[^0-9a-zA-Z]+', '_', girdi).strip('_')}"


def _ekle(sinif: type, sira: int, ornek: dict, govde) -> None:
    govde.__doc__ = f"{ornek['girdi']}: {ornek['kaynak']}"
    if ornek.get("bilinen_eksik"):
        govde = unittest.expectedFailure(govde)
    setattr(sinif, _ad(sira, ornek["girdi"]), govde)


class TestImla(unittest.TestCase):
    """Bitişik yazılan harflerin ayrılması (tokenizer)."""


class TestSarf(unittest.TestCase):
    """Tek kelimenin kök, kalıp, i'râb, sayı ve cins çözümlemesi."""


class TestNahiv(unittest.TestCase):
    """Cümlede âmil-ma'mûl ilişkileri."""


def _imla_testi(ornek: dict):
    def govde(self):
        self.assertEqual(EpistemicTokenizer().tokenize(ornek["girdi"]), ornek["beklenen"])
    return govde


def _sarf_testi(ornek: dict):
    def govde(self):
        cozum = SarfEngine(graph_client=LocalOntoLexGraphClient()).derive_lexicon([ornek["girdi"]])[ornek["girdi"]]
        bulunan = {alan: getattr(cozum, SARF_ALANLARI[alan]) for alan in ornek["beklenen"]}
        self.assertEqual(bulunan, ornek["beklenen"])
    return govde


def _nahiv_testi(ornek: dict):
    def govde(self):
        tokens = EpistemicTokenizer().tokenize(ornek["girdi"])
        lexicon = SarfEngine(graph_client=LocalOntoLexGraphClient()).derive_lexicon(tokens)
        bulunan = {(amil, mamul, rel) for amil, mamul, rel, _ in NahivDependencyCompiler().suggest_dependencies(tokens, lexicon)}
        eksik = [iliski for iliski in ornek.get("icermeli", []) if iliski not in bulunan]
        fazla = [iliski for iliski in ornek.get("icermemeli", []) if iliski in bulunan]
        self.assertEqual((eksik, fazla), ([], []), f"Tokenlar: {tokens} | Bulunan: {sorted(bulunan)}")
    return govde


for _sira, _ornek in enumerate(TOKENIZER, 1):
    _ekle(TestImla, _sira, _ornek, _imla_testi(_ornek))
for _sira, _ornek in enumerate(SARF, 1):
    _ekle(TestSarf, _sira, _ornek, _sarf_testi(_ornek))
for _sira, _ornek in enumerate(NAHIV, 1):
    _ekle(TestNahiv, _sira, _ornek, _nahiv_testi(_ornek))


class TestKorpusButunlugu(unittest.TestCase):
    def test_every_known_gap_is_documented(self):
        """Her eksik işareti tanımlı bir koda ve her örnek bir kaynağa dayanmalı."""
        for ornek in TOKENIZER + SARF + NAHIV:
            with self.subTest(girdi=ornek["girdi"]):
                self.assertTrue(ornek.get("kaynak"))
                if ornek.get("bilinen_eksik"):
                    self.assertIn(ornek["bilinen_eksik"], BILINEN_EKSIKLER)

    def test_sarf_expectations_use_known_fields(self):
        for ornek in SARF:
            with self.subTest(girdi=ornek["girdi"]):
                self.assertLessEqual(set(ornek["beklenen"]), set(SARF_ALANLARI))


if __name__ == "__main__":
    unittest.main()
