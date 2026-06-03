import z3
from typing import Dict, Any, Tuple, Union
from core.logic_engine import AristotelianSolver
from linguistics.ilm_wad_adapter import SemanticStatementIR, NestedPredicate

class Layer3SMTCircuitBreaker:
    def __init__(self, solver: AristotelianSolver, timeout_ms: int = 3000):
        self.core_solver = solver
        
        self.core_solver.solver.set("timeout", timeout_ms)
        self.core_solver.solver.set("smt.mbqi", True)
        self.core_solver.solver.set("smt.macro_finder", True)
        
        self._memoization_cache: Dict[Tuple, Dict[str, Any]] = {}

    def _freeze_ir_matrix(self, predicates: list) -> Tuple:
        frozen_elements = []
        for item in predicates:
            if isinstance(item, tuple):
                frozen_elements.append(item)
            elif isinstance(item, NestedPredicate):
                frozen_elements.append((item.operator, self._freeze_ir_matrix(item.args)))
        return tuple(sorted(frozen_elements, key=lambda x: str(x)))

    def _build_z3_expr(self, item: Union[Tuple[str, str, int], NestedPredicate], w_const: z3.ExprRef, t_const: z3.ExprRef) -> z3.ExprRef:
        if isinstance(item, tuple):
            pred_id, arg_id, arity = item
            if arity == 1:
                entity_const = z3.Const(arg_id, self.core_solver.builder.EntitySort)
                # [FAZ 1.4] Vaz' Nev'î Role yüklemlerinin dinamik oluşturulması
                predicate = self.core_solver.builder.get_or_create_predicate(pred_id, arity=1)
                return predicate(w_const, t_const, entity_const)
            elif arity == 2:
                amil_str, mamul_str = arg_id.split('::', 1) 
                amil_const = z3.Const(amil_str, self.core_solver.builder.EntitySort)
                mamul_const = z3.Const(mamul_str, self.core_solver.builder.EntitySort)
                
                if pred_id in ["Rel_Mudaf_MudafIlayh", "Rel_Mubteda_Haber"]:
                    return amil_const == mamul_const
                
                predicate = self.core_solver.builder.get_or_create_predicate(pred_id, arity=2)
                return predicate(w_const, t_const, amil_const, mamul_const)
            else:
                raise ValueError(f"[SENTAKS İHLALİ] Desteklenmeyen arite: {arity}")
        else:
            args = [self._build_z3_expr(a, w_const, t_const) for a in item.args]
            if item.operator == "Luzumi":
                if len(args) == 2:
                    return z3.Implies(args[0], args[1])
                return z3.And(args) 
            elif item.operator == "Inadi":
                if len(args) == 2:
                    return z3.And(z3.Or(args[0], args[1]), z3.Not(z3.And(args[0], args[1])))
                return z3.Or(args)
            elif item.operator == "Wajib_Fiqh":
                body = args[0] if len(args) == 1 else z3.And(args)
                return z3.ForAll([w_const, t_const], body)
            elif item.operator == "Haram_Fiqh":
                body = args[0] if len(args) == 1 else z3.And(args)
                return z3.Not(z3.Exists([w_const, t_const], body))
            else:
                raise ValueError(f"[SENTAKS İHLALİ] Bilinmeyen hiyerarşik operatör: {item.operator}")

    def _inject_structural_axioms(self) -> None:
        """
        [FAZ 1.4] İlm-i Vaz' Lüzumiyet Aksiyomları.
        Bir cümlede Fâ'il (Agent) veya Mef'ûl (Patient) kalıbı varsa,
        bu durum ontolojik olarak bir Eylemin (Action) varlığını zorunlu kılar.
        """
        w_var = z3.Const('w_vaz', self.core_solver.builder.WorldSort)
        t_var = z3.Const('t_vaz', self.core_solver.builder.TimeSort)
        x_var = z3.Const('x_var', self.core_solver.builder.EntitySort)
        y_var = z3.Const('y_var', self.core_solver.builder.EntitySort)

        role_agent = self.core_solver.builder.get_or_create_predicate("Role_Agent", arity=1)
        role_patient = self.core_solver.builder.get_or_create_predicate("Role_Patient", arity=1)
        role_action = self.core_solver.builder.get_or_create_predicate("Role_Action", arity=1)

        # Aksiyom 1: Agent(x) => Exists(y) Action(y)
        agent_axiom = z3.ForAll(
            [w_var, t_var, x_var],
            z3.Implies(
                role_agent(w_var, t_var, x_var),
                z3.Exists([y_var], role_action(w_var, t_var, y_var))
            )
        )
        self.core_solver.solver.assert_and_track(agent_axiom, "AXIOM_VAZ_NEVI_AGENT_REQUIRES_ACTION")

        # Aksiyom 2: Patient(x) => Exists(y) Action(y)
        patient_axiom = z3.ForAll(
            [w_var, t_var, x_var],
            z3.Implies(
                role_patient(w_var, t_var, x_var),
                z3.Exists([y_var], role_action(w_var, t_var, y_var))
            )
        )
        self.core_solver.solver.assert_and_track(patient_axiom, "AXIOM_VAZ_NEVI_PATIENT_REQUIRES_ACTION")

    def execute_sat_check(self, ir_matrix: SemanticStatementIR) -> Dict[str, Any]:
        matrix_signature = self._freeze_ir_matrix(ir_matrix.predicates)
        
        if matrix_signature in self._memoization_cache:
            return self._memoization_cache[matrix_signature]

        self.core_solver.solver.push()
        
        try:
            # [FAZ 1.4] Yapısal Aksiyomların Çözücüye Zerk Edilmesi
            self._inject_structural_axioms()

            w_base = z3.Const('w_base', self.core_solver.builder.WorldSort)
            t_base = z3.Const('t_base', self.core_solver.builder.TimeSort)
            
            for item in ir_matrix.predicates:
                z3_expr = self._build_z3_expr(item, w_base, t_base)
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