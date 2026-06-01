from typing import Dict, Any
from schools.base_usul import AbstractSchoolUsul
from linguistics.ilm_wad_adapter import SemanticStatementIR

class AshariUsul(AbstractSchoolUsul):
    """Eş'arî Yönlü Asiklik Çizgesi (DAG) ve DSL Kuralları."""
    @property
    def namespace(self) -> str:
        return "Ashari"

    @property
    def dsl_ruleset(self) -> Dict[str, Any]:
        return {
            "allow_tevil": True,
            "blocked_nodes": [] # Eş'arîler haberî sıfatlarda te'vile geniş izin verir. Spesifik yasak yoktur.
        }

    def execute_dag(self, ir_matrix: SemanticStatementIR, l1_engine, l2_engine, l3_engine) -> Dict[str, Any]:
        l1_analysis = l1_engine.analyze_ir(ir_matrix)
        
        l2_decision = l2_engine.enforce_rules(
            is_metaphor_likely=l1_analysis.get("is_metaphor_likely", False), 
            ruleset=self.dsl_ruleset, 
            flagged_elements=l1_analysis.get("flagged_elements", [])
        )
        
        l3_result = l3_engine.execute_sat_check(ir_matrix)
        
        if l3_result["status"] == "UNSAT":
            return {
                "status": "FALLBACK_TRIGGERED",
                "message": "Z3 Çelişkisi. Nakz yerine te'vil döngüsü tetiklendi.",
                "unsat_core": l3_result["message"],
                "l2_context": l2_decision["action"]
            }
            
        return {**l3_result, "l2_context": l2_decision["action"]}