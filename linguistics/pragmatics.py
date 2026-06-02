from typing import List, Dict, Any

class PragmaticsFilter:
    """
    'İlm-i Ma'ânî (Pragmatics) Filtresi.
    Faz 3 - Adım 2: Fıkhî İstinbat (Deontik Mantık) İzolasyon Motoru.
    İnşâî formdaki istifham (soru) edatları reddedilirken, emir (if'al) ve nehiy (yasak)
    kalıpları Deontik Mantık olarak Z3'e girmesi için onaylanır.
    """
    def __init__(self):
        self.inshai_markers = {
            "question": ["hal", "a", "mata", "kayfa", "man", "ma", "eyne"],
            "imperative": ["if'al", "la_taf'al", "ef'al", "li_yaf'al"]
        }

    def analyze_pragmatics(self, tokens: List[str]) -> Dict[str, Any]:
        if not tokens:
            return {"is_valid": False, "type": "Empty"}
        
        first_token = tokens[0].lower()
        
        if first_token in self.inshai_markers["question"]:
            return {"is_valid": False, "type": "Istifham", "message": "Soru cümleleri mantıksal değer taşımaz."}
            
        if first_token in self.inshai_markers["imperative"]:
            is_prohibitive = first_token.startswith("la_")
            return {"is_valid": True, "type": "Deontic", "operator": "Nehiy" if is_prohibitive else "Emir"}
            
        return {"is_valid": True, "type": "Khabari"}
        
    def is_khabari(self, tokens: List[str]) -> bool:
        res = self.analyze_pragmatics(tokens)
        return res["is_valid"]