from typing import List, Tuple, Dict
from pydantic import BaseModel
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.pragmatics import PragmaticsFilter
from linguistics.discourse_state import DiscourseRegister
from linguistics.sarf_parser import MorphologicalAnalysis

class SemanticStatementIR(BaseModel):
    active_namespace: str
    predicates: List[Tuple[str, str, int]] 
    is_valid_for_z3: bool

class IlmWadAdapter:
    def __init__(self, lexicon: ContextualLexicon, discourse: DiscourseRegister):
        self.lexicon = lexicon
        self.discourse = discourse
        self.pragmatics = PragmaticsFilter()

    def generate_ir(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]], active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis] = None) -> SemanticStatementIR:
        if auto_lexicon is None:
            auto_lexicon = {}

        if not self.pragmatics.is_khabari(tokens):
            return SemanticStatementIR(active_namespace=active_namespace, predicates=[], is_valid_for_z3=False)

        ir_predicates = []

        for amil, mamul, rel_type, _ in dependencies:
            amil_id = self._resolve_entity(amil, active_namespace, auto_lexicon)
            mamul_id = self._resolve_entity(mamul, active_namespace, auto_lexicon)
            
            rel_id = f"Rel_{rel_type}"
            ir_predicates.append((rel_id, f"{amil_id}::{mamul_id}", 2))
            
            ir_predicates.append((amil_id, amil_id, 1))
            ir_predicates.append((mamul_id, mamul_id, 1))

        return SemanticStatementIR(active_namespace=active_namespace, predicates=ir_predicates, is_valid_for_z3=True)
        
    def _resolve_entity(self, word: str, active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis]) -> str:
        pronoun_res = self.discourse.resolve_pronoun(word)
        if pronoun_res:
            return pronoun_res
            
        search_key = word
        morph_data = auto_lexicon.get(word)
        if morph_data:
            search_key = morph_data.root

        ontologic_id = self.lexicon.resolve_id(search_key, active_namespace)
        
        if not ontologic_id.startswith("Fiil_") and not ontologic_id.startswith("Harf_"):
            self.discourse.add_mention(word, ontologic_id)
        
        return ontologic_id