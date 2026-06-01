import z3
from typing import Dict, Any, Tuple, Union
from core.logic_engine import AristotelianSolver
from linguistics.ilm_wad_adapter import SemanticStatementIR, NestedPredicate

class Layer3SMTCircuitBreaker:
    """
    İzole Z3 Çözücü Katmanı (Devre Kesici ve Cache Motoru).
    Faz 2 - Adım 3: Kripke Semantiği (WorldSort) ve NestedPredicate (Hiyerarşik IR)
    yapılarını destekleyen özyineli SMT derleyicisi ve derin önbellek algoritması.
    """
    def __init__(self, solver: AristotelianSolver, timeout_ms: int = 2000):
        self.core_solver = solver
        self.core_solver.solver.set("timeout", timeout_ms)
        self._memoization_cache: Dict[Tuple, Dict[str, Any]] = {}

    def _freeze_ir_matrix(self, predicates: list) -> Tuple:
        """Hiyerarşik (Nested) Pydantic listelerini Hashable (değiştirilemez) Tuple'lara dönüştürür."""
        frozen_elements = []
        for item in predicates:
            if isinstance(item, tuple):
                frozen_elements.append(item)
            elif isinstance(item, NestedPredicate):
                frozen_elements.append((item.operator, self._freeze_ir_matrix(item.args)))
        # Kombinatoryal tekrarı önlemek için düğümler sıralanarak (lexicographical) imza oluşturulur
        return tuple(sorted(frozen_elements, key=lambda x: str(x)))

    def _build_z3_expr(self, item: Union[Tuple[str, str, int], NestedPredicate], w_const: z3.ExprRef) -> z3.ExprRef:
        """IR Matrisini Z3 Node'larına dönüştüren özyineli inşacı (Recursive Builder)."""
        if isinstance(item, tuple):
            pred_id, arg_id, arity = item
            if arity == 1:
                entity_const = z3.Const(arg_id, self.core_solver.builder.EntitySort)
                predicate = self.core_solver.builder.get_or_create_predicate(pred_id, arity=1)
                return predicate(w_const, entity_const)
            elif arity == 2:
                amil_str, mamul_str = arg_id.split('_', 1) 
                amil_const = z3.Const(amil_str, self.core_solver.builder.EntitySort)
                mamul_const = z3.Const(mamul_str, self.core_solver.builder.EntitySort)
                predicate = self.core_solver.builder.get_or_create_predicate(pred_id, arity=2)
                return predicate(w_const, amil_const, mamul_const)
            else:
                raise ValueError(f"[SENTAKS İHLALİ] Desteklenmeyen arite: {arity}")
        else:
            # NestedPredicate (Kadiyye-i Şartiyye) Çözümlemesi
            args = [self._build_z3_expr(a, w_const) for a in item.args]
            if item.operator == "Luzumi":
                # Şartlı önermelerin ana omurgası (Implies)
                if len(args) == 2:
                    return z3.Implies(args[0], args[1])
                return z3.And(args) # N-Ary bağlama
            elif item.operator == "Inadi":
                if len(args) == 2:
                    return z3.And(z3.Or(args[0], args[1]), z3.Not(z3.And(args[0], args[1])))
                return z3.Or(args)
            else:
                raise ValueError(f"[SENTAKS İHLALİ] Bilinmeyen hiyerarşik operatör: {item.operator}")

    def execute_sat_check(self, ir_matrix: SemanticStatementIR) -> Dict[str, Any]:
        """Güvenli ve izole edilmiş Z3 SAT çözümü. Modal uzay destekli."""
        
        # 1. Hiyerarşik İmza Üretimi
        matrix_signature = self._freeze_ir_matrix(ir_matrix.predicates)
        
        if matrix_signature in self._memoization_cache:
            return self._memoization_cache[matrix_signature]

        self.core_solver.solver.push()
        
        try:
            # Muvaccehât (Modalite): Her önerme varsayılan bir baz uzayda (w_base) test edilir
            w_base = z3.Const('w_base', self.core_solver.builder.WorldSort)
            
            for item in ir_matrix.predicates:
                z3_expr = self._build_z3_expr(item, w_base)
                self.core_solver.solver.add(z3_expr)
            
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