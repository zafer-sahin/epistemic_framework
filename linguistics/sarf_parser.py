import json
from pathlib import Path
from typing import Dict, List

class SarfEngine:
    """
    Kelimelerin morfolojik yapısını (Kök ve Vezin) analiz ederek
    ontolojik kategorilerini (İsim, Fiil, Harf) deterministik olarak hesaplar.
    """
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.lexicon_db = self._load_db()

    def _load_db(self) -> Dict[str, str]:
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise RuntimeError(f"[ÇÖKÜŞ] Morfolojik Veritabanı bulunamadı: {self.db_path}")

    def derive_lexicon(self, words: List[str]) -> Dict[str, str]:
        """
        Ham kelime listesini alır, veritabanı üzerinden ontolojik türlerini
        çıkartır ve Nahiv motorunun tüketebileceği bir Sözlük (Lexicon) üretir.
        """
        derived_lexicon = {}
        for word in words:
            if word in self.lexicon_db:
                derived_lexicon[word] = self.lexicon_db[word]
            else:
                raise ValueError(f"[SARF HATASI] '{word}' kelimesinin morfolojik kökü (Cezr) bulunamadı.")
        return derived_lexicon