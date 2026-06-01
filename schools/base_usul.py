from abc import ABC, abstractmethod
from typing import Dict, Any
from linguistics.ilm_wad_adapter import SemanticStatementIR

class AbstractSchoolUsul(ABC):
    @property
    @abstractmethod
    def namespace(self) -> str:
        pass

    @property
    @abstractmethod
    def dsl_ruleset(self) -> Dict[str, Any]:
        pass

    # [LOGIC FIX]: Abstract Interface'e current_attempt eklendi.
    @abstractmethod
    def execute_dag(self, ir_matrix: SemanticStatementIR, l1_engine, l2_engine, l3_engine, current_attempt: int = 0) -> Dict[str, Any]:
        pass