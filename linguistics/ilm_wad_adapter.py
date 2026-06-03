from __future__ import annotations
from typing import List, Tuple, Dict, Union, Optional
from pydantic import BaseModel, ConfigDict
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.pragmatics import MaaniSpeechActAnalyzer
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

class StructuralPositingEngine:
    """
    İlm-i Vaz' Yapısal Kodlama Motoru (Vaz' Nev'î).
    Faz 1.2: Kelimelerin morfolojik kalıbından (vezninden) doğan tematik rolleri 
    (Agent, Patient, Action) Semantik Ara Temsil'e (IR) FOL yüklemi olarak enjekte eder.
    """
    def extract_structural_roles(self, word: str, ontologic_id: str, auto_lexicon: Dict[str, MorphologicalAnalysis]) -> List[Tuple[str, str, int]]:
        predicates = []
        morph_data = auto_lexicon.get(word)
        if morph_data and morph_data.thematic_role:
            # Örn: ("Role_Agent", "Zeyd_Entity", 1)
            role_predicate = f"Role_{morph_data.thematic_role}"
            predicates.append((role_predicate, ontologic_id, 1))
        return predicates

class IlmWadAdapter:
    def __init__(self, lexicon: ContextualLexicon, discourse: DiscourseRegister):
        self.lexicon = lexicon
        self.discourse = discourse
        # [FAZ 2.3] PragmaticsFilter yerine MaaniSpeechActAnalyzer entegre edildi.
        self.pragmatics = MaaniSpeechActAnalyzer(self.discourse)
        self.positing_engine = StructuralPositingEngine() 
        self.luzumi_particles = {"in", "iza", "law", "amma"}
        self.inadi_particles = {"imma", "aw", "ya"} 
        self.current_tevil_targets: List[str] = []

    def generate_ir(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]], active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis] = None, tevil_fallback_nodes: List[str] = None, proposition_type: str = "Kadiyye-i_Hamliyye") -> SemanticStatementIR:
        if auto_lexicon is None: auto_lexicon = {}
        if tevil_fallback_nodes is None: tevil_fallback_nodes = []
        
        self.current_tevil_targets = tevil_fallback_nodes
        
        # [FAZ 2.3] Muktazâ el-Hâl analizi için dependencies parametresi de gönderilir
        pragmatics_res = self.pragmatics.analyze_pragmatics(tokens, dependencies)
        if not pragmatics_res["is_valid"]:
            # MAANI_VIOLATION (Muktazâ el-Hâl ihlali) veya Istifham_Hakiki reddi
            return SemanticStatementIR(active_namespace=active_namespace, predicates=[], is_valid_for_z3=False)

        ir_predicates: List[Union[Tuple[str, str, int], NestedPredicate]] = []
        atomic_predicates: List[Union[Tuple[str, str, int], NestedPredicate]] = []
        
        has_luzumi = any(t.lower() in self.luzumi_particles for t in tokens)
        has_inadi = any(t.lower() in self.inadi_particles for t in tokens)
        
        processed_roles = set()

        for amil, mamul, rel_type, _ in dependencies:
            if amil.lower() in self.luzumi_particles or mamul.lower() in self.luzumi_particles:
                continue
            if amil.lower() in self.inadi_particles or mamul.lower() in self.inadi_particles:
                continue

            amil_id = self._resolve_entity(amil, active_namespace, auto_lexicon, proposition_type)
            mamul_id = self._resolve_entity(mamul, active_namespace, auto_lexicon, proposition_type)
            
            # Tevkîd edatları ontolojik yüklem matrisine (Z3) girmez, Muktazâ el-Hâl için kullanılır.
            if rel_type == 'Tevkid_Modifier':
                continue
            
            rel_id = f"Rel_{rel_type}"
            atomic_predicates.append((rel_id, f"{amil_id}::{mamul_id}", 2))
            
            atomic_predicates.append((amil_id, amil_id, 1))
            atomic_predicates.append((mamul_id, mamul_id, 1))

            amil_roles = self.positing_engine.extract_structural_roles(amil, amil_id, auto_lexicon)
            for role in amil_roles:
                if role not in processed_roles:
                    atomic_predicates.append(role)
                    processed_roles.add(role)
                    
            mamul_roles = self.positing_engine.extract_structural_roles(mamul, mamul_id, auto_lexicon)
            for role in mamul_roles:
                if role not in processed_roles:
                    atomic_predicates.append(role)
                    processed_roles.add(role)

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
            
        # [FAZ 2.4] İstifham-ı İnkârî Sarmalayıcısı
        elif pragmatics_res["type"] == "Istifham_i_Inkari":
            inkari_logic = NestedPredicate(operator="Istifham_Inkari", args=ir_predicates)
            ir_predicates = [inkari_logic]

        # Çift (Duplicate) yüklemlerin temizlenerek IR'nin Z3 optimizasyonuna hazırlanması
        unique_predicates = []
        seen = set()
        for item in ir_predicates:
            frozen_item = str(item)
            if frozen_item not in seen:
                seen.add(frozen_item)
                unique_predicates.append(item)

        return SemanticStatementIR(active_namespace=active_namespace, predicates=unique_predicates, is_valid_for_z3=True)
        
    def _resolve_entity(self, word: str, active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis], proposition_type: str) -> str:
        # [FAZ 4] Zamir çözücüye 'active_namespace' zırhı basıldı
        pronoun_res = self.discourse.resolve_pronoun(word, enforcement_namespace=active_namespace)
        if pronoun_res:
            return pronoun_res
            
        search_key = word
        morph_data = auto_lexicon.get(word)
        if morph_data:
            search_key = morph_data.root

        # Harf_Tevkid için leksikon sorgusunu atla, Z3 ontolojisine girmemesi gereken salt gramatik düğüm.
        if morph_data and morph_data.ontologic_type == "Harf_Tevkid":
            return f"GrammarNode_{search_key.capitalize()}"

        # [FAZ 3] Bağlam Avcısı
        base_ontologic_id = self.lexicon.resolve_id(search_key, active_namespace, proposition_type, self.discourse)
        
        if base_ontologic_id in getattr(self, 'current_tevil_targets', []):
            try:
                ontologic_id = self.lexicon.resolve_id(search_key, active_namespace, "Metaphor_Fallback", self.discourse)
            except ValueError:
                ontologic_id = base_ontologic_id
        else:
            ontologic_id = base_ontologic_id
        
        if not ontologic_id.startswith("Fiil_") and not ontologic_id.startswith("Harf_") and not ontologic_id.startswith("GrammarNode_"):
            # [FAZ 4] Söylem belleğine kayıt esnasında 'active_namespace' mührü eklendi
            self.discourse.add_mention(word, ontologic_id, active_namespace)
            
        return ontologic_id