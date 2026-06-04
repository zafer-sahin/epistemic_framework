import z3
from typing import Dict, Any, Tuple, Union, List
from core.logic_engine import AristotelianSolver
from linguistics.ilm_wad_adapter import SemanticStatementIR, NestedPredicate

class Layer3SMTCircuitBreaker:
    def __init__(self, solver: AristotelianSolver, timeout_ms: int = 3000):
        self.core_solver = solver
        
        self.core_solver.solver.set("timeout", timeout_ms)
        self.core_solver.solver.set("smt.mbqi", True)
        self.core_solver.solver.set("smt.macro_finder", True)
        
        self._memoization_cache: Dict[Tuple, Dict[str, Any]] = {}
        self._proven_bridges = set()
        self._active_bridge_axioms = []

    def _freeze_ir_matrix(self, predicates: list) -> Tuple:
        frozen_elements = []
        for item in predicates:
            if isinstance(item, tuple):
                frozen_elements.append(item)
            elif isinstance(item, NestedPredicate):
                frozen_elements.append((item.operator, self._freeze_ir_matrix(item.args)))
        return tuple(sorted(frozen_elements, key=lambda x: str(x)))

    def _build_z3_expr(self, item: Union[Tuple[str, str, int], NestedPredicate], w_const: z3.ExprRef, tz_const: z3.ExprRef, tv_const: z3.ExprRef) -> z3.ExprRef:
        if isinstance(item, tuple):
            pred_id, arg_id, arity = item
            if arity == 1:
                entity_const = z3.Const(arg_id, self.core_solver.builder.EntitySort)
                predicate = self.core_solver.builder.get_or_create_predicate(pred_id, arity=1)
                return predicate(w_const, tz_const, tv_const, entity_const)
            elif arity == 2:
                amil_str, mamul_str = arg_id.split('::', 1) 
                amil_const = z3.Const(amil_str, self.core_solver.builder.EntitySort)
                mamul_const = z3.Const(mamul_str, self.core_solver.builder.EntitySort)
                
                if pred_id in ["Rel_Mudaf_MudafIlayh", "Rel_Mubteda_Haber"]:
                    return amil_const == mamul_const
                
                predicate = self.core_solver.builder.get_or_create_predicate(pred_id, arity=2)
                return predicate(w_const, tz_const, tv_const, amil_const, mamul_const)
            else:
                raise ValueError(f"[SENTAKS İHLALİ] Desteklenmeyen arite: {arity}")
        else:
            args = [self._build_z3_expr(a, w_const, tz_const, tv_const) for a in item.args]
            
            if item.operator == "Luzumi":
                if len(args) == 2:
                    return z3.Implies(args[0], args[1])
                return z3.And(args) 
            elif item.operator == "Inadi_Hakikiyye":
                if len(args) == 2:
                    return z3.And(z3.Or(args[0], args[1]), z3.Not(z3.And(args[0], args[1])))
                return z3.Or(args)
            elif item.operator == "Inadi_Maniatul_Cem":
                if len(args) == 2:
                    return z3.Not(z3.And(args[0], args[1]))
                return z3.Not(z3.And(args))
            elif item.operator == "Inadi_Maniatul_Huluv":
                if len(args) == 2:
                    return z3.Or(args[0], args[1])
                return z3.Or(args)
            elif item.operator == "Wajib_Fiqh":
                body = args[0] if len(args) == 1 else z3.And(args)
                # [FAZ 2 ENTEGRASYONU] Deontik (Emir) Zaman Kilitlenmesi Çözüldü.
                # Emirler mutlak zâtî doğa yasası değildir, vasfî zamandaki eylemsel lüzumiyettir.
                return z3.ForAll([w_const, tv_const], body)
            elif item.operator == "Haram_Fiqh":
                body = args[0] if len(args) == 1 else z3.And(args)
                # [FAZ 2 ENTEGRASYONU] Nehiyler (Yasaklar) vasfî zaman düzleminde varoluşsal yokluktur.
                return z3.Not(z3.Exists([w_const, tv_const], body))
            elif item.operator == "Istifham_Inkari":
                body = args[0] if len(args) == 1 else z3.And(args)
                return z3.ForAll([w_const, tz_const, tv_const], z3.Not(body))
            elif item.operator == "Kasr_Sifat_to_Mevsuf":
                # [FAZ 2 ENTEGRASYONU] Yönlü Kasr (Sıfatın Mevsufa Hasredilmesi)
                # ∀y (y ≠ Target ⇒ ¬Predicate(w, tz, tv, Amil, y))
                base_truth = args[0] if len(args) == 1 else z3.And(args)
                exclusion_axioms = []
                
                for a in item.args:
                    if isinstance(a, tuple) and a[2] == 2 and '::' in a[1]:
                        pred_id, arg_id, arity = a
                        amil_str, mamul_str = arg_id.split('::', 1)
                        predicate = self.core_solver.builder.get_or_create_predicate(pred_id, arity=2)
                        
                        y_kasr = z3.Const('y_kasr', self.core_solver.builder.EntitySort)
                        amil_const = z3.Const(amil_str, self.core_solver.builder.EntitySort)
                        mamul_const = z3.Const(mamul_str, self.core_solver.builder.EntitySort)
                        
                        exclusion = z3.ForAll([w_const, tz_const, tv_const, y_kasr],
                            z3.Implies(
                                y_kasr != mamul_const,
                                z3.Not(predicate(w_const, tz_const, tv_const, amil_const, y_kasr))
                            )
                        )
                        exclusion_axioms.append(exclusion)
                        
                if exclusion_axioms:
                    return z3.And(base_truth, *exclusion_axioms)
                return base_truth
            elif item.operator == "Kasr_Mevsuf_to_Sifat":
                # [FAZ 2 ENTEGRASYONU] Yönlü Kasr (Mevsufun Sıfata Hasredilmesi)
                # ∀x (x ≠ Amil ⇒ ¬Predicate(w, tz, tv, x, Target))
                base_truth = args[0] if len(args) == 1 else z3.And(args)
                exclusion_axioms = []
                
                for a in item.args:
                    if isinstance(a, tuple) and a[2] == 2 and '::' in a[1]:
                        pred_id, arg_id, arity = a
                        amil_str, mamul_str = arg_id.split('::', 1)
                        predicate = self.core_solver.builder.get_or_create_predicate(pred_id, arity=2)
                        
                        x_kasr = z3.Const('x_kasr', self.core_solver.builder.EntitySort)
                        amil_const = z3.Const(amil_str, self.core_solver.builder.EntitySort)
                        mamul_const = z3.Const(mamul_str, self.core_solver.builder.EntitySort)
                        
                        exclusion = z3.ForAll([w_const, tz_const, tv_const, x_kasr],
                            z3.Implies(
                                x_kasr != amil_const,
                                z3.Not(predicate(w_const, tz_const, tv_const, x_kasr, mamul_const))
                            )
                        )
                        exclusion_axioms.append(exclusion)
                        
                if exclusion_axioms:
                    return z3.And(base_truth, *exclusion_axioms)
                return base_truth
            else:
                raise ValueError(f"[SENTAKS İHLALİ] Bilinmeyen hiyerarşik operatör: {item.operator}")

    def _inject_structural_axioms(self) -> None:
        w_var = z3.Const('w_vaz', self.core_solver.builder.WorldSort)
        tz_var = z3.Const('tz_vaz', self.core_solver.builder.TimeSortZati)
        tv_var = z3.Const('tv_vaz', self.core_solver.builder.TimeSortVasfi)
        x_var = z3.Const('x_var', self.core_solver.builder.EntitySort)
        y_var = z3.Const('y_var', self.core_solver.builder.EntitySort)

        role_agent = self.core_solver.builder.get_or_create_predicate("Role_Agent", arity=1)
        role_patient = self.core_solver.builder.get_or_create_predicate("Role_Patient", arity=1)
        role_action = self.core_solver.builder.get_or_create_predicate("Role_Action", arity=1)

        agent_axiom = z3.ForAll(
            [w_var, tz_var, tv_var, x_var],
            z3.Implies(
                role_agent(w_var, tz_var, tv_var, x_var),
                z3.Exists([y_var], role_action(w_var, tz_var, tv_var, y_var))
            )
        )
        self.core_solver.solver.add(agent_axiom)

        patient_axiom = z3.ForAll(
            [w_var, tz_var, tv_var, x_var],
            z3.Implies(
                role_patient(w_var, tz_var, tv_var, x_var),
                z3.Exists([y_var], role_action(w_var, tz_var, tv_var, y_var))
            )
        )
        self.core_solver.solver.add(patient_axiom)
        
    def prove_metaphorical_bridge(self, chain: List[str]) -> bool:
        """
        [FAZ 3 ENTEGRASYONU] İlm-i Beyân Ma'nâ el-Ma'nâ İspatı.
        L1'den gelen deterministik nedensellik (Alâka) zincirini (Örn: Yed -> Bats -> Kudret) 
        Kripke Semantiğine (Olası Dünyalar ve Çift Zaman) uygun Z3 aksiyomlarına dönüştürür.
        Bu sayede te'vil (metaphor), mantıksal bir sıçrama olmaktan çıkıp ispatlanabilir bir lüzumiyet halini alır.
        """
        if not chain or len(chain) < 2:
            return False

        w_var = z3.Const('w_beyan', self.core_solver.builder.WorldSort)
        tz_var = z3.Const('tz_beyan', self.core_solver.builder.TimeSortZati)
        tv_var = z3.Const('tv_beyan', self.core_solver.builder.TimeSortVasfi)
        x_var = z3.Const('x_beyan', self.core_solver.builder.EntitySort)

        for i in range(len(chain) - 1):
            source_id = chain[i]
            target_id = chain[i+1]
            
            bridge_id = f"AXIOM_MANA_EL_MANA_{source_id}_TO_{target_id}"
            
            if bridge_id in self._proven_bridges:
                continue

            source_pred = self.core_solver.builder.get_or_create_predicate(source_id, arity=1)
            target_pred = self.core_solver.builder.get_or_create_predicate(target_id, arity=1)

            # Lüzum-u Zihnî: Kaynağın (Lafz) var olduğu her olası dünya ve zamanda, 
            # hedefin (Ma'nâ el-Ma'nâ) de var olması zorunludur.
            bridge_axiom = z3.ForAll(
                [w_var, tz_var, tv_var, x_var],
                z3.Implies(source_pred(w_var, tz_var, tv_var, x_var), target_pred(w_var, tz_var, tv_var, x_var))
            )
            
            self._active_bridge_axioms.append(bridge_axiom)
            self._proven_bridges.add(bridge_id)
            
        return True

    def execute_sat_check(self, ir_matrix: SemanticStatementIR) -> Dict[str, Any]:
        matrix_signature = self._freeze_ir_matrix(ir_matrix.predicates)
        
        if matrix_signature in self._memoization_cache:
            return self._memoization_cache[matrix_signature]

        self.core_solver.solver.push()
        
        try:
            self._inject_structural_axioms()
            
            for b_axiom in self._active_bridge_axioms:
                self.core_solver.solver.add(b_axiom)

            w_base = z3.Const('w_base', self.core_solver.builder.WorldSort)
            tz_base = z3.Const('tz_base', self.core_solver.builder.TimeSortZati)
            tv_base = z3.Const('tv_base', self.core_solver.builder.TimeSortVasfi)
            
            for item in ir_matrix.predicates:
                z3_expr = self._build_z3_expr(item, w_base, tz_base, tv_base)
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