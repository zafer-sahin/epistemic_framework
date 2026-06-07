from __future__ import annotations
from typing import List, Tuple, Dict, Union, Optional
from pydantic import BaseModel, ConfigDict
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.pragmatics import MaaniSpeechActAnalyzer
from linguistics.discourse_state import DiscourseRegister
from linguistics.sarf_parser import MorphologicalAnalysis
from core.exceptions import DiachronicViolationError

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
    def extract_structural_roles(self, word: str, ontologic_id: str, auto_lexicon: Dict[str, MorphologicalAnalysis]) -> List[Tuple[str, str, int]]:
        predicates = []
        morph_data = auto_lexicon.get(word)
        if morph_data and morph_data.thematic_role:
            role_predicate = f"Role_{morph_data.thematic_role}"
            predicates.append((role_predicate, ontologic_id, 1))
        return predicates

class IlmWadAdapter:
    """
    Doğal dil bileşenlerini (AST ve Sarf) Birinci Dereceden Mantık (FOL) matrislerine (Semantic IR) dönüştürür.
    Faz 2 - Adım 3.1: İlm-i Ma'ânî'den (Pragmatics) gelen yönlü 'Kasr_Data' verisini 'Kasr_Mevsuf_to_Sifat' 
    veya 'Kasr_Sifat_to_Mevsuf' NestedPredicate formuna çevirerek Z3'e mutlak evrensel dışlama komutu verir.
    Faz 2 - Adım 3.2: Harf-i Atıf (Fasıl/Vasıl) edatlarını Kadiyye-i Şartiyye (Inadi/Luzumi) düğümlerine dönüştürür.
    [FAZ 1 ENTEGRASYONU]: Çifte Dönüşüm (Double Conversion) yasaklanmıştır. Tüm ara birim yüklemleri 
    'Classical' dönemi zaman damgasıyla (epoch) işlenmeye zorlanır. Pivot dil sızıntısı izole edilmiştir.
    [FAZ 3 ENTEGRASYONU]: Amel_Inne AST bağları çözümlenerek Kripke uzayı için Epistemic_Necessity operatörüne sarmalanır.
    """
    def __init__(self, lexicon: ContextualLexicon, discourse: DiscourseRegister):
        self.lexicon = lexicon
        self.discourse = discourse
        self.pragmatics = MaaniSpeechActAnalyzer(self.discourse)
        self.positing_engine = StructuralPositingEngine() 
        self.luzumi_particles = {"in", "iza", "law", "amma"}
        self.inadi_particles = {"imma", "aw", "ya", "am"} 
        self.mani_cem_particles = {"mani_cem", "la_yectemian"} 
        self.mani_huluv_particles = {"mani_huluv", "la_yahtaliyan"} 
        self.current_tevil_targets: List[str] = []

    def generate_ir(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]], active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis] = None, tevil_fallback_nodes: List[str] = None, proposition_type: str = "Kadiyye-i_Hamliyye", epoch: str = "Classical") -> SemanticStatementIR:
        if epoch != "Classical":
            raise DiachronicViolationError("[ÇİFTE DÖNÜŞÜM İHLALİ] Semantic IR Matrisi yalnızca 'Classical' Arapça ontolojisini derleyebilir. Çeviri katmanları yasaktır.")
            
        if auto_lexicon is None: auto_lexicon = {}
        if tevil_fallback_nodes is None: tevil_fallback_nodes = []
        
        self.current_tevil_targets = tevil_fallback_nodes
        
        pragmatics_res = self.pragmatics.analyze_pragmatics(tokens, dependencies)
        if not pragmatics_res["is_valid"]:
            return SemanticStatementIR(active_namespace=active_namespace, predicates=[], is_valid_for_z3=False)

        ir_predicates: List[Union[Tuple[str, str, int], NestedPredicate]] = []
        atomic_predicates: List[Union[Tuple[str, str, int], NestedPredicate]] = []
        
        has_luzumi = any(t.lower() in self.luzumi_particles for t in tokens)
        has_inadi = any(t.lower() in self.inadi_particles for t in tokens)
        has_mani_cem = any(t.lower() in self.mani_cem_particles for t in tokens)
        has_mani_huluv = any(t.lower() in self.mani_huluv_particles for t in tokens)
        
        processed_roles = set()

        # [FAZ 3 ENTEGRASYONU] Amel_Inne İlişkilerini Kadiyye-i Hamliyye'ye (Mubteda_Haber) Döndürme
        inne_relations = {}
        for amil, mamul, rel_type, irab in dependencies:
            if rel_type == 'Amel_Inne_Ism':
                if amil not in inne_relations: inne_relations[amil] = {}
                inne_relations[amil]['ism'] = mamul
            elif rel_type == 'Amel_Inne_Haber':
                if amil not in inne_relations: inne_relations[amil] = {}
                inne_relations[amil]['haber'] = mamul

        for inne_token, rels in inne_relations.items():
            if 'ism' in rels and 'haber' in rels:
                ism_id = self._resolve_entity(rels['ism'], active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
                haber_id = self._resolve_entity(rels['haber'], active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
                # Haber -> Mubteda (Amil -> Mamul) as per Nahiv logic where Haber is the predicate.
                atomic_predicates.append(("Rel_Mubteda_Haber", f"{haber_id}::{ism_id}", 2))
                atomic_predicates.append((ism_id, ism_id, 1))
                atomic_predicates.append((haber_id, haber_id, 1))

        for amil, mamul, rel_type, irab in dependencies:
            # [FAZ 3 ENTEGRASYONU] Amel_Inne_ bağları yukarıda çözüldüğü için standart döngüde es geçilir.
            if rel_type in ['Tevkid_Modifier', 'Kasr_Modifier', 'Rel_Ihtisas'] or rel_type.startswith('Amel_Inne_'):
                continue
            
            # [FAZ 2.6] Harf-i Atıf (Fasıl/Vasıl) Doğrudan Kadiyye-i Şartiyye'ye (NestedPredicate) dönüştürülür
            if rel_type == 'Rel_Atif':
                amil_id = self._resolve_entity(amil, active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
                mamul_id = self._resolve_entity(mamul, active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
                
                particle = irab.lower()
                if particle in self.inadi_particles:
                    atomic_predicates.append(NestedPredicate(operator="Inadi_Hakikiyye", args=[(amil_id, amil_id, 1), (mamul_id, mamul_id, 1)]))
                else: # wa, fa, summe, vb. Lüzumî (Birleştirici) bağlar
                    atomic_predicates.append(NestedPredicate(operator="Luzumi", args=[(amil_id, amil_id, 1), (mamul_id, mamul_id, 1)]))
                
                atomic_predicates.append((amil_id, amil_id, 1))
                atomic_predicates.append((mamul_id, mamul_id, 1))
                continue

            if amil.lower() in self.luzumi_particles or mamul.lower() in self.luzumi_particles:
                continue
            if amil.lower() in self.inadi_particles or mamul.lower() in self.inadi_particles:
                continue
            if amil.lower() in self.mani_cem_particles or mamul.lower() in self.mani_cem_particles:
                continue
            if amil.lower() in self.mani_huluv_particles or mamul.lower() in self.mani_huluv_particles:
                continue

            amil_id = self._resolve_entity(amil, active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
            mamul_id = self._resolve_entity(mamul, active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
            
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

        if has_mani_cem:
            nested_logic = NestedPredicate(operator="Inadi_Maniatul_Cem", args=atomic_predicates)
            ir_predicates.append(nested_logic)
        elif has_mani_huluv:
            nested_logic = NestedPredicate(operator="Inadi_Maniatul_Huluv", args=atomic_predicates)
            ir_predicates.append(nested_logic)
        elif has_inadi:
            nested_logic = NestedPredicate(operator="Inadi_Hakikiyye", args=atomic_predicates)
            ir_predicates.append(nested_logic)
        elif has_luzumi:
            nested_logic = NestedPredicate(operator="Luzumi", args=atomic_predicates)
            ir_predicates.append(nested_logic)
        else:
            ir_predicates.extend(atomic_predicates)

        if pragmatics_res.get("type") == "Deontic":
            op = "Wajib_Fiqh" if pragmatics_res.get("operator") == "Emir" else "Haram_Fiqh"
            deontic_logic = NestedPredicate(operator=op, args=ir_predicates)
            ir_predicates = [deontic_logic]
            
        elif pragmatics_res.get("type") == "Istifham_i_Inkari":
            inkari_logic = NestedPredicate(operator="Istifham_Inkari", args=ir_predicates)
            ir_predicates = [inkari_logic]

        # [FAZ 2 ENTEGRASYONU] İlm-i Ma'ânî Yönlü Kasr (Hasr) İşlemesi
        kasr_data = pragmatics_res.get("kasr_data")
        if kasr_data:
            kasr_dir = kasr_data.get("kasr_direction", "Mevsuf_to_Sifat")
            kasr_logic = NestedPredicate(operator=f"Kasr_{kasr_dir}", args=ir_predicates)
            ir_predicates = [kasr_logic]

        # [FAZ 3 ENTEGRASYONU] Epistemic Necessity (Tahkik) Sarmalaması
        epistemic_modality = pragmatics_res.get("epistemic_modality")
        if epistemic_modality == "Epistemic_Necessity":
            epistemic_logic = NestedPredicate(operator="Epistemic_Necessity", args=ir_predicates)
            ir_predicates = [epistemic_logic]

        unique_predicates = []
        seen = set()
        for item in ir_predicates:
            frozen_item = str(item)
            if frozen_item not in seen:
                seen.add(frozen_item)
                unique_predicates.append(item)

        return SemanticStatementIR(active_namespace=active_namespace, predicates=unique_predicates, is_valid_for_z3=True)
        
    def _resolve_entity(self, word: str, active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis], proposition_type: str, dependencies: List[Tuple[str, str, str, str]], epoch: str) -> str:
        pronoun_res = self.discourse.resolve_pronoun(word, enforcement_namespace=active_namespace)
        if pronoun_res:
            return pronoun_res
            
        search_key = word
        morph_data = auto_lexicon.get(word)
        if morph_data:
            search_key = morph_data.root

        if morph_data and morph_data.ontologic_type == "Harf_Tevkid":
            return f"GrammarNode_{search_key.capitalize()}"
            
        if morph_data and morph_data.ontologic_type == "Harf_Kasr":
            return f"GrammarNode_{search_key.capitalize()}"

        # [FAZ 3 ENTEGRASYONU] Inne operatörü Leksikon hatası vermemesi için GrammarNode sarmalaması
        if morph_data and morph_data.ontologic_type == "Harf_Inne":
            return f"GrammarNode_{search_key.capitalize()}"

        base_ontologic_id = self.lexicon.resolve_id(search_key, active_namespace, proposition_type, self.discourse, dependencies, epoch)
        
        if base_ontologic_id in getattr(self, 'current_tevil_targets', []):
            try:
                ontologic_id = self.lexicon.resolve_id(search_key, active_namespace, "Metaphor_Fallback", self.discourse, dependencies, epoch)
            except (ValueError, DiachronicViolationError):
                ontologic_id = base_ontologic_id
        else:
            ontologic_id = base_ontologic_id
        
        if not ontologic_id.startswith("Fiil_") and not ontologic_id.startswith("Harf_") and not ontologic_id.startswith("GrammarNode_"):
            self.discourse.add_mention(word, ontologic_id, active_namespace)
            
        return ontologic_id