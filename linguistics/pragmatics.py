from typing import List, Dict, Any, Tuple
from linguistics.discourse_state import DiscourseRegister, DenialLevel

class MaaniSpeechActAnalyzer:
    """
    'İlm-i Ma'ânî Söz Edimi ve Muktazâ el-Hâl Analizörü.
    Faz 2 - Adım 2.3: PragmaticsFilter'ın yerine inşa edilmiştir.
    Cümlenin formunu (vurgu/tevkîd) muhatabın epistemik inkâr derecesiyle (Denial Level) çapraz denetler.
    Faz 2 - Adım 2.4: İstifham-ı İnkârî (Reddedici Soru) tespiti.
    """
    def __init__(self, discourse: DiscourseRegister):
        self.discourse = discourse
        self.inshai_markers = {
            "question": ["hal", "a", "mata", "kayfa", "man", "ma", "eyne"],
            "imperative": ["if'al", "la_taf'al", "ef'al", "li_yaf'al"]
        }
        self.nefy_markers = {"illa", "la", "ma", "lam", "lan"}

    def analyze_pragmatics(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]]) -> Dict[str, Any]:
        if not tokens:
            return {"is_valid": False, "type": "Empty"}
        
        first_token = tokens[0].lower()
        
        # 1. İstifham-ı İnkârî ve Normal Soru Kontrolü (Faz 2.4)
        if first_token in self.inshai_markers["question"]:
            has_nefy = any(t.lower() in self.nefy_markers for t in tokens)
            if has_nefy:
                return {
                    "is_valid": True, 
                    "type": "Istifham_i_Inkari", 
                    "message": "İstifham-ı İnkârî tespit edildi. Evrensel/Varoluşsal ret mantığına dönüştürülecek."
                }
            else:
                return {
                    "is_valid": False, 
                    "type": "Istifham_Hakiki", 
                    "message": "Gerçek soru cümleleri (İstifham-ı Hakikî) mantıksal değer taşımaz."
                }
            
        # 2. Deontik Mantık (Emir/Nehiy)
        if first_token in self.inshai_markers["imperative"]:
            is_prohibitive = first_token.startswith("la_")
            return {"is_valid": True, "type": "Deontic", "operator": "Nehiy" if is_prohibitive else "Emir"}
            
        # 3. Muktazâ el-Hâl (Bağlamsal Gereklilik) Denetimi (Faz 2.3)
        tevkid_count = sum(1 for _, _, rel, _ in dependencies if rel == 'Tevkid_Modifier')
        opponent_denial_level = self.discourse.get_opponent_epistemic_state()

        if opponent_denial_level == DenialLevel.KHALI_AL_ZIHN and tevkid_count > 0:
            return {
                "is_valid": False,
                "type": "MAANI_VIOLATION",
                "message": "[ADAB_WARNING] Muktazâ el-Hâl İhlali: Muhatabın zihni boş (Khali_al_Zihn) iken tevkîd (pekiştirme) kullanılamaz."
            }
            
        if opponent_denial_level == DenialLevel.MUNKIR and tevkid_count == 0:
            return {
                "is_valid": False,
                "type": "MAANI_VIOLATION",
                "message": "[ADAB_WARNING] Muktazâ el-Hâl İhlali: Muhatap kesin inkar (Munkir) makamında iken tevkîd (pekiştirme) terk edilemez."
            }
            
        return {"is_valid": True, "type": "Khabari"}
        
    def is_khabari(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]]) -> bool:
        res = self.analyze_pragmatics(tokens, dependencies)
        return res["is_valid"]