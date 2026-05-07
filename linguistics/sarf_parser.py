import re
from typing import Dict, List, Tuple

class SarfEngine:
    """
    Kelimelerin yapısal formunu (Vezin) Regex matrisleri üzerinden analiz ederek
    ontolojik kategorilerini (İsim, Fiil, Harf) deterministik olarak türeten (Derivation)
    Üretken Morfoloji Motoru. Statik sözlük (Mock DB) safsatasını ortadan kaldırır.
    """
    def __init__(self):
        # Vezin Matrisi: Regex Pattern -> (Vezin Adı, Ontolojik Tür)
        # Arapça transkripsiyonda sesli harf dizilimleri baz alınmıştır.
        self.vezin_matrix = [
            # Fiil Kalıpları
            (re.compile(r'^.a.a.a$'), "Fa'ala", "Fiil"),       # Örn: daraba, kataba, nasara
            (re.compile(r'^ya..i.u$'), "Yaf'ilu", "Fiil"),      # Örn: yadribu, yaktibu
            
            # İsim / Sıfat Kalıpları (Fail/Meful İsimleri)
            (re.compile(r'^.a.i.un$'), "Fâ'ilun", "Ism"),     # Örn: dâribun, kâtibun
            (re.compile(r'^ma..u.un$'), "Maf'ûlun", "Ism"),    # Örn: madrûbun, maktûbun
            
            # Özel İsimler (Alem) ve Diğer İsim Kalıpları
            (re.compile(r'^.*un$'), "Alem/Ism (Marfu)", "Ism"), # Örn: zeydun, reculun
            (re.compile(r'^.*an$'), "Alem/Ism (Mansub)", "Ism"),# Örn: amran, reculen
            (re.compile(r'^.*in$'), "Alem/Ism (Majrur)", "Ism"),# Örn: zeydin, reculin
            
            # Harfler (Edatlar)
            (re.compile(r'^(fi|min|ila|ala)$'), "Harf-i Cer", "Harf")
        ]

    def _derive_word_type(self, word: str) -> str:
        """Tek bir kelimenin türünü Vezin matrisinden geçirerek hesaplar."""
        word_lower = word.lower()
        
        for pattern, vezin_name, ontologic_type in self.vezin_matrix:
            if pattern.match(word_lower):
                return ontologic_type
                
        raise ValueError(f"[SARF HATASI] '{word}' kelimesinin Vezin matrisi ontolojik evrende tanımlı değil.")

    def derive_lexicon(self, words: List[str]) -> Dict[str, str]:
        """
        Ham kelime listesini alır, Vezin matrisi üzerinden ontolojik türlerini
        üretir ve Nahiv motorunun tüketebileceği bir Sözlük (Lexicon) yaratır.
        """
        derived_lexicon = {}
        for word in words:
            derived_lexicon[word] = self._derive_word_type(word)
        return derived_lexicon