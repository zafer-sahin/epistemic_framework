import z3
from typing import Dict, Any, List, Tuple
import re
from linguistics.ilm_wad_adapter import IlmWadAdapter, SemanticStatementIR
from linguistics.sarf_parser import MorphologicalAnalysis
from core.layer1_graph import Layer1HeuristicGraph
from core.layer2_rules import Layer2RuleEngine
from schools.base_usul import AbstractSchoolUsul

class EpistemicOrchestrator:
    """
    Bilişsel Çıkarım Motoru (Pipeline Manager).
    Faz 4 - Adım 2: Çapraz-Usûl (Cross-School) Mu'aradah Orkestrasyonu.
    Faz 2 - Adım 2.5: İlm-i Ma'ânî (Muktazâ el-Hâl) ihlallerinin loglanması.
    Rakip iki ekolün ontolojik sınırlarını eşzamanlı olarak çarpıştırır.
    """
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
        
        has_condition = any(t.lower() in ["in", "iza", "law", "amma", "imma", "aw", "ya"] for t in tokens)
        proposition_type = "Kadiyye-i_Sartiyye" if has_condition else "Kadiyye-i_Hamliyye"
        
        while current_attempt <= max_tevil_retries:
            ir_matrix = self.adapter.generate_ir(
                tokens, dependencies, usul_profile.namespace, auto_lexicon, tevil_flagged_nodes, proposition_type
            )
            
            # [FAZ 2.5] PragmaticsFilter yerine MaaniSpeechActAnalyzer reddi yakalanır
            if not ir_matrix.is_valid_for_z3:
                return {
                    "status": "PRAGMATICS_REJECT", 
                    "message": "İlm-i Ma'ânî İhlali: İnşâî form (İstifham-ı Hakikî) veya Muktazâ el-Hâl uyumsuzluğu."
                }
            
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

    def execute_cross_school_muaradah(self, 
                                      mujib_claim_ir: SemanticStatementIR, 
                                      mujib_usul: AbstractSchoolUsul, 
                                      sail_tokens: List[str],
                                      sail_dependencies: List[Tuple[str, str, str, str]],
                                      sail_usul: AbstractSchoolUsul,
                                      sail_auto_lexicon: Dict[str, MorphologicalAnalysis] = None) -> Dict[str, Any]:
        """Z3 Push/Pop İzolasyonu ile Çapraz Sorgu (Mu'aradah)."""
        sail_native_ir = self.adapter.generate_ir(sail_tokens, sail_dependencies, sail_usul.namespace, sail_auto_lexicon)
        sail_result = sail_usul.execute_dag(sail_native_ir, self.l1, self.l2, self.l3, current_attempt=0)

        if sail_result["status"] not in ["SAT", "FALLBACK_TRIGGERED"]:
            return {
                "status": "MUARADAH_FAILED",
                "message": f"Sâil'in karşı delili kendi L2/L3 uzayında ({sail_usul.namespace}) geçersiz: {sail_result.get('reason', sail_result.get('message'))}"
            }

        cross_injected_ir = self.adapter.generate_ir(sail_tokens, sail_dependencies, mujib_usul.namespace, sail_auto_lexicon)

        self.l3.core_solver.solver.push()
        try:
            mujib_base_result = self.l3.execute_sat_check(mujib_claim_ir)
            
            if mujib_base_result["status"] != "SAT":
                 return {"status": "MUJIB_INVALID", "message": "Mucîb'in kendi iddiası çapraz sorguya girmeden çöktü."}

            w_base = z3.Const('w_base', self.l3.core_solver.builder.WorldSort)
            t_base = z3.Const('t_base', self.l3.core_solver.builder.TimeSort)
            
            for item in mujib_claim_ir.predicates:
                z3_expr = self.l3._build_z3_expr(item, w_base, t_base)
                self.l3.core_solver.solver.add(z3_expr)
                
            for item in cross_injected_ir.predicates:
                z3_expr = self.l3._build_z3_expr(item, w_base, t_base)
                self.l3.core_solver.solver.add(z3_expr)

            cross_status = self.l3.core_solver.solver.check()

            if cross_status == z3.unsat:
                return {
                    "status": "MUARADAH_SUCCESS",
                    "message": f"Mu'aradah Başarılı: Sâil ({sail_usul.namespace}), Mucîb'in ({mujib_usul.namespace}) ontolojik uzayında çelişki (UNSAT) yarattı. Diyalektik Stalemate."
                }
            else:
                return {
                    "status": "MUARADAH_INEFFECTIVE",
                    "message": "Mu'aradah Başarısız: Sâil'in karşı delili Mucîb'in argümanıyla sentaktik veya semantik bir çelişki yaratmadı (Paralel Gerçeklik)."
                }
        finally:
            self.l3.core_solver.solver.pop()