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

    def _traverse_and_assert(self, entity: EpistemicEntity) -> None:
        # Kök değişkeni İngilizce alias yerine mutlak ontologic_id üzerinden oluşturulur.
        predicate = self.builder.get_or_create_predicate(entity.ontologic_id)
        x = z3.Const(f"x_{entity.ontologic_id}", self.builder.EntitySort)
        
        # KURAL 1: Varoluş
        existence_axiom = z3.Exists([x], predicate(x))
        self.solver.assert_and_track(existence_axiom, f"AXIOM_EXISTENCE_{entity.ontologic_id}")
        
        # KURAL 2: Hiyerarşik Geçişlilik
        for child in entity.children:
            child_pred = self.builder.get_or_create_predicate(child.ontologic_id)
            y = z3.Const(f"y_{child.ontologic_id}_trans", self.builder.EntitySort)
            
            transitivity_axiom = z3.ForAll([y], z3.Implies(child_pred(y), predicate(y)))
            self.solver.assert_and_track(
                transitivity_axiom, 
                f"AXIOM_HIERARCHY_{child.ontologic_id}_IMPLIES_{entity.ontologic_id}"
            )
        
        # KURAL 3: Yatay Dışlama (Sibling Disjointness)
        if len(entity.children) > 1:
            for child_a, child_b in itertools.combinations(entity.children, 2):
                pred_a = self.builder.get_or_create_predicate(child_a.ontologic_id)
                pred_b = self.builder.get_or_create_predicate(child_b.ontologic_id)
                z = z3.Const(f"z_disjoint_{child_a.ontologic_id}_{child_b.ontologic_id}", self.builder.EntitySort)
                
                disjoint_axiom = z3.ForAll([z], z3.Not(z3.And(pred_a(z), pred_b(z))))
                self.solver.assert_and_track(
                    disjoint_axiom,
                    f"AXIOM_DISJOINT_{child_a.ontologic_id}_AND_{child_b.ontologic_id}"
                )

        # KURAL 4: Fasıl (Differentia) İzolasyonu
        if entity.differentia_id:
            diff_name = f"Diff_{entity.ontologic_id}_{entity.differentia_id}"
            diff_pred = self.builder.get_or_create_predicate(diff_name)
            
            diff_axiom = z3.ForAll([x], z3.Implies(predicate(x), diff_pred(x)))
            self.solver.assert_and_track(diff_axiom, f"AXIOM_DIFFERENTIA_{entity.ontologic_id}")

        # KURAL 5: Hâssa (Proprium)
        for prop_id in entity.propria_ids:
            prop_name = f"Prop_{entity.ontologic_id}_{prop_id}"
            prop_pred = self.builder.get_or_create_predicate(prop_name)
            
            prop_axiom_forward = z3.ForAll([x], z3.Implies(predicate(x), prop_pred(x)))
            self.solver.assert_and_track(prop_axiom_forward, f"AXIOM_PROP_FWD_{entity.ontologic_id}_{prop_id}")
            
            prop_axiom_backward = z3.ForAll([x], z3.Implies(prop_pred(x), predicate(x)))
            self.solver.assert_and_track(prop_axiom_backward, f"AXIOM_PROP_BWD_{entity.ontologic_id}_{prop_id}")

        # KURAL 6: N-Ary İlişkisel Kısıtlar
        for relation in entity.relations:
            try:
                rel_axiom = self.builder.parse(relation.axiom)
                self.solver.assert_and_track(
                    rel_axiom,
                    f"AXIOM_REL_{relation.relation_type.upper()}_{entity.ontologic_id}_TO_{relation.target_id}"
                )
            except Exception as e:
                raise RuntimeError(f"[ÇÖKÜŞ] İlişkisel Aksiyom Derleme Hatası (Kaynak: {entity.ontologic_id}): {e}")

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