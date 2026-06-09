from __future__ import annotations
from typing import List, Tuple, Dict, Union, Optional, Any
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
    """Tematik rolleri (Thematic Roles) FOL uzayında yapısal kısıtlara çevirir."""
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
    Faz 2 - Adım 3.1: İlm-i Ma'ânî'den (Pragmatics) gelen yönlü 'Kasr_Data' verisini 'Kasr_Mevsuf_to_Sifat' veya 'Kasr_Sifat_to_Mevsuf' NestedPredicate formuna çevirerek Z3'e mutlak evrensel dışlama komutu verir.
    Faz 2 - Adım 3.2: Harf-i Atıf (Fasıl/Vasıl) edatlarını Kadiyye-i Şartiyye (Inadi/Luzumi) düğümlerine dönüştürür.
    [FAZ 1 ENTEGRASYONU]: Çifte Dönüşüm (Double Conversion) yasaklanmıştır. Tüm ara birim yüklemleri 'Classical' dönemi zaman damgasıyla (epoch) işlenmeye zorlanır. Pivot dil sızıntısı izole edilmiştir.
    [FAZ 3 ENTEGRASYONU]: Amel_Inne AST bağları çözümlenerek Kripke uzayı için Epistemic_Necessity operatörüne sarmalanır.
    [FAZ 4 ENTEGRASYONU]: Zarf-ı Mustakar ve Zarf-ı Lağv Muteallak ilişkileri LocatedIn FOL kısıtına çevrilir.
    [FAZ 5 ENTEGRASYONU]: Muteallak_Harf ve Muteallak_Mekan ayırımı yapılarak Şibh-i Fiil ve diğer ontolojik edat bağları Z3 matrislerine uyarlandı.
    [FAZ 7 ENTEGRASYONU]: AST'den gelen Rabıta statüleri (Identity/Predication) IR formlarına eşlendi. Fâ-i Füzâiyye 'Luzumi_Dynamic' ve 'Dynamic_Transition' kısıtlarına çevrildi.
    
    [FAZ 9 LITERATE CHUNKING]: Bilişsel yükü (Cognitive Load) azaltmak için devasa `generate_ir` 
    fonksiyonu; 'İnne İşlemleri', 'Rabıta Çözümlemesi', 'Dinamik Mantık', 'Müteallak (Uzay)' 
    ve 'Kiplik (Pragmatics)' şeklinde izole private method'lara (Chunking) bölünmüştür.
    Her semantik düğümün Z3 SMT motorundaki felsefi/ontolojik kısıt karşılığı 
    pedagojik anlatılarla (LaTeX destekli) kod bloklarına dokunmuştur (Weaving).
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

    def _resolve_inne_relations(self, dependencies: List[Tuple[str, str, str, str]], atomic_predicates: List[Union[Tuple[str, str, int], NestedPredicate]], active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis], proposition_type: str, epoch: str) -> None:
        """
        .. pedagojik_anlati::
            Amel_Inne İlişkilerini Kadiyye-i Hamliyye'ye (Mubteda_Haber) Döndürme.
            Z3 SMT motorunda bu yapı $ \square (Ism \implies Haber) $ formunda 
            Epistemic Necessity (Zorunluluk) düğümüne dönüştürülmek üzere hazırlanır.
        """
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
                
                atomic_predicates.append(("Rel_Rabita_Predication", f"{haber_id}::{ism_id}", 2))
                atomic_predicates.append((ism_id, ism_id, 1))
                atomic_predicates.append((haber_id, haber_id, 1))

    def _resolve_rabita_and_dynamic_logic(self, amil: str, mamul: str, rel_type: str, irab: str, dependencies: List[Tuple[str, str, str, str]], atomic_predicates: List[Union[Tuple[str, str, int], NestedPredicate]], active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis], proposition_type: str, epoch: str) -> bool:
        """
        .. pedagojik_anlati::
            Rabıta düğümleri ontolojik eşdeğerliği ($x = y$) veya aidiyeti ($x \in Y$) kurar.
            Fâ-i Füzâiyye ve Harf-i Atıf ise Kripke semantiğinde dinamik durum sıçramaları 
            ($W_t \implies W_{t+1}$) ile mantıksal nedenselliği kilitler.
        """
        if rel_type in ['Tevkid_Modifier', 'Kasr_Modifier', 'Rel_Ihtisas', 'Rabita_Subject', 'Rabita_Predicate'] or rel_type.startswith('Amel_Inne_'):
            return True
            
        if rel_type in ['Rabita_Predication', 'Mubteda_Haber'] and amil == 'Kainun_Virtual':
            return True

        if rel_type in ['Rabita_Identity', 'Rabita_Predication', 'Mubteda_Haber']: 
            amil_id = self._resolve_entity(amil, active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
            mamul_id = self._resolve_entity(mamul, active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
            
            if rel_type == 'Rabita_Identity':
                atomic_predicates.append(("Rel_Rabita_Identity", f"{amil_id}::{mamul_id}", 2))
            else:
                atomic_predicates.append(("Rel_Rabita_Predication", f"{amil_id}::{mamul_id}", 2))
            
            atomic_predicates.append((amil_id, amil_id, 1))
            atomic_predicates.append((mamul_id, mamul_id, 1))
            return True

        if rel_type in ['Rel_Fa_Sebebiyye', 'Rel_Fa_Fuzaiyye']:
            amil_id = self._resolve_entity(amil, active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
            mamul_id = self._resolve_entity(mamul, active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
            op = "Luzumi_Dynamic" if rel_type == 'Rel_Fa_Sebebiyye' else "Dynamic_Transition"
            atomic_predicates.append(NestedPredicate(operator=op, args=[(amil_id, amil_id, 1), (mamul_id, mamul_id, 1)]))
            atomic_predicates.append((amil_id, amil_id, 1))
            atomic_predicates.append((mamul_id, mamul_id, 1))
            return True

        if rel_type == 'Rel_Atif':
            amil_id = self._resolve_entity(amil, active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
            mamul_id = self._resolve_entity(mamul, active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
            particle = irab.lower()
            
            if particle in self.inadi_particles:
                atomic_predicates.append(NestedPredicate(operator="Inadi_Hakikiyye", args=[(amil_id, amil_id, 1), (mamul_id, mamul_id, 1)]))
            else: 
                atomic_predicates.append(NestedPredicate(operator="Luzumi", args=[(amil_id, amil_id, 1), (mamul_id, mamul_id, 1)]))
            
            atomic_predicates.append((amil_id, amil_id, 1))
            atomic_predicates.append((mamul_id, mamul_id, 1))
            return True
            
        return False

    def _resolve_mutaallak_spatial_logic(self, amil: str, mamul: str, rel_type: str, dependencies: List[Tuple[str, str, str, str]], atomic_predicates: List[Union[Tuple[str, str, int], NestedPredicate]], active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis], proposition_type: str, epoch: str) -> bool:
        """
        .. pedagojik_anlati::
            Harf-i Cerlerin Müteallak (Bağlantı) Prensibi:
            FOL uzayında $\exists x. \text{LocatedIn}(x, l, w, t)$ şeklinde çok boyutlu
            uzay kısıtını Kripke dünyalarına uygular.
        """
        if rel_type in ['Muteallak_Mekan', 'Muteallak_Harf']:
            harf_node = mamul
            mecrur_target = next((m for a, m, r, _ in dependencies if r == 'Harf_Mecrur' and a == harf_node), None)
            
            if mecrur_target:
                mecrur_id = self._resolve_entity(mecrur_target, active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
                
                if amil == 'Kainun_Virtual':
                    mubteda_token = next((m for a, m, r, _ in dependencies if r in ['Mubteda_Haber', 'Rabita_Predication'] and a == 'Kainun_Virtual'), None)
                    if mubteda_token:
                        amil_id = self._resolve_entity(mubteda_token, active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
                    else:
                        amil_id = "Kainun_Virtual"
                else:
                    amil_id = self._resolve_entity(amil, active_namespace, auto_lexicon, proposition_type, dependencies, epoch)
                
                if rel_type == 'Muteallak_Mekan':
                    atomic_predicates.append(("LocatedIn", f"{amil_id}::{mecrur_id}", 2))
                else:
                    atomic_predicates.append(("Rel_Muteallak", f"{amil_id}::{mecrur_id}", 2))
            return True
        return False

    def _wrap_with_pragmatic_modalities(self, ir_predicates: List[Union[Tuple[str, str, int], NestedPredicate]], pragmatics_res: Dict[str, Any]) -> List[Union[Tuple[str, str, int], NestedPredicate]]:
        """
        .. pedagojik_anlati::
            İlm-i Ma'ânî'den süzülen pragmatik verilerin (Deontik $O(P)$, Kasr $\forall x$, 
            Epistemik $\square P$) üst-kapsül olarak IR yüklemlerine sarılması işlemidir.
        """
        if pragmatics_res.get("type") == "Deontic":
            op = "Wajib_Fiqh" if pragmatics_res.get("operator") == "Emir" else "Haram_Fiqh"
            ir_predicates = [NestedPredicate(operator=op, args=ir_predicates)]
            
        elif pragmatics_res.get("type") == "Istifham_i_Inkari":
            ir_predicates = [NestedPredicate(operator="Istifham_Inkari", args=ir_predicates)]

        kasr_data = pragmatics_res.get("kasr_data")
        if kasr_data:
            kasr_dir = kasr_data.get("kasr_direction", "Mevsuf_to_Sifat")
            ir_predicates = [NestedPredicate(operator=f"Kasr_{kasr_dir}", args=ir_predicates)]

        epistemic_modality = pragmatics_res.get("epistemic_modality")
        if epistemic_modality == "Epistemic_Necessity":
            ir_predicates = [NestedPredicate(operator="Epistemic_Necessity", args=ir_predicates)]
            
        return ir_predicates

    def _process_atomic_relations(self, dependencies: List[Tuple[str, str, str, str]], atomic_predicates: List[Union[Tuple[str, str, int], NestedPredicate]], active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis], proposition_type: str, epoch: str) -> None:
        """
        .. pedagojik_anlati::
            Temel Amil-Mamul ilişkilerinin, yapısal roller (Agent, Patient) ile 
            birlikte salt FOL (First-Order Logic) atomlarına ayrıştırılmasıdır.
        """
        processed_roles = set()
        for amil, mamul, rel_type, irab in dependencies:
            if self._resolve_rabita_and_dynamic_logic(amil, mamul, rel_type, irab, dependencies, atomic_predicates, active_namespace, auto_lexicon, proposition_type, epoch):
                continue
                
            if self._resolve_mutaallak_spatial_logic(amil, mamul, rel_type, dependencies, atomic_predicates, active_namespace, auto_lexicon, proposition_type, epoch):
                continue

            if rel_type == 'Harf_Mecrur':
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

    def _apply_propositional_capsules(self, has_mani_cem: bool, has_mani_huluv: bool, has_inadi: bool, has_luzumi: bool, atomic_predicates: List[Union[Tuple[str, str, int], NestedPredicate]]) -> List[Union[Tuple[str, str, int], NestedPredicate]]:
        """
        .. pedagojik_anlati::
            Kadiyye-i Şartiyye (Hipotetik Önermeler) için İnadî/Lüzumî üst kapsülleme işlemleri.
        """
        ir_predicates = []
        if has_mani_cem:
            ir_predicates.append(NestedPredicate(operator="Inadi_Maniatul_Cem", args=atomic_predicates))
        elif has_mani_huluv:
            ir_predicates.append(NestedPredicate(operator="Inadi_Maniatul_Huluv", args=atomic_predicates))
        elif has_inadi:
            ir_predicates.append(NestedPredicate(operator="Inadi_Hakikiyye", args=atomic_predicates))
        elif has_luzumi:
            ir_predicates.append(NestedPredicate(operator="Luzumi", args=atomic_predicates))
        else:
            ir_predicates.extend(atomic_predicates)
        return ir_predicates

    def generate_ir(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]], active_namespace: str, auto_lexicon: Dict[str, MorphologicalAnalysis] = None, tevil_fallback_nodes: List[str] = None, proposition_type: str = "Kadiyye-i_Hamliyye", epoch: str = "Classical") -> SemanticStatementIR:
        if epoch != "Classical":
            raise DiachronicViolationError("[ÇİFTE DÖNÜŞÜM İHLALİ] Semantic IR Matrisi yalnızca 'Classical' Arapça ontolojisini derleyebilir. Çeviri katmanları yasaktır.")
            
        if auto_lexicon is None: auto_lexicon = {}
        if tevil_fallback_nodes is None: tevil_fallback_nodes = []
        
        self.current_tevil_targets = tevil_fallback_nodes
        
        pragmatics_res = self.pragmatics.analyze_pragmatics(tokens, dependencies)
        if not pragmatics_res["is_valid"]:
            return SemanticStatementIR(active_namespace=active_namespace, predicates=[], is_valid_for_z3=False)

        atomic_predicates: List[Union[Tuple[str, str, int], NestedPredicate]] = []
        
        has_luzumi = any(t.lower() in self.luzumi_particles for t in tokens)
        has_inadi = any(t.lower() in self.inadi_particles for t in tokens)
        has_mani_cem = any(t.lower() in self.mani_cem_particles for t in tokens)
        has_mani_huluv = any(t.lower() in self.mani_huluv_particles for t in tokens)
        
        self._resolve_inne_relations(dependencies, atomic_predicates, active_namespace, auto_lexicon, proposition_type, epoch)
        self._process_atomic_relations(dependencies, atomic_predicates, active_namespace, auto_lexicon, proposition_type, epoch)
        
        ir_predicates = self._apply_propositional_capsules(has_mani_cem, has_mani_huluv, has_inadi, has_luzumi, atomic_predicates)
        ir_predicates = self._wrap_with_pragmatic_modalities(ir_predicates, pragmatics_res)

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