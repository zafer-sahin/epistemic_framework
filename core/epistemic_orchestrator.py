from typing import Dict, Any, List, Tuple
import re
from linguistics.ilm_wad_adapter import IlmWadAdapter
from linguistics.sarf_parser import MorphologicalAnalysis
from core.layer1_graph import Layer1HeuristicGraph
from core.layer2_rules import Layer2RuleEngine
from schools.base_usul import AbstractSchoolUsul

class EpistemicOrchestrator:
    def __init__(self, adapter: IlmWadAdapter, l1: Layer1HeuristicGraph, l2: Layer2RuleEngine, l3_circuit_breaker):
        self.adapter = adapter
        self.l1 = l1
        self.l2 = l2
        self.l3 = l3_circuit_breaker

    def _extract_conflict_nodes_from_core(self, unsat_core: str) -> List[str]:
        conflict_nodes = set()
        matches = re.findall(r'AXIOM_[A-Z]+_([A-Za-z0-9_]+)', unsat_core)
        for match in matches:
            parts = match.split('_AND_')
            conflict_nodes.update(parts)
        return list(conflict_nodes)

    def process_statement(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]], usul_profile: AbstractSchoolUsul, auto_lexicon: Dict[str, MorphologicalAnalysis] = None) -> Dict[str, Any]:
        max_tevil_retries = usul_profile.dsl_ruleset.get("max_tevil_retries", 1)
        current_attempt = 0
        tevil_flagged_nodes = []
        
        while current_attempt <= max_tevil_retries:
            ir_matrix = self.adapter.generate_ir(
                tokens, dependencies, usul_profile.namespace, auto_lexicon, tevil_fallback_nodes=tevil_flagged_nodes
            )
            
            if not ir_matrix.is_valid_for_z3:
                return {
                    "status": "PRAGMATICS_REJECT", 
                    "message": "İlm-i Ma'ânî İhlali: İnşâî form mantık motoruna giremez."
                }
            
            # [LOGIC FIX]: current_attempt artık usûl katmanına geçiriliyor.
            execution_result = usul_profile.execute_dag(ir_matrix, self.l1, self.l2, self.l3, current_attempt)
            
            if execution_result.get("status") == "FALLBACK_TRIGGERED" and current_attempt < max_tevil_retries:
                if usul_profile.dsl_ruleset.get("allow_tevil", False):
                    unsat_core_str = str(execution_result.get("unsat_core", ""))
                    conflicts = self._extract_conflict_nodes_from_core(unsat_core_str)
                    
                    if conflicts:
                        tevil_flagged_nodes.extend(conflicts)
                        current_attempt += 1
                        continue
                    else:
                        break
                else:
                    break

            if current_attempt > 0 and execution_result.get("status") == "SAT":
                execution_result["tevil_applied"] = True
                execution_result["message"] += f" (Te'vil uygulandı: {tevil_flagged_nodes})"
                
            return execution_result
            
        return execution_result