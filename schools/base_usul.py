from abc import ABC, abstractmethod
from typing import Dict, Any
from linguistics.ilm_wad_adapter import SemanticStatementIR

class AbstractSchoolUsul(ABC):
    """
    Polimorfik Ekol (Mezhep) Yürütme Usûlü Soyut Sınıfı.
    Her mezhep bu sınıftan türeyerek kendi Yönlü Asiklik Çizgesini (DAG) dayatır.
    """
    @property
    @abstractmethod
    def namespace(self) -> str:
        """Leksikon ve Ontoloji katmanındaki isim alanı (Örn: 'Salafi', 'Ashari')"""
        pass

    @abstractmethod
    def execute_dag(self, ir_matrix: SemanticStatementIR, l1_engine, l2_engine, l3_engine) -> Dict[str, Any]:
        """
        N-Katmanlı motorun hangi sırayla ve kısıtla çağrılacağını orkestre eder.
        """
        pass