import z3
import itertools
from typing import Dict, List, Tuple
from core.models import BaseOntology, EpistemicEntity
from core.logic_parser import Z3ExpressionBuilder

class AristotelianSolver:
    def __init__(self, ontology: BaseOntology, active_namespace: str = "Base"):
        self.solver = z3.Solver()
        self.solver.set(unsat_core=True)
        self.ontology = ontology
        self.builder = Z3ExpressionBuilder()
        self.active_namespace = active_namespace
        
        self._hydrate_ontological_axioms()

    def _hydrate_ontological_axioms(self) -> None:
        if self.active_namespace not in self.ontology.porphyrian_tree.roots:
            raise ValueError(f"[UNKNOWN_VARIABLE] Hiyerarşi tanımsız: {self.active_namespace}")
            
        root_entity = self.ontology.porphyrian_tree.roots[self.active_namespace]
        self._traverse_and_assert(root_entity)
        self._inject_kalamic_causality()

    def _inject_kalamic_causality(self) -> None:
        """
        [FAZ 4 - Tamamlama] İmkân ve Nedensellik (Kalamic Causality)
        SMT motorunun olasılık çöküşü yaşamaması için, Kripke uzayındaki 
        her Mümkin varlık Zorunlu varlığa bağlanır.
        """
        try:
            wajib_pred = self.builder.get_or_create_predicate("Wajib_al_Wujud", arity=1)
            mumkin_pred = self.builder.get_or_create_predicate("Mumkin_al_Wujud", arity=1)
            
            w = z3.Const('w_causality', self.builder.WorldSort)
            tz = z3.Const('tz_causality', self.builder.TimeSortZati)
            tv = z3.Const('tv_causality', self.builder.TimeSortVasfi)
            x_mumkin = z3.Const('x_mumkin', self.builder.EntitySort)
            y_wajib = z3.Const('y_wajib', self.builder.EntitySort)

            # Her mümkün varlık, en az bir zorunlu varlığın (Wajib_al_Wujud) aynı dünyada ve zâtî zamanda var olmasını gerektirir.
            causality_axiom = z3.ForAll([w, tz, tv, x_mumkin],
                z3.Implies(
                    mumkin_pred(w, tz, tv, x_mumkin),
                    z3.Exists([y_wajib], wajib_pred(w, tz, tv, y_wajib))
                )
            )
            self.solver.assert_and_track(causality_axiom, "AXIOM_KALAMIC_CAUSALITY_DEPENDENCE")
        except ValueError:
            pass # Çalışılan namespace (örn. daraltılmış test uzayları) bu düğümleri içermiyorsa yoksay

    def _traverse_and_assert(self, entity: EpistemicEntity) -> None:
        predicate = self.builder.get_or_create_predicate(entity.ontologic_id)
        x = z3.Const(f"x_{entity.ontologic_id}", self.builder.EntitySort)
        w = z3.Const(f"w_{entity.ontologic_id}", self.builder.WorldSort)
        tz = z3.Const(f"tz_{entity.ontologic_id}", self.builder.TimeSortZati)
        tv = z3.Const(f"tv_{entity.ontologic_id}", self.builder.TimeSortVasfi)
        
        # [FAZ 4] KURAL 1: Çift Katmanlı Varlık ve Kiplik (Modal Status) Entegrasyonu
        if entity.modal_status in ["Wajib", "Zaruriyye_i_Mutlaka"]:
            existence_axiom = z3.Exists([x], z3.ForAll([w, tz, tv], predicate(w, tz, tv, x)))
            self.solver.assert_and_track(existence_axiom, f"AXIOM_EXISTENCE_{entity.ontologic_id}_{entity.modal_status}")
            
        elif entity.modal_status == "Daime_i_Mutlaka":
            existence_axiom = z3.Exists([w, x], z3.ForAll([tz, tv], predicate(w, tz, tv, x)))
            self.solver.assert_and_track(existence_axiom, f"AXIOM_EXISTENCE_{entity.ontologic_id}_{entity.modal_status}")
            
        elif entity.modal_status == "Mustahil":
            existence_axiom = z3.ForAll([w, tz, tv, x], z3.Not(predicate(w, tz, tv, x)))
            self.solver.assert_and_track(existence_axiom, f"AXIOM_EXISTENCE_{entity.ontologic_id}_{entity.modal_status}")
            
        elif entity.modal_status == "Mesruta_i_Amme" and entity.modal_condition_id:
            condition_pred = self.builder.get_or_create_predicate(entity.modal_condition_id)
            existence_axiom = z3.ForAll([w, tz, tv, x], 
                z3.Implies(condition_pred(w, tz, tv, x), predicate(w, tz, tv, x))
            )
            self.solver.assert_and_track(existence_axiom, f"AXIOM_EXISTENCE_{entity.ontologic_id}_{entity.modal_status}")
            
        elif entity.modal_status == "Orfiyye_i_Amme" and entity.modal_condition_id:
            condition_pred = self.builder.get_or_create_predicate(entity.modal_condition_id)
            existence_axiom = z3.Exists([w], z3.ForAll([tz, tv, x], 
                z3.Implies(condition_pred(w, tz, tv, x), predicate(w, tz, tv, x))
            ))
            self.solver.assert_and_track(existence_axiom, f"AXIOM_EXISTENCE_{entity.ontologic_id}_{entity.modal_status}")
            
        else:
            pass
        
        # KURAL 2: Hiyerarşik Geçişlilik
        for child in entity.children:
            child_pred = self.builder.get_or_create_predicate(child.ontologic_id)
            y = z3.Const(f"y_{child.ontologic_id}_trans", self.builder.EntitySort)
            
            transitivity_axiom = z3.ForAll([w, tz, tv, y], z3.Implies(child_pred(w, tz, tv, y), predicate(w, tz, tv, y)))
            self.solver.assert_and_track(
                transitivity_axiom, 
                f"AXIOM_HIERARCHY_{child.ontologic_id}_IMPLIES_{entity.ontologic_id}"
            )
            
        # KURAL 3: Yatay Dışlama (Sibling Disjointness)
        if len(entity.children) > 1:
            for child_a, child_b in itertools.combinations(entity.children, 2):
                pred_a = self.builder.get_or_create_predicate(child_a.ontologic_id)
                pred_b = self.builder.get_or_create_predicate(child_b.ontologic_id)
                z_var = z3.Const(f"z_disjoint_{child_a.ontologic_id}_{child_b.ontologic_id}", self.builder.EntitySort)
                
                disjoint_axiom = z3.ForAll([w, tz, tv, z_var], z3.Not(z3.And(pred_a(w, tz, tv, z_var), pred_b(w, tz, tv, z_var))))
                self.solver.assert_and_track(
                    disjoint_axiom,
                    f"AXIOM_DISJOINT_{child_a.ontologic_id}_AND_{child_b.ontologic_id}"
                )

        # KURAL 4: Fasıl (Differentia) İzolasyonu
        if entity.differentia_id:
            diff_name = f"Diff_{entity.ontologic_id}_{entity.differentia_id}"
            diff_pred = self.builder.get_or_create_predicate(diff_name)
            diff_axiom = z3.ForAll([w, tz, tv, x], z3.Implies(predicate(w, tz, tv, x), diff_pred(w, tz, tv, x)))
            self.solver.assert_and_track(diff_axiom, f"AXIOM_DIFFERENTIA_{entity.ontologic_id}")

        # KURAL 5: Hâssa (Proprium)
        for prop_id in entity.propria_ids:
            prop_name = f"Prop_{entity.ontologic_id}_{prop_id}"
            prop_pred = self.builder.get_or_create_predicate(prop_name)
            
            prop_axiom_forward = z3.ForAll([w, tz, tv, x], z3.Implies(predicate(w, tz, tv, x), prop_pred(w, tz, tv, x)))
            self.solver.assert_and_track(prop_axiom_forward, f"AXIOM_PROP_FWD_{entity.ontologic_id}_{prop_id}")
            
            prop_axiom_backward = z3.ForAll([w, tz, tv, x], z3.Implies(prop_pred(w, tz, tv, x), predicate(w, tz, tv, x)))
            self.solver.assert_and_track(prop_axiom_backward, f"AXIOM_PROP_BWD_{entity.ontologic_id}_{prop_id}")

        # Mutlak Rekürsiyon
        for child in entity.children:
            self._traverse_and_assert(child)

    def check_consistency(self) -> Tuple[bool, List[str]]:
        result = self.solver.check()
        if result == z3.sat:
            return True, ["Ontoloji Mantıksal Olarak Tutarlı (SAT)."]
        elif result == z3.unsat:
            core = self.solver.unsat_core()
            return False, [str(c) for c in core]
        else:
            raise RuntimeError(f"Z3 Çözücü Kararsız Durumda (UNKNOWN). Neden: {self.solver.reason_unknown()}")

    def verify_syllogism(self, premises: List[str], conclusion: str) -> bool:
        self.solver.push()
        try:
            for premise in premises:
                z3_premise = self.builder.parse(premise)
                self.solver.add(z3_premise)
            
            z3_conclusion = self.builder.parse(conclusion)
            self.solver.add(z3.Not(z3_conclusion))
            
            result = self.solver.check()
            return result == z3.unsat
        finally:
            self.solver.pop()