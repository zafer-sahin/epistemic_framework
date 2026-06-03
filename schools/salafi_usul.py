from typing import Dict, Any, Tuple
from schools.base_usul import AbstractSchoolUsul
from linguistics.ilm_wad_adapter import SemanticStatementIR

class SalafiUsul(AbstractSchoolUsul):
    """
    İbn Teymiyye Semantiği (Selefî Epistemolojisi) Otorite Motoru.
    Faz 6: Hakikat Taşınması (Node Relocation) ve Sıfır-Transformasyon Kısıtı.
    Mecazı (Te'vil) mutlak surette reddeder, ancak kelimenin bağlama göre 
    kendi 'Hakikatini' (Bila-Kayf) yaratmasını ontolojik olarak destekler.
    """
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
        
        # [FAZ 6] Bila-Kayf Node Relocation (Yapısal Hakikat Taşınması) Denetimi
        # String kontrolü yerine IR matrisinin yapısal (Tuple) analizi yapılır.
        is_bila_kayf = False
        for item in ir_matrix.predicates:
            if isinstance(item, tuple):
                pred_id = item[0]
                arg_id = item[1]
                if "Bila_Kayf" in pred_id or "Bila_Kayf" in arg_id:
                    is_bila_kayf = True
                    break
        
        # Eğer kelime Bilâ-Keyf uzayına otonom olarak (İzafet ile) taşındıysa, 
        # ontolojik mesafe (L1) ihlali (Mecaz şüphesi) sıfırlanır.
        adjusted_metaphor_likelihood = l1_analysis.get("is_metaphor_likely", False) and not is_bila_kayf
        
        l2_decision = l2_engine.enforce_rules(
            is_metaphor_likely=adjusted_metaphor_likelihood, 
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
                "message": f"Z3 Çelişkisi kesin çürütme (Nakz) kabul edildi. Gerekçe: Usûl kuralları te'vili mutlak reddeder. {l3_result['message']}"
            }
            
        if l3_result["status"] == "SAT" and is_bila_kayf:
            return {
                "status": "SAT_BILA_KAYF",
                "message": "İbn Teymiyye Semantiği: Kelime literal (Cism) ontolojisinden koparılıp yepyeni bir Hakikat (Bilâ-Keyf) olarak Zorunlu Varlık'a bağlandı. Ontolojik uyum sağlandı.",
                "l2_context": "BILA_KAYF_NODE_RELOCATION"
            }
            
        return {**l3_result, "l2_context": l2_decision["action"]}