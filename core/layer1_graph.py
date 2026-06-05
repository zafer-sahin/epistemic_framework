from typing import Dict, Any, Optional, List, Tuple
from linguistics.ilm_wad_adapter import SemanticStatementIR, NestedPredicate
from core.models import BaseOntology, EpistemicEntity

class Layer1HeuristicGraph:
    def __init__(self, ontology: BaseOntology):
        self.ontology = ontology
        self.entity_map: Dict[str, EpistemicEntity] = {}
        self._build_entity_map()

    def _build_entity_map(self) -> None:
        for root_node in self.ontology.porphyrian_tree.roots.values():
            self._traverse_and_map(root_node)

    def _traverse_and_map(self, entity: EpistemicEntity) -> None:
        self.entity_map[entity.ontologic_id] = entity
        for child in entity.children:
            self._traverse_and_map(child)

    def _evaluate_modal_conflict(self, amil_entity: EpistemicEntity, mamul_entity: EpistemicEntity) -> float:
        """
        İlm-i Beyân prensiplerine göre ontolojik modalite uyuşmazlığını (Karîne-i Mânia) ölçer.
        Uzaklık (distance) yerine 'Hüsn-ü Mücerred' ve 'Vâcib/Mümkin' statüleri baz alınır.
        """
        conflict_score = 0.0
        
        # Kural 1: Vâcibu'l-Vücûd (Zorunlu Varlık) ile Mümkin (Hâdis) varlık/araz etkileşimi
        if (amil_entity.modal_status in ["Wajib", "Zaruriyye_i_Mutlaka"] and mamul_entity.modal_status in ["Mumkin", "Mumkine_i_Amme"]) or \
           (mamul_entity.modal_status in ["Wajib", "Zaruriyye_i_Mutlaka"] and amil_entity.modal_status in ["Mumkin", "Mumkine_i_Amme"]):
            conflict_score += 0.6
            
        # Kural 2: Hüsn-ü Mücerred (Soyut Mükemmellik) İhlali
        if amil_entity.husn_u_mucerred and not mamul_entity.husn_u_mucerred:
            conflict_score += 0.4
        elif mamul_entity.husn_u_mucerred and not amil_entity.husn_u_mucerred:
            conflict_score += 0.4
            
        # Kural 3: Leksikal Karine Derecesi Çarpanı (Delalet-i Tazammun/İltizam)
        max_karine = max(amil_entity.karine_derecesi, mamul_entity.karine_derecesi)
        if max_karine > 0:
            conflict_score += (max_karine * 0.2)

        return min(conflict_score, 1.0)

    def _find_istiare_mushabehat(self, source_id: str, target_id: str) -> List[str]:
        """
        [FAZ 3] İstiare (Müşabehet) için Kesişim (Intersection) Algoritması.
        Kaynak (Müsteâr'un Minh) ve hedef (Müsteâr'un Leh) arasındaki ortak 
        'beyan_mushabehat_ids' veya 'propria_ids' (Hâssa) kesişimini bulur.
        """
        source_ent = self.entity_map.get(source_id)
        target_ent = self.entity_map.get(target_id)
        
        if not source_ent or not target_ent:
            return []
            
        source_traits = set(source_ent.beyan_mushabehat_ids + source_ent.propria_ids)
        target_traits = set(target_ent.beyan_mushabehat_ids + target_ent.propria_ids)
        
        return list(source_traits.intersection(target_traits))

    def find_mana_el_mana_chain(self, source_id: str, target_id: str) -> Dict[str, Any]:
        """
        [FAZ 3 ENTEGRASYONU] İlm-i Beyân Alâka İzi (Deterministic Path).
        Mecaz-ı Mürsel (DFS nedensellik) ve İstiare (Proprium Kesişimi) algoritmalarını ayırır.
        Kinaye rotaları da ilişki (relation) bazlı taranır. Z3 ispatı için Lüzum Derecesini tespit eder.
        """
        # 1. İstiare Kontrolü (Müşabehet / Benzerlik Taraması)
        mushabehat = self._find_istiare_mushabehat(source_id, target_id)
        if mushabehat:
            source_ent = self.entity_map.get(source_id)
            luzum_derecesi = "Luzum_u_Zihni" # İstiare varsayılan olarak zihinsel lüzumiyet taşır.
            alaka_type = "İstiare_Tahkikiyye"
            
            if source_ent:
                for rel in source_ent.relations:
                    if rel.target_id == target_id and rel.alaka_type and "İstiare" in rel.alaka_type:
                        luzum_derecesi = rel.luzum_derecesi or "Luzum_u_Zihni"
                        alaka_type = rel.alaka_type
                        break
                        
            return {
                "is_found": True,
                "type": "Istiare",
                "path": [source_id, target_id],
                "alaka_type": alaka_type,
                "mushabehat": mushabehat,
                "luzum_derecesi": luzum_derecesi
            }

        # 2. Mecaz-ı Mürsel / Kinaye Kontrolü (DFS Nedensellik Ağı Taraması)
        visited = set()
        path = []
        found_alaka_type = None
        found_luzum = None

        def _trace_alaka_path(current_node: str) -> bool:
            nonlocal found_alaka_type, found_luzum
            if current_node == target_id:
                path.append(current_node)
                return True

            if current_node in visited:
                return False

            visited.add(current_node)
            path.append(current_node)

            entity = self.entity_map.get(current_node)
            if not entity:
                path.pop()
                return False

            # Yatay Öncelikli Tarama: Kinaye ve Mecaz-ı Mürsel İlişkileri
            for rel in entity.relations:
                if rel.alaka_type and ("Alaka" in rel.alaka_type or "Kinaye" in rel.alaka_type):
                    if _trace_alaka_path(rel.target_id):
                        found_alaka_type = rel.alaka_type
                        found_luzum = rel.luzum_derecesi
                        return True

            # Dikey Tarama: Alâka-i Cüz'iyye / Külliyye (Hiyerarşik İniş)
            for child in entity.children:
                if _trace_alaka_path(child.ontologic_id):
                    if not found_alaka_type:
                        found_alaka_type = "Alaka_Cüziyye"
                        found_luzum = "Luzum_u_Zihni"
                    return True

            path.pop()
            return False

        if _trace_alaka_path(source_id):
            return {
                "is_found": True,
                "type": "Mecaz_Kinaye",
                "path": path,
                "alaka_type": found_alaka_type,
                "luzum_derecesi": found_luzum or "Luzum_u_Zihni"
            }

        return {"is_found": False}

    def analyze_ir(self, ir_matrix: SemanticStatementIR) -> Dict[str, Any]:
        if not ir_matrix.is_valid_for_z3:
            return {"status": "REJECTED", "metaphor_probability": 0.0, "reason": "İnşâî form"}

        max_conflict = 0.0
        flagged_predicates = []

        # [FAZ 2 ENTEGRASYONU] NestedPredicate içeren Kasr/Deontik yapıları taramak için rekürsif tarayıcı
        def _scan_predicates(pred_list):
            nonlocal max_conflict
            for item in pred_list:
                if isinstance(item, tuple):
                    pred_id, arg_id, arity = item
                
                    if arity == 2 and '::' in arg_id:
                        try:
                            amil_str, mamul_str = arg_id.split('::', 1)
                            amil_ent = self.entity_map.get(amil_str)
                            mamul_ent = self.entity_map.get(mamul_str)
                            
                            if amil_ent and mamul_ent:
                                conflict = self._evaluate_modal_conflict(amil_ent, mamul_ent)
                                
                                if conflict >= 0.5:
                                    max_conflict = max(max_conflict, conflict)
                                    flagged_predicates.append(arg_id)
                        except ValueError:
                            continue 
                elif isinstance(item, NestedPredicate):
                    _scan_predicates(item.args)

        _scan_predicates(ir_matrix.predicates)

        is_metaphor_likely = max_conflict >= 0.5

        return {
            "status": "ANALYZED",
            "is_metaphor_likely": is_metaphor_likely,
            "metaphor_probability": max_conflict,
            "max_modal_conflict_score": max_conflict,
            "flagged_elements": flagged_predicates
        }