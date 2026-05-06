from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Literal, Dict

class TermModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tr: Optional[str] = None
    ar: Optional[str] = None
    en: Optional[str] = None


class QuinqueVoces(str, Enum):
    Genus = "Genus"
    Species = "Species"
    Differentia = "Differentia"
    Proprium = "Proprium"
    Accident = "Accident"


class QuinqueVocesElement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: QuinqueVoces
    tr: Optional[str] = None
    ar: Optional[str] = None
    en: Optional[str] = None


class QuinqueVocesModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    elements: List[QuinqueVocesElement] = Field(default_factory=list)

class RelationalConstraint(BaseModel):
    """
    İki ontolojik varlık arasındaki n-ary (ikili) ilişkileri tanımlar.
    Örn: type="dependency", source="Fiil", target="Fail", property="Marfu"
    """
    model_config = ConfigDict(extra="forbid")
    
    relation_type: str  # İlişkinin doğası (Örn: "Amil_Mamul", "Mubteda_Haber")
    target: str         # İlişkinin yöneldiği varlık (Hedef düğüm)
    axiom: str          # Z3 içinFOL şablonu. Örn: "Forall([x, y], Implies(And(Fiil(x), Fail(y)), Rel_Amil(x, y)))"

class EpistemicEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    terms: TermModel
    level: Optional[int] = None

    differentia: Optional[TermModel] = None
    propria: List[TermModel] = Field(default_factory=list)
    accidents: List[TermModel] = Field(default_factory=list)
    
    # YENİ EKLENEN VEKTÖR: Çapraz Kesişim ve İlişkiler (Graph Edges)
    relations: List[RelationalConstraint] = Field(default_factory=list)
    
    children: List['EpistemicEntity'] = Field(default_factory=list)

class LogicalTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    tr: Optional[str] = None
    ar: Optional[str] = None
    en: Optional[str] = None


class LogicalComponent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    terms: Dict[str, LogicalTerm] = Field(alias="Terms")
    premises: Dict[str, TermModel] = Field(alias="Premises")


SyllogismPart = Literal["Major", "Minor", "Conclusion"]


class SyllogismMood(BaseModel):
    model_config = ConfigDict(extra="forbid")

    islamic_term: Optional[str] = None
    logic_structure: str
    mapping: Dict[SyllogismPart, str]
    predicates: List[str] = Field(default_factory=list)


class PorphyrianTree(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root: EpistemicEntity


class BaseOntology(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    logical_components: LogicalComponent = Field(alias="Logical_Components")
    quinque_voces: QuinqueVocesModel = Field(alias="Quinque_Voces")
    porphyrian_tree: PorphyrianTree = Field(alias="Porphyrian_Tree")
    syllogism_moods: Dict[str, Dict[str, SyllogismMood]] = Field(alias="Syllogism_Moods")


class OntologyLoader:
    def __init__(self, ontology_path: Optional["str | Path"] = None) -> None:
        self.ontology_path = Path(ontology_path) if ontology_path is not None else None

    def load(self, ontology_path: Optional["str | Path"] = None) -> BaseOntology:
        path = Path(ontology_path) if ontology_path is not None else self.ontology_path
        if path is None:
            raise ValueError("ontology_path must be provided (constructor or load())")

        # Deterministik tam okuma. Hata yutma iptal edilmiştir.
        raw_data = path.read_text(encoding="utf-8")
        
        # Eğer JSON formatında (virgül, parantez) bir hata varsa, sistem burada çökecektir (Beklenen davranış).
        parsed_data = json.loads(raw_data)
        
        # Katı Pydantic doğrulaması
        return BaseOntology.model_validate(parsed_data)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> BaseOntology:
        return BaseOntology.model_validate(data)


EpistemicEntity.model_rebuild()
