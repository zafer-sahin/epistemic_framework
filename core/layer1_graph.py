from typing import Dict, Any, Optional, List
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
        
    def find_mana_el_mana_chain(self, source_id: str, target_id: str) -> List[str]:
        """
        [FAZ 3 ENTEGRASYONU] İlm-i Beyân Alâka İzi (Deterministic Path).
        Abdülkâhir el-Cürcânî'nin 'Ma'nâ el-Ma'nâ' teorisine uygun olarak; 
        rastgele (fallback) veya serbest hiyerarşik (BFS) arama yerine, doğrudan 
        'alaka_type' (Sebebiyye, Mülâzemet vb.) ile etiketlenmiş kenarları VE 
        Alâka-i Cüz'iyye/Külliyye'yi (hiyerarşik alt türleri) takip ederek nedensellik vektörü çıkarır.
        """
        visited = set()
        path = []

        def _trace_alaka_path(current_node: str) -> bool:
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

            # 1. Öncelik: Doğrudan İlm-i Beyân Alâka tiplerine sahip yatay ilişkiler (Sebebiyye/Mülâzemet vb.)
            for rel in entity.relations:
                if getattr(rel, 'alaka_type', None):
                    if _trace_alaka_path(rel.target_id):
                        return True

            # 2. Öncelik: İlm-i Beyân Alâka-i Cüz'iyye / Külliyye (Hiyerarşik Alt/Üst Bağlantılar)
            # Kudret -> Sifat_Yed_Metaphor gibi spesifik alt türlere inmek için zorunludur.
            for child in entity.children:
                if _trace_alaka_path(child.ontologic_id):
                    return True

            path.pop()
            return False

        if _trace_alaka_path(source_id):
            return path
        return []

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