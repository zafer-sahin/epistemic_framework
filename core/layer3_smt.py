import z3
from typing import Dict, Any, Tuple
from core.logic_engine import AristotelianSolver
from linguistics.ilm_wad_adapter import SemanticStatementIR

class Layer3SMTCircuitBreaker:
    """
    İzole Z3 Çözücü Katmanı (Devre Kesici ve Cache Motoru).
    Kombinatoryal patlamayı engellemek için Idempotent (tekrarlayan) 
    matrisleri önbellekten (Memoization) çözer.
    """
    def __init__(self, solver: AristotelianSolver, timeout_ms: int = 2000):
        self.core_solver = solver
        self.core_solver.solver.set("timeout", timeout_ms)
        self._memoization_cache: Dict[Tuple, Dict[str, Any]] = {}

    def execute_sat_check(self, ir_matrix: SemanticStatementIR) -> Dict[str, Any]:
        """Güvenli ve izole edilmiş Z3 SAT çözümü. Tekrarlı işlemler O(1) maliyetle cache'den döner."""
        
        # Matrisin benzersiz (hashable) imzasını çıkart
        matrix_signature = tuple(sorted(ir_matrix.predicates))
        if matrix_signature in self._memoization_cache:
            return self._memoization_cache[matrix_signature]

        self.core_solver.solver.push()
        
        try:
            for pred_id, arg_id, arity in ir_matrix.predicates:
                if arity == 1:
                    entity_const = z3.Const(arg_id, self.core_solver.builder.EntitySort)
                    predicate = self.core_solver.builder.get_or_create_predicate(pred_id, arity=1)
                    self.core_solver.solver.add(predicate(entity_const))
                
                elif arity == 2:
                    amil_str, mamul_str = arg_id.split('_', 1) 
                    amil_const = z3.Const(amil_str, self.core_solver.builder.EntitySort)
                    mamul_const = z3.Const(mamul_str, self.core_solver.builder.EntitySort)
                    
                    predicate = self.core_solver.builder.get_or_create_predicate(pred_id, arity=2)
                    self.core_solver.solver.add(predicate(amil_const, mamul_const))
            
            result = self.core_solver.solver.check()
            
            if result == z3.sat:
                response = {"status": "SAT", "message": "Ontolojik Uyum Sağlandı."}
            elif result == z3.unsat:
                core = self.core_solver.solver.unsat_core()
                response = {"status": "UNSAT", "message": f"Ontolojik Çelişki: {[str(c) for c in core]}"}
            else:
                response = {"status": "UNKNOWN", "message": f"Devre Kesici Tetiklendi veya Kararsız Durum: {self.core_solver.solver.reason_unknown()}"}
                
            self._memoization_cache[matrix_signature] = response
            return response
            
        except Exception as e:
            return {"status": "ERROR", "message": f"L3 SMT Derleme Çöküşü: {e}"}
        finally:
            self.core_solver.solver.pop()