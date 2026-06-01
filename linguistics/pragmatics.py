# DOSYA: ./linguistics/pragmatics.py

from typing import List

class PragmaticsFilter:
    """
    'İlm-i Ma'ânî (Pragmatics) Filtresi.
    Cümlelerin Khabarî (Bilgi/Hüküm bildiren) veya İnşâî (Soru/Emir/Temenni)
    olduğunu denetler. Mantık motoru (Z3 SMT) sadece Khabarî cümleleri işleyebilir.
    """
    def __init__(self):
        # Transliterasyon tabanlı İnşâî (Soru ve Emir) edatları/kalıpları
        self.inshai_markers = {
            "question": ["hal", "a", "mata", "kayfa", "man", "ma", "eyne"],
            "imperative_patterns": ["if'al", "la_taf'al"]
        }

    def is_khabari(self, tokens: List[str]) -> bool:
        """
        Token dizisini analiz eder. Eğer inşâî bir alamet varsa False döner.
        """
        if not tokens:
            return False
        
        first_token = tokens[0].lower()
        
        # Soru edatı (İstifham) kontrolü
        if first_token in self.inshai_markers["question"]:
            return False
            
        # Gelecek fazlarda daha karmaşık emir/nehiy (imperative/prohibitive) 
        # kalıpları buraya eklenecektir.
        
        return True