from __future__ import annotations
import json
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Literal, Dict, Any

class EpistemicNamespace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    id: str  # Örn: "Base", "Maturidi", "Ashari"
    parent_namespace: Optional[str] = None  # Hiyerarşik kalıtım için

class TermModel(BaseModel):
    """
    Çifte çeviri safsatası (BRQ-01) iptal edilmiştir.
    Z3 değişkenleri sadece 'ar' (Transliterasyon) üzerinden türetilir.
    """
    model_config = ConfigDict(extra="forbid")
    ar: str  # Mutlak Ontolojik ID (Örn: Natiq, Hayvan)
    ar_script: Optional[str] = None # Arapça orijinal yazım (Görsel/Loglama için)

class RelationalConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    relation_type: str
    target_id: str  
    axiom: str

class EpistemicEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ontologic_id: str
    namespace: str = "Base" 
    terms: TermModel
    level: Optional[int] = None

    differentia_id: Optional[str] = None
    propria_ids: List[str] = Field(default_factory=list)
    accidents_ids: List[str] = Field(default_factory=list)
    
    relations: List[RelationalConstraint] = Field(default_factory=list)
    children: List['EpistemicEntity'] = Field(default_factory=list)

class LogicalTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: str
    ar: str

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
    """Monolitik ağaç yerine namespace bazlı çoklu kök yapısı (BRQ-02)."""
    model_config = ConfigDict(extra="forbid")
    namespaces: Dict[str, EpistemicNamespace] = Field(default_factory=dict)
    roots: Dict[str, EpistemicEntity] = Field(default_factory=dict)

class BaseOntology(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    logical_components: LogicalComponent = Field(alias="Logical_Components")
    porphyrian_tree: PorphyrianTree = Field(alias="Porphyrian_Tree")
    syllogism_moods: Dict[str, Dict[str, SyllogismMood]] = Field(alias="Syllogism_Moods")

class OntologyLoader:
    def __init__(self, ontology_path: Optional["str | Path"] = None) -> None:
        self.ontology_path = Path(ontology_path) if ontology_path is not None else None

    def load(self, ontology_path: Optional["str | Path"] = None) -> BaseOntology:
        path = Path(ontology_path) if ontology_path is not None else self.ontology_path
        if path is None:
            raise ValueError("[UNKNOWN_VARIABLE] ontology_path eksik.")

        raw_data = path.read_text(encoding="utf-8")
        parsed_data = json.loads(raw_data)
        return BaseOntology.model_validate(parsed_data)

EpistemicEntity.model_rebuild()