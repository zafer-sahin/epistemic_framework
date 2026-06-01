import unittest
import z3
from pathlib import Path
from core.models import OntologyLoader
from core.logic_engine import AristotelianSolver
from core.logic_parser import Z3ExpressionBuilder

class TestZ3Engine(unittest.TestCase):
    """
    Z3 SMT çözücüsünün ontolojik sınırlar (Porphyrian Tree) dahilinde
    'Ex Falso Quodlibet' (Çelişkiden her şey çıkar) ve Combinatorial 
    Explosion zafiyetlerine karşı direncini ölçen Red-Teaming testi.
    """
    @classmethod
    def setUpClass(cls):
        loader = OntologyLoader()
        cls.ontology = loader.load(Path("data/base_ontology.json"))
        
    def setUp(self):
        self.solver = AristotelianSolver(self.ontology)
        
    def test_sibling_disjointness(self):
        """[BRQ-02] Yatay dışlama ihlali (Bir varlığın aynı anda hem İnsan hem Feres/At olması durumu)."""
        
        # Z3 formülünü str() ile çevirmek yerine, doğrudan AST motorumuzun
        # anlayacağı syntax ile payload oluşturulmalıdır.
        impossible_intersection = "Forall([x], And(Insan(x), Feres(x)))"
        
        # UNSAT beklentisi: İmkansız bir ontolojik varlık üretimi reddedilmelidir.
        is_valid = self.solver.verify_syllogism([], impossible_intersection)
        self.assertFalse(is_valid, "[KRİTİK ZAFİYET] Z3 motoru yatay kesişime izin verdi. Çelişmezlik ilkesi ihlal edildi.")

    def test_ex_falso_quodlibet_prevention(self):
        """[BRQ-04] Çelişkili öncüllerden (Premises) geçerli bir sonuç türetilmesinin donanımsal reddi."""
        
        # Serbest değişkenler (Örn: 'Zeyd') yerine güvenlik duvarına uygun olarak
        # niceleyici (quantifier) ile bağlanmış çelişkili aksiyomlar test edilir.
        premises = [
            "Exists([x], Insan(x))",
            "Forall([x], Not(Insan(x)))"
        ]
        
        self.solver.solver.push()
        try:
            for p in premises:
                self.solver.solver.add(self.solver.builder.parse(p))
            
            result = self.solver.solver.check()
            self.assertEqual(result, z3.unsat, "[ZAFİYET] Çelişkili öncüller SAT verdi. Lüzum bağı çöktü.")
        finally:
            self.solver.solver.pop()

    def test_ast_sandbox_recursion_limit(self):
        """Faz 1.1'deki Güvenlik Duvarı: AST Parse limitinin derinlik saldırılarına (Stack Overflow) karşı testi."""
        builder = Z3ExpressionBuilder(max_depth=3)
        
        # Derinlik limitini (3) aşan 4 katmanlı rekürsif FOL payload'u
        malicious_payload = "Not(Not(Not(Not(Insan(x)))))"
        
        with self.assertRaises(RecursionError, msg="[KRİTİK ZAFİYET] AST Derinlik Limiti aşıldı. Combinatorial Explosion riski aktif."):
            builder.parse(malicious_payload)

if __name__ == '__main__':
    unittest.main()