import re
from typing import List, Tuple
from core.models import BaseOntology

class SyllogismEngine:
    def __init__(self, ontology: BaseOntology):
        self.ontology = ontology

    def construct_syllogism(self, figure: str, mood: str, major_term_id: str, minor_term_id: str, middle_term_id: str) -> Tuple[List[str], str]:
        try:
            mood_data = self.ontology.syllogism_moods[figure][mood]
        except KeyError:
            raise ValueError(f"[UNKNOWN_VARIABLE] Geçersiz veya tanımlanmamış Kıyas Formu: {figure} -> {mood}")

        raw_predicates = mood_data.predicates
        
        if len(raw_predicates) != 3:
            raise ValueError(f"LOGIC_FAILURE_PROBABILITY: HIGH - {mood} modu arite uyuşmazlığı (Beklenen: 3).")

        def substitute_terms(expr: str) -> str:
            # Word Boundary (\b) izolasyonu ile Z3 AST çakışmaları engellenir.
            expr = re.sub(r'\bS\b', minor_term_id, expr)
            expr = re.sub(r'\bM\b', middle_term_id, expr)
            expr = re.sub(r'\bP\b', major_term_id, expr)
            return expr

        premises = [substitute_terms(p) for p in raw_predicates[:2]]
        conclusion = substitute_terms(raw_predicates[2])

        return premises, conclusion