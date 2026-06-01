from typing import Dict, Any
from schools.base_usul import AbstractSchoolUsul
from linguistics.ilm_wad_adapter import SemanticStatementIR

class MaturidiUsul(AbstractSchoolUsul):
    """
    Mâtürîdî Yönlü Asiklik Çizgesi (DAG) ve DSL Kuralları.
    Eş'arîlikten farklı olarak 'Tekvin' ve fiilî sıfatlarda katı 
    ontolojik kısıtlar (Blocked Nodes) uygular.
    """
    @property
    def namespace(self) -> str:
        return "Maturidi"

    @property
    def dsl_ruleset(self) -> Dict[str, Any]:
        return {
            "allow_tevil": True,
            "blocked_nodes": ["Tekvin", "Hikmet"] # Bu ontolojik düğümlerde te'vil mekanizması kilitlenir.
        }

    def execute_dag(self, ir_matrix: SemanticStatementIR, l1_engine, l2_engine, l3_engine) -> Dict[str, Any]:
        l1_analysis = l1_engine.analyze_ir(ir_matrix)
        
        l2_decision = l2_engine.enforce_rules(
            is_metaphor_likely=l1_analysis.get("is_metaphor_likely", False), 
            ruleset=self.dsl_ruleset, 
            flagged_elements=l1_analysis.get("flagged_elements", [])
        )
        
        # Mâtürîdî spesifik blokajı
        if l2_decision["action"] == "BLOCK":
            return {
                "status": "REJECTED_BY_USUL", 
                "reason": f"[Mâtürîdî Otoritesi Reddi] {l2_decision['reason']}"
            }
            
        l3_result = l3_engine.execute_sat_check(ir_matrix)
        
        if l3_result["status"] == "UNSAT":
            return {
                "status": "FALLBACK_TRIGGERED",
                "message": "Z3 Çelişkisi tespit edildi. Te'vil döngüsü devrede.",
                "unsat_core": l3_result["message"],
                "l2_context": l2_decision["action"]
            }
            
        return {**l3_result, "l2_context": l2_decision["action"]}