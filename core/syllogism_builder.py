import re
from typing import List, Tuple
from core.models import BaseOntology

class SyllogismEngine:
    def __init__(self, ontology: BaseOntology):
        self.ontology = ontology

    def construct_syllogism(self, figure: str, mood: str, term_map: dict) -> Tuple[List[str], str]:
        """
        Faz 1 - Adım 2: Statik (S, P, M) arite limiti kaldırılmış, 
        dinamik term_map (Örn: {'S': 'Minor', 'P': 'Major', 'M': 'Middle', 'A': 'Antecedent', 'C': 'Consequent'}) 
        sözlüğü entegre edilmiştir.
        """
        try:
            mood_data = self.ontology.syllogism_moods[figure][mood]
        except KeyError:
            raise ValueError(f"[UNKNOWN_VARIABLE] Geçersiz veya tanımlanmamış Kıyas Formu: {figure} -> {mood}")

        raw_predicates = mood_data.predicates
        
        if len(raw_predicates) < 2:
            raise ValueError(f"LOGIC_FAILURE_PROBABILITY: HIGH - {mood} modu arite uyuşmazlığı (Beklenen en az: 2).")

        def substitute_terms(expr: str) -> str:
            # Word Boundary (\b) izolasyonu ile Z3 AST çakışmaları engellenir.
            for symbol, ontologic_id in term_map.items():
                expr = re.sub(rf'\b{symbol}\b', ontologic_id, expr)
            return expr

        # Son eleman her zaman netice (conclusion), geri kalanlar mukaddime (premise) kabul edilir.
        premises = [substitute_terms(p) for p in raw_predicates[:-1]]
        conclusion = substitute_terms(raw_predicates[-1])

        return premises, conclusion