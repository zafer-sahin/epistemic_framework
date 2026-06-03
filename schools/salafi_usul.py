from typing import Dict, Any
from schools.base_usul import AbstractSchoolUsul
from linguistics.ilm_wad_adapter import SemanticStatementIR

class SalafiUsul(AbstractSchoolUsul):
    @property
    def namespace(self) -> str:
        return "Salafi"

    @property
    def dsl_ruleset(self) -> Dict[str, Any]:
        return {
            "allow_tevil": False,
            "max_tevil_retries": 0,
            "blocked_nodes": ["ALL"] 
        }

    def execute_dag(self, ir_matrix: SemanticStatementIR, l1_engine, l2_engine, l3_engine, current_attempt: int = 0) -> Dict[str, Any]:
        l1_analysis = l1_engine.analyze_ir(ir_matrix)
        
        # [FAZ 6] Bila-Kayf Node Relocation (Düğüm Taşınması) Denetimi
        # İbn Teymiyye'nin Hakikat Felsefesine göre, eğer kelime "Bila_Kayf" düğümüne taşındıysa, 
        # ontolojik mesafe (L1) ihlali ortadan kalkar ve Mecaz riski (is_metaphor_likely) düşer.
        is_bila_kayf = any("Bila_Kayf" in str(pred) for pred in ir_matrix.predicates)
        
        l2_decision = l2_engine.enforce_rules(
            is_metaphor_likely=l1_analysis.get("is_metaphor_likely", False) and not is_bila_kayf, 
            ruleset=self.dsl_ruleset, 
            flagged_elements=l1_analysis.get("flagged_elements", []),
            current_attempt=current_attempt
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
            
        if l3_result["status"] == "SAT" and is_bila_kayf:
            return {
                "status": "SAT_BILA_KAYF",
                "message": "İbn Teymiyye Semantiği: Kelime literal (Cism) ontolojisinden koparılıp yepyeni bir Hakikat (Bilâ-Keyf) olarak Zorunlu Varlık'a bağlandı. Ontolojik uyum sağlandı.",
                "l2_context": "BILA_KAYF_NODE_RELOCATION"
            }
            
        return {**l3_result, "l2_context": l2_decision["action"]}