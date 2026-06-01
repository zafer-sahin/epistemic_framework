from __future__ import annotations
from typing import List, Tuple, Dict, Union
from pydantic import BaseModel, ConfigDict
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.pragmatics import PragmaticsFilter
from linguistics.discourse_state import DiscourseRegister
from linguistics.sarf_parser import MorphologicalAnalysis

class NestedPredicate(BaseModel):
    """
    Faz 1 - Adım 3: Düz (Flat) tuple yapısını hiyerarşik Kadiyye-i Şartiyye
    kapsamlarına (Lüzumi/İnadi) bağlayan özyineli (recursive) IR düğümü.
    """
    model_config = ConfigDict(extra="forbid")
    operator: str
    args: List[Union[Tuple[str, str, int], 'NestedPredicate']]

NestedPredicate.model_rebuild()

class SemanticStatementIR(BaseModel):
    model_config = ConfigDict(extra="forbid")
    active_namespace: str
    predicates: List[Union[Tuple[str, str, int], NestedPredicate]] 
    is_valid_for_z3: bool

class IlmWadAdapter:
    def __init__(self, lexicon: ContextualLexicon, discourse: DiscourseRegister):
        self.lexicon = lexicon
        self.discourse = discourse
        self.pragmatics = PragmaticsFilter()
        # Transliterasyonlu İslâmî Şart Edatları (Conditional Particles)
        self.conditional_particles = {"in", "iza", "law", "amma"}

    def generate_ir(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]], active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis] = None) -> SemanticStatementIR:
        if auto_lexicon is None:
            auto_lexicon = {}

        if not self.pragmatics.is_khabari(tokens):
            return SemanticStatementIR(active_namespace=active_namespace, predicates=[], is_valid_for_z3=False)

        ir_predicates: List[Union[Tuple[str, str, int], NestedPredicate]] = []
        atomic_predicates: List[Union[Tuple[str, str, int], NestedPredicate]] = []
        
        has_condition = any(t.lower() in self.conditional_particles for t in tokens)

        for amil, mamul, rel_type, _ in dependencies:
            # Şart edatlarını ontolojik varlık çözümlemesinden (resolve_entity) muaf tut
            if amil.lower() in self.conditional_particles or mamul.lower() in self.conditional_particles:
                continue

            amil_id = self._resolve_entity(amil, active_namespace, auto_lexicon)
            mamul_id = self._resolve_entity(mamul, active_namespace, auto_lexicon)
            
            rel_id = f"Rel_{rel_type}"
            atomic_predicates.append((rel_id, f"{amil_id}::{mamul_id}", 2))
            
            atomic_predicates.append((amil_id, amil_id, 1))
            atomic_predicates.append((mamul_id, mamul_id, 1))

        if has_condition:
            # Şart edatı tespit edildiğinde, düz matris "Luzumi" operatörü ile 
            # nested (hiyerarşik) bir şartlı önerme gövdesine hapsedilir.
            # (Faz 4 FSM entegrasyonunda bu düğüm Mukaddem ve Tâli olarak iki alt-ağaca bölünecektir).
            nested_logic = NestedPredicate(
                operator="Luzumi",
                args=atomic_predicates
            )
            ir_predicates.append(nested_logic)
        else:
            ir_predicates.extend(atomic_predicates)

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
        
        # Söylem belleğine sadece ontolojik yük taşıyan isim ve türevleri (Fiil/Harf hariç) atılır
        if not ontologic_id.startswith("Fiil_") and not ontologic_id.startswith("Harf_"):
            self.discourse.add_mention(word, ontologic_id)
        
        return ontologic_id