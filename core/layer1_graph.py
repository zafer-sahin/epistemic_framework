from typing import Dict, Any, Optional, List
from linguistics.ilm_wad_adapter import SemanticStatementIR
from core.models import BaseOntology, EpistemicEntity

class Layer1HeuristicGraph:
    def __init__(self, ontology: BaseOntology):
        self.ontology = ontology
        self.parent_map: Dict[str, str] = {}
        self._build_parent_map()

    def _build_parent_map(self) -> None:
        for root_node in self.ontology.porphyrian_tree.roots.values():
            self._traverse_and_map(root_node, None)

    def _traverse_and_map(self, entity: EpistemicEntity, parent_id: Optional[str]) -> None:
        if parent_id:
            self.parent_map[entity.ontologic_id] = parent_id
        for child in entity.children:
            self._traverse_and_map(child, entity.ontologic_id)

    def _get_distance(self, node_a: str, node_b: str) -> int:
        if node_a not in self.parent_map and node_a not in self.ontology.porphyrian_tree.roots:
            return 0 
        if node_b not in self.parent_map and node_b not in self.ontology.porphyrian_tree.roots:
            return 0

        path_a = self._get_ancestors(node_a)
        path_b = self._get_ancestors(node_b)

        lca = None
        for ancestor in path_a:
            if ancestor in path_b:
                lca = ancestor
                break
        
        if not lca:
            return len(path_a) + len(path_b)

        return path_a.index(lca) + path_b.index(lca)

    def _get_ancestors(self, node: str) -> List[str]:
        path = [node]
        current = node
        while current in self.parent_map:
            current = self.parent_map[current]
            path.append(current)
        return path

    def analyze_ir(self, ir_matrix: SemanticStatementIR) -> Dict[str, Any]:
        if not ir_matrix.is_valid_for_z3:
            return {"status": "REJECTED", "metaphor_probability": 0.0, "reason": "İnşâî form"}

        max_distance = 0
        flagged_predicates = []

        for pred_id, arg_id, arity in ir_matrix.predicates:
            if arity == 2:
                try:
                    # [LOGIC FIX]: Ayrıştırıcı '_' yerine '::' yapıldı.
                    amil_str, mamul_str = arg_id.split('::', 1)
                    distance = self._get_distance(amil_str, mamul_str)
                    
                    if distance > 3:
                        max_distance = max(max_distance, distance)
                        flagged_predicates.append(arg_id)
                except ValueError:
                    continue 

        metaphor_score = min((max_distance / 10.0), 1.0) if max_distance > 3 else 0.0
        is_metaphor_likely = metaphor_score >= 0.5

        return {
            "status": "ANALYZED",
            "is_metaphor_likely": is_metaphor_likely,
            "metaphor_probability": metaphor_score,
            "max_ontological_distance": max_distance,
            "flagged_elements": flagged_predicates
        }