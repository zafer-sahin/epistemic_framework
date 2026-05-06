import z3
import itertools # Yatay kombinasyonlar için zorunlu
from typing import Dict, List, Tuple
from core.models import BaseOntology, EpistemicEntity
from core.logic_parser import Z3ExpressionBuilder

class AristotelianSolver:
    """
    Porphyrios Ağacını ve Tasım (Syllogism) kurallarını Z3 SMT Çözücüsüne
    bağlayan deterministik mantık motoru.
    """
    def __init__(self, ontology: BaseOntology):
        # Unsat Core analizi için çözücü özel parametrelerle başlatılır.
        self.solver = z3.Solver()
        self.solver.set(unsat_core=True)
        
        self.ontology = ontology
        self.builder = Z3ExpressionBuilder()
        
        self._hydrate_ontological_axioms()

    def _hydrate_ontological_axioms(self) -> None:
        """
        Pydantic veri modelindeki Porphyrios Ağacını özyinelemeli (recursive)
        olarak tarar ve Z3 evrenindeki varoluşsal/geçişli kısıtları üretir.
        """
        root_entity = self.ontology.porphyrian_tree.root
        self._traverse_and_assert(root_entity)

    def _traverse_and_assert(self, entity: EpistemicEntity) -> None:
        """
        1. Vacuous Truth İzolasyonu: Evrende bu cinsten/nevden en az bir nesne var olmalıdır.
        2. Hiyerarşi İzolasyonu: Alt küme elemanları (Species), üst küme (Genus) kurallarına tabidir.
        """
        # Sınıfı temsil eden yüklemi (Predicate) Z3'e kaydet (Örn: 'Substantia')
        predicate = self.builder.get_or_create_predicate(entity.name)
        x = z3.Const(f"x_{entity.name}", self.builder.EntitySort)
        
        # KURAL 1: Varoluş (Existence)
        # ∃x. P(x)
        existence_axiom = z3.Exists([x], predicate(x))
        self.solver.assert_and_track(existence_axiom, f"AXIOM_EXISTENCE_{entity.name}")
        
        # KURAL 2: Hiyerarşik Geçişlilik (Transitivity)
        # Alt düğümler taranır. ∀y. (Child(y) => Parent(y))
        for child in entity.children:
            child_pred = self.builder.get_or_create_predicate(child.name)
            y = z3.Const(f"y_{child.name}_trans", self.builder.EntitySort)
            
            transitivity_axiom = z3.ForAll([y], z3.Implies(child_pred(y), predicate(y)))
            self.solver.assert_and_track(
                transitivity_axiom, 
                f"AXIOM_HIERARCHY_{child.name}_IMPLIES_{entity.name}"
            )
        
        # KURAL 3: Yatay Dışlama (Sibling Disjointness)
        # Matematiksel Formül: \forall z . \neg (A(z) \land B(z))
        if len(entity.children) > 1:
            for child_a, child_b in itertools.combinations(entity.children, 2):
                pred_a = self.builder.get_or_create_predicate(child_a.name)
                pred_b = self.builder.get_or_create_predicate(child_b.name)
                z = z3.Const(f"z_disjoint_{child_a.name}_{child_b.name}", self.builder.EntitySort)
                
                disjoint_axiom = z3.ForAll([z], z3.Not(z3.And(pred_a(z), pred_b(z))))
                self.solver.assert_and_track(
                    disjoint_axiom,
                    f"AXIOM_DISJOINT_{child_a.name}_AND_{child_b.name}"
                )

        # KURAL 4: Fasıl (Differentia) İzolasyonu
        # ∀x. (Species(x) -> Differentia(x))
        if entity.differentia:
            # Geçerli bir sembol ismi üret (Tercihen İngilizce veya Türkçe üzerinden)
            diff_base = entity.differentia.en or entity.differentia.tr or "Diff"
            diff_name = f"Diff_{entity.name}_{diff_base.replace(' ', '_')}"
            diff_pred = self.builder.get_or_create_predicate(diff_name)
            
            diff_axiom = z3.ForAll([x], z3.Implies(predicate(x), diff_pred(x)))
            self.solver.assert_and_track(diff_axiom, f"AXIOM_DIFFERENTIA_{entity.name}")

        # KURAL 5: Hâssa (Proprium) - Karşılıklı Gerektirme (Bi-conditional Split)
        for prop in entity.propria:
            prop_base = prop.en or prop.tr or "Prop"
            prop_name = f"Prop_{entity.name}_{prop_base.replace(' ', '_')}"
            prop_pred = self.builder.get_or_create_predicate(prop_name)
            
            # Vektör 1: Tür -> Hâssa
            prop_axiom_forward = z3.ForAll([x], z3.Implies(predicate(x), prop_pred(x)))
            self.solver.assert_and_track(
                prop_axiom_forward, 
                f"AXIOM_PROP_FWD_{entity.name}_{prop_base}"
            )
            
            # Vektör 2: Hâssa -> Tür
            prop_axiom_backward = z3.ForAll([x], z3.Implies(prop_pred(x), predicate(x)))
            self.solver.assert_and_track(
                prop_axiom_backward, 
                f"AXIOM_PROP_BWD_{entity.name}_{prop_base}"
            )

        # KURAL 6: Çapraz Kesişim ve İlişkisel Bağımlılıklar (Relational Edges)
        # N-ary (Çok değişkenli) FOL formüllerini Z3'e derler. 
        # Örn: Amil-Mamul, İlliyet (Nedensellik), Soruşturma Kısıtları.
        for relation in entity.relations:
            try:
                # String formatındaki aksiyomu AST'ye çevir.
                rel_axiom = self.builder.parse(relation.axiom)
                
                # Z3 evrenine takip edilebilir (trackable) bir kısıt olarak ekle
                self.solver.assert_and_track(
                    rel_axiom,
                    f"AXIOM_REL_{relation.relation_type.upper()}_{entity.name}_TO_{relation.target}"
                )
            except Exception as e:
                # Fail-Fast: İlişkisel sözdizimi hatalıysa sistemi doğrudan çökert.
                raise RuntimeError(f"[ÇÖKÜŞ] İlişkisel Aksiyom Derleme Hatası (Kaynak: {entity.name}): {e}")

        # MUTLAK REKÜRSİYON (DFS) - KAPSAM DÜZELTMESİ
        # Hiçbir if/for bloğuna (Kural 4 veya 5) bağlı olmadan, metodun kök girintisinde (indentation) 
        # yer almalıdır. Ağacın tüm alt dallarını eksiksiz taramayı garanti eder.
        for child in entity.children:
            self._traverse_and_assert(child)

    def check_consistency(self) -> Tuple[bool, List[str]]:
        """
        Ontolojik ağacın ve tanımlanan aksiyomların tatmin edilebilirliğini (SAT) denetler.
        Çelişki varsa Unsat Core dizisini döndürür.
        """
        result = self.solver.check()
        
        if result == z3.sat:
            return True, ["Ontoloji Mantıksal Olarak Tutarlı (SAT)."]
        elif result == z3.unsat:
            core = self.solver.unsat_core()
            core_names = [str(c) for c in core]
            return False, core_names
        else:
            raise RuntimeError(f"Z3 Çözücü Kararsız Durumda (UNKNOWN). Neden: {self.solver.reason_unknown()}")

    def verify_syllogism(self, premises: List[str], conclusion: str) -> bool:
        """
        Dışarıdan verilen bir kıyasın (Syllogism) ontolojik ağaç üzerinde
        geçerli olup olmadığını test eder. (Proof by Contradiction)
        """
        self.solver.push() # Mevcut ontolojik durumu korumak için scope aç (Backtracking)
        
        try:
            # Öncülleri (Premises) evrene ekle
            for premise in premises:
                z3_premise = self.builder.parse(premise)
                self.solver.add(z3_premise)
            
            # Çelişkiyle İspat: Sonucun (Conclusion) DEĞİLİNİ ekle
            z3_conclusion = self.builder.parse(conclusion)
            self.solver.add(z3.Not(z3_conclusion))
            
            # Eğer 'Öncüller + Değil(Sonuç)' çelişki (UNSAT) yaratıyorsa, sonuç ZORUNLUDUR (Geçerli).
            result = self.solver.check()
            return result == z3.unsat
            
        finally:
            self.solver.pop() # Geçici kısıtları çöpe at, evreni başlangıç durumuna döndür