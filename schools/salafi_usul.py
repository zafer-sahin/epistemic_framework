from typing import Dict, Any
from schools.base_usul import AbstractSchoolUsul
from linguistics.ilm_wad_adapter import SemanticStatementIR

class SalafiUsul(AbstractSchoolUsul):
    """Selefî Yönlü Asiklik Çizgesi (DAG) ve DSL Kuralları."""
    @property
    def namespace(self) -> str:
        return "Salafi"

    @property
    def dsl_ruleset(self) -> Dict[str, Any]:
        return {
            "allow_tevil": False,
            "blocked_nodes": ["ALL"] # Sıkı lafızcılık (Strict Literalism). Sıfır transformasyon.
        }

    def execute_dag(self, ir_matrix: SemanticStatementIR, l1_engine, l2_engine, l3_engine) -> Dict[str, Any]:
        l1_analysis = l1_engine.analyze_ir(ir_matrix)
        
        l2_decision = l2_engine.enforce_rules(
            is_metaphor_likely=l1_analysis.get("is_metaphor_likely", False), 
            ruleset=self.dsl_ruleset, 
            flagged_elements=l1_analysis.get("flagged_elements", [])
        )
        
        if l2_decision["action"] == "BLOCK":
            return {
                "status": "REJECTED_BY_USUL", 
                "reason": f"[Selefî Usûlü İhlali] {l2_decision['reason']}"
            }
        
        l3_result = l3_engine.execute_sat_check(ir_matrix)
        
        if l3_result["status"] == "UNSAT":
            return {
                "status": "NAKZ",
                "message": f"Z3 Çelişkisi kesin çürütme (Nakz) kabul edildi. {l3_result['message']}"
            }
            
        return {**l3_result, "l2_context": l2_decision["action"]}