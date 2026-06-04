import unittest
from pathlib import Path
from core.models import OntologyLoader

class TestAirGappedOntology(unittest.TestCase):
    """
    [FAZ 1 - KÖKEN DOĞRULAMASI]
    Porphyrios Ağacına (Base Ontology) sızabilecek seküler veya modern kavramları 
    derleme anında engelleyen donanımsal mührün test süiti.
    """
    @classmethod
    def setUpClass(cls):
        loader = OntologyLoader()
        cls.ontology = loader.load(Path("data/base_ontology.json"))

    def test_provenance_and_epoch_locks(self):
        """
        Tüm Base Ontology düğümlerinin istisnasız 'Classical' zaman damgasına ve
        'provenance_locked=True' mührüne sahip olduğunu özyineli olarak doğrular.
        """
        def _scan_entity(entity):
            self.assertEqual(
                entity.origin_epoch, 
                "Classical", 
                f"[ONTOLOJİK SIZINTI İHLALİ] '{entity.ontologic_id}' düğümü seküler/modern ('{entity.origin_epoch}') mühür taşıyor."
            )
            self.assertTrue(
                entity.provenance_locked, 
                f"[KÖKEN İHLALİ] '{entity.ontologic_id}' düğümü dış müdahaleye ve LLM sızıntısına açık bırakılmış."
            )
            for child in entity.children:
                _scan_entity(child)

        base_root = self.ontology.porphyrian_tree.roots.get("Base")
        self.assertIsNotNone(base_root, "Base (Mevcud) kökü Porphyrios ağacında bulunamadı.")
        
        _scan_entity(base_root)

if __name__ == '__main__':
    unittest.main()