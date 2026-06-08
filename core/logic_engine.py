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
        self._inject_tahayyuz_axioms()

    def _inject_tahayyuz_axioms(self) -> None:
        """
        [FAZ 4 ENTEGRASYONU] İlm-i Kelâm Mekân (Tahayyuz) ve Tenzih Aksiyomları.
        Vâcibu'l-Vücûd mekândan münezzehtir (LocatedIn bağımsızdır).
        Cism (Cisim) ve Araz'lar ise mutlak surette bir mekâna (SpaceSort) muhtaçtır.
        Bu metod, teolojik tenzih prensibini Z3 FOL matrisinde donanımsal bir kısıta çevirir.
        """
        try:
            wajib_pred = self.builder.get_or_create_predicate("Wajib_al_Wujud", arity=1)
            cism_pred = self.builder.get_or_create_predicate("Cism", arity=1)
            
            w_tahayyuz = z3.Const('w_tahayyuz', self.builder.WorldSort)
            tz_tahayyuz = z3.Const('tz_tahayyuz', self.builder.TimeSortZati)
            tv_tahayyuz = z3.Const('tv_tahayyuz', self.builder.TimeSortVasfi)
            s_tahayyuz = z3.Const('s_tahayyuz', self.builder.SpaceSort)
            x_tahayyuz = z3.Const('x_tahayyuz', self.builder.EntitySort)

            # Tenzih Aksiyomu: Zorunlu Varlık hiçbir mekânsal düzlemde (SpaceSort) bulunamaz.
            tenzih_axiom = z3.ForAll([w_tahayyuz, tz_tahayyuz, tv_tahayyuz, s_tahayyuz, x_tahayyuz],
                z3.Implies(
                    wajib_pred(w_tahayyuz, tz_tahayyuz, tv_tahayyuz, s_tahayyuz, x_tahayyuz),
                    z3.Not(self.builder.LocatedIn(w_tahayyuz, tz_tahayyuz, tv_tahayyuz, s_tahayyuz, x_tahayyuz))
                )
            )
            self.solver.assert_and_track(tenzih_axiom, "AXIOM_TENZIH_WAJIB_AL_WUJUD")

            # Tahayyuz Aksiyomu: Her Cisim (Cism) mutlak surette bir mekânda (SpaceSort) bulunmak zorundadır.
            s_loc = z3.Const('s_loc', self.builder.SpaceSort)
            tahayyuz_axiom = z3.ForAll([w_tahayyuz, tz_tahayyuz, tv_tahayyuz, s_tahayyuz, x_tahayyuz],
                z3.Implies(
                    cism_pred(w_tahayyuz, tz_tahayyuz, tv_tahayyuz, s_tahayyuz, x_tahayyuz),
                    z3.Exists([s_loc], self.builder.LocatedIn(w_tahayyuz, tz_tahayyuz, tv_tahayyuz, s_loc, x_tahayyuz))
                )
            )
            self.solver.assert_and_track(tahayyuz_axiom, "AXIOM_TAHAYYUZ_CISM")

        except ValueError:
            pass # Test ortamında veya daraltılmış ontolojide bu düğümler yoksa yoksay

    def _inject_kalamic_causality(self) -> None:
        """
        [FAZ 4 - Güncelleme] İmkân ve Nedensellik (Kalamic Causality)
        Kripke uzayındaki her Mümkin varlık Zorunlu varlığa bağlanır.
        SpaceSort (s_causality) boyutu ariteye eklendi.
        """
        try:
            wajib_pred = self.builder.get_or_create_predicate("Wajib_al_Wujud", arity=1)
            mumkin_pred = self.builder.get_or_create_predicate("Mumkin_al_Wujud", arity=1)
            
            w = z3.Const('w_causality', self.builder.WorldSort)
            tz = z3.Const('tz_causality', self.builder.TimeSortZati)
            tv = z3.Const('tv_causality', self.builder.TimeSortVasfi)
            s = z3.Const('s_causality', self.builder.SpaceSort)
            x_mumkin = z3.Const('x_mumkin', self.builder.EntitySort)
            y_wajib = z3.Const('y_wajib', self.builder.EntitySort)
            s_wajib = z3.Const('s_wajib', self.builder.SpaceSort)

            causality_axiom = z3.ForAll([w, tz, tv, s, x_mumkin],
                z3.Implies(
                    mumkin_pred(w, tz, tv, s, x_mumkin),
                    z3.Exists([y_wajib, s_wajib], wajib_pred(w, tz, tv, s_wajib, y_wajib))
                )
            )
            self.solver.assert_and_track(causality_axiom, "AXIOM_KALAMIC_CAUSALITY_DEPENDENCE")
        except ValueError:
            pass 

    def _traverse_and_assert(self, entity: EpistemicEntity) -> None:
        predicate = self.builder.get_or_create_predicate(entity.ontologic_id)
        x = z3.Const(f"x_{entity.ontologic_id}", self.builder.EntitySort)
        w = z3.Const(f"w_{entity.ontologic_id}", self.builder.WorldSort)
        tz = z3.Const(f"tz_{entity.ontologic_id}", self.builder.TimeSortZati)
        tv = z3.Const(f"tv_{entity.ontologic_id}", self.builder.TimeSortVasfi)
        s = z3.Const(f"s_{entity.ontologic_id}", self.builder.SpaceSort)
        
        if entity.modal_status in ["Wajib", "Zaruriyye_i_Mutlaka"]:
            existence_axiom = z3.Exists([x], z3.ForAll([w, tz, tv, s], predicate(w, tz, tv, s, x)))
            self.solver.assert_and_track(existence_axiom, f"AXIOM_EXISTENCE_{entity.ontologic_id}_{entity.modal_status}")
            
        elif entity.modal_status == "Daime_i_Mutlaka":
            existence_axiom = z3.Exists([w, x], z3.ForAll([tz, tv, s], predicate(w, tz, tv, s, x)))
            self.solver.assert_and_track(existence_axiom, f"AXIOM_EXISTENCE_{entity.ontologic_id}_{entity.modal_status}")
            
        elif entity.modal_status == "Mustahil":
            existence_axiom = z3.ForAll([w, tz, tv, s, x], z3.Not(predicate(w, tz, tv, s, x)))
            self.solver.assert_and_track(existence_axiom, f"AXIOM_EXISTENCE_{entity.ontologic_id}_{entity.modal_status}")
            
        elif entity.modal_status == "Mesruta_i_Amme" and entity.modal_condition_id:
            condition_pred = self.builder.get_or_create_predicate(entity.modal_condition_id)
            existence_axiom = z3.ForAll([w, tz, tv, s, x], 
                z3.Implies(condition_pred(w, tz, tv, s, x), predicate(w, tz, tv, s, x))
            )
            self.solver.assert_and_track(existence_axiom, f"AXIOM_EXISTENCE_{entity.ontologic_id}_{entity.modal_status}")
            
        elif entity.modal_status == "Orfiyye_i_Amme" and entity.modal_condition_id:
            condition_pred = self.builder.get_or_create_predicate(entity.modal_condition_id)
            existence_axiom = z3.Exists([w], z3.ForAll([tz, tv, s, x], 
                z3.Implies(condition_pred(w, tz, tv, s, x), predicate(w, tz, tv, s, x))
            ))
            self.solver.assert_and_track(existence_axiom, f"AXIOM_EXISTENCE_{entity.ontologic_id}_{entity.modal_status}")
            
        else:
            pass
        
        for child in entity.children:
            child_pred = self.builder.get_or_create_predicate(child.ontologic_id)
            y = z3.Const(f"y_{child.ontologic_id}_trans", self.builder.EntitySort)
            
            transitivity_axiom = z3.ForAll([w, tz, tv, s, y], z3.Implies(child_pred(w, tz, tv, s, y), predicate(w, tz, tv, s, y)))
            self.solver.assert_and_track(
                transitivity_axiom, 
                f"AXIOM_HIERARCHY_{child.ontologic_id}_IMPLIES_{entity.ontologic_id}"
            )
            
        if len(entity.children) > 1:
            for child_a, child_b in itertools.combinations(entity.children, 2):
                pred_a = self.builder.get_or_create_predicate(child_a.ontologic_id)
                pred_b = self.builder.get_or_create_predicate(child_b.ontologic_id)
                z_var = z3.Const(f"z_disjoint_{child_a.ontologic_id}_{child_b.ontologic_id}", self.builder.EntitySort)
                
                disjoint_axiom = z3.ForAll([w, tz, tv, s, z_var], z3.Not(z3.And(pred_a(w, tz, tv, s, z_var), pred_b(w, tz, tv, s, z_var))))
                self.solver.assert_and_track(
                    disjoint_axiom,
                    f"AXIOM_DISJOINT_{child_a.ontologic_id}_AND_{child_b.ontologic_id}"
                )

        if entity.differentia_id:
            diff_name = f"Diff_{entity.ontologic_id}_{entity.differentia_id}"
            diff_pred = self.builder.get_or_create_predicate(diff_name)
            diff_axiom = z3.ForAll([w, tz, tv, s, x], z3.Implies(predicate(w, tz, tv, s, x), diff_pred(w, tz, tv, s, x)))
            self.solver.assert_and_track(diff_axiom, f"AXIOM_DIFFERENTIA_{entity.ontologic_id}")

        for prop_id in entity.propria_ids:
            prop_name = f"Prop_{entity.ontologic_id}_{prop_id}"
            prop_pred = self.builder.get_or_create_predicate(prop_name)
            
            prop_axiom_forward = z3.ForAll([w, tz, tv, s, x], z3.Implies(predicate(w, tz, tv, s, x), prop_pred(w, tz, tv, s, x)))
            self.solver.assert_and_track(prop_axiom_forward, f"AXIOM_PROP_FWD_{entity.ontologic_id}_{prop_id}")
            
            prop_axiom_backward = z3.ForAll([w, tz, tv, s, x], z3.Implies(prop_pred(w, tz, tv, s, x), predicate(w, tz, tv, s, x)))
            self.solver.assert_and_track(prop_axiom_backward, f"AXIOM_PROP_BWD_{entity.ontologic_id}_{prop_id}")

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