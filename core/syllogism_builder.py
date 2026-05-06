from typing import List, Tuple
from core.models import BaseOntology

class SyllogismEngine:
    """
    JSON ontolojisindeki soyut kıyas şablonlarını (Örn: M-P, S-M),
    somut ontolojik terimler (Örn: Rationale, Corpus) ile eşleştirerek
    Z3 AST derleyicisi için kapalı formüller (Closed Formulas) üreten motor.
    """
    def __init__(self, ontology: BaseOntology):
        self.ontology = ontology

    def construct_syllogism(self, figure: str, mood: str, major_term: str, minor_term: str, middle_term: str) -> Tuple[List[str], str]:
        """
        Belirtilen figür ve moda göre Z3 için string kısıtları dinamik olarak üretir.
        
        Parametreler:
        - figure: JSON'daki Kıyas Şekli (Örn: "Figure_1")
        - mood: Kıyas Modu (Örn: "Barbara")
        - major_term: Hadd-i Ekber / P (Örn: "Corpus")
        - minor_term: Hadd-i Asgar / S (Örn: "Rationale")
        - middle_term: Hadd-i Evsat / M (Örn: "Vivens")
        """
        try:
            mood_data = self.ontology.syllogism_moods[figure][mood]
        except KeyError:
            raise ValueError(f"Geçersiz veya tanımlanmamış Kıyas Formu: {figure} -> {mood}")

        raw_predicates = mood_data.predicates
        
        # Aristoteles tasımında mutlak kural: 2 öncül (Premise) ve 1 sonuç (Conclusion).
        if len(raw_predicates) != 3:
            raise ValueError(f"Mantıksal anomali: {mood} modu tam olarak 3 predikat içermelidir.")

        premises_raw = raw_predicates[:2]
        conclusion_raw = raw_predicates[2]

        # AST Çeviricinin (Z3ExpressionBuilder) hata yapmaması için sadece fonksiyon çağrılarını değiştir.
        # Regex kullanmamak için güvenli ve spesifik değiştirme stratejisi:
        def substitute_terms(expr: str) -> str:
            return expr.replace("S(x)", f"{minor_term}(x)") \
                       .replace("M(x)", f"{middle_term}(x)") \
                       .replace("P(x)", f"{major_term}(x)")

        premises = [substitute_terms(p) for p in premises_raw]
        conclusion = substitute_terms(conclusion_raw)

        return premises, conclusion