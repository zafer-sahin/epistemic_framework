from __future__ import annotations
from typing import List, Tuple, Dict, Union, Optional
from pydantic import BaseModel, ConfigDict
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.pragmatics import PragmaticsFilter
from linguistics.discourse_state import DiscourseRegister
from linguistics.sarf_parser import MorphologicalAnalysis

class NestedPredicate(BaseModel):
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
        self.luzumi_particles = {"in", "iza", "law", "amma"}
        self.inadi_particles = {"imma", "aw", "ya"} 
        self.current_tevil_targets: List[str] = []

    def generate_ir(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]], active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis] = None, tevil_fallback_nodes: List[str] = None, proposition_type: str = "Kadiyye-i_Hamliyye") -> SemanticStatementIR:
        if auto_lexicon is None: auto_lexicon = {}
        if tevil_fallback_nodes is None: tevil_fallback_nodes = []
        
        self.current_tevil_targets = tevil_fallback_nodes
        
        pragmatics_res = self.pragmatics.analyze_pragmatics(tokens)
        if not pragmatics_res["is_valid"]:
            return SemanticStatementIR(active_namespace=active_namespace, predicates=[], is_valid_for_z3=False)

        ir_predicates: List[Union[Tuple[str, str, int], NestedPredicate]] = []
        atomic_predicates: List[Union[Tuple[str, str, int], NestedPredicate]] = []
        
        has_luzumi = any(t.lower() in self.luzumi_particles for t in tokens)
        has_inadi = any(t.lower() in self.inadi_particles for t in tokens)

        for amil, mamul, rel_type, _ in dependencies:
            if amil.lower() in self.luzumi_particles or mamul.lower() in self.luzumi_particles:
                continue
            if amil.lower() in self.inadi_particles or mamul.lower() in self.inadi_particles:
                continue

            amil_id = self._resolve_entity(amil, active_namespace, auto_lexicon, proposition_type)
            mamul_id = self._resolve_entity(mamul, active_namespace, auto_lexicon, proposition_type)
            
            rel_id = f"Rel_{rel_type}"
            atomic_predicates.append((rel_id, f"{amil_id}::{mamul_id}", 2))
            
            atomic_predicates.append((amil_id, amil_id, 1))
            atomic_predicates.append((mamul_id, mamul_id, 1))

        if has_inadi:
            nested_logic = NestedPredicate(operator="Inadi", args=atomic_predicates)
            ir_predicates.append(nested_logic)
        elif has_luzumi:
            nested_logic = NestedPredicate(operator="Luzumi", args=atomic_predicates)
            ir_predicates.append(nested_logic)
        else:
            ir_predicates.extend(atomic_predicates)

        # [FAZ 3] Deontik Mantık Sarmalayıcısı
        if pragmatics_res["type"] == "Deontic":
            op = "Wajib_Fiqh" if pragmatics_res["operator"] == "Emir" else "Haram_Fiqh"
            deontic_logic = NestedPredicate(operator=op, args=ir_predicates)
            ir_predicates = [deontic_logic]

        return SemanticStatementIR(active_namespace=active_namespace, predicates=ir_predicates, is_valid_for_z3=True)
        
    def _resolve_entity(self, word: str, active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis], proposition_type: str) -> str:
        pronoun_res = self.discourse.resolve_pronoun(word)
        if pronoun_res:
            return pronoun_res
            
        search_key = word
        morph_data = auto_lexicon.get(word)
        if morph_data:
            search_key = morph_data.root

        # [FAZ 3] Bağlam Avcısı: Discourse objesi Siyak-Sibak için Leksikona zerk edilir
        base_ontologic_id = self.lexicon.resolve_id(search_key, active_namespace, proposition_type, self.discourse)
        
        if base_ontologic_id in getattr(self, 'current_tevil_targets', []):
            try:
                ontologic_id = self.lexicon.resolve_id(search_key, active_namespace, "Metaphor_Fallback", self.discourse)
            except ValueError:
                ontologic_id = base_ontologic_id
        else:
            ontologic_id = base_ontologic_id
        
        if not ontologic_id.startswith("Fiil_") and not ontologic_id.startswith("Harf_"):
            self.discourse.add_mention(word, ontologic_id)
            
        return ontologic_id