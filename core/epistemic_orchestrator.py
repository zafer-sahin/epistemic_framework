from typing import Dict, Any, List, Tuple
from linguistics.ilm_wad_adapter import IlmWadAdapter
from linguistics.sarf_parser import MorphologicalAnalysis
from core.layer1_graph import Layer1HeuristicGraph
from core.layer2_rules import Layer2RuleEngine
from schools.base_usul import AbstractSchoolUsul

class EpistemicOrchestrator:
    """
    Bilişsel Çıkarım Motoru (Pipeline Manager).
    Sentaksı (AST) Semantiğe (IR), Semantiği N-Katmanlı Yürütme Çizgesine bağlar.
    """
    def __init__(self, adapter: IlmWadAdapter, l1: Layer1HeuristicGraph, l2: Layer2RuleEngine, l3_circuit_breaker):
        self.adapter = adapter
        self.l1 = l1
        self.l2 = l2
        self.l3 = l3_circuit_breaker

    def process_statement(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]], usul_profile: AbstractSchoolUsul, auto_lexicon: Dict[str, MorphologicalAnalysis] = None) -> Dict[str, Any]:
        """Uçtan uca AST derleme ve Usûl'e (Ekol) dayalı Z3 ispat döngüsü."""
        
        # Faz 9 Bağlantısı: auto_lexicon matrisi doğrudan adaptöre iletilir
        ir_matrix = self.adapter.generate_ir(tokens, dependencies, usul_profile.namespace, auto_lexicon)
        
        if not ir_matrix.is_valid_for_z3:
            return {
                "status": "PRAGMATICS_REJECT", 
                "message": "'İlm-i Ma'ânî İhlali: İnşâî form mantık motoruna giremez."
            }
        
        execution_result = usul_profile.execute_dag(ir_matrix, self.l1, self.l2, self.l3)
        return execution_result