from __future__ import annotations
import json
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Literal, Dict, Any

class EpistemicNamespace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    parent_namespace: Optional[str] = None

class TermModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ar: str
    ar_script: Optional[str] = None

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
    
    # [FAZ 4 ENTEGRASYONU]: Şemsiyye Kiplikleri (Kâtibî'nin 13 Kipliği - Zât ve Vasıf Ayrımı)
    modal_status: Literal[
        "Wajib", "Mumkin", "Mustahil", 
        "Zaruriyye_i_Mutlaka", "Daime_i_Mutlaka", "Mumkine_i_Amme",
        "Mesruta_i_Amme", "Orfiyye_i_Amme"
    ] = "Mumkin"
    
    # Meşrûta ve Örfiyye kipliklerinde, mutlak Zâtî Zaman (t_zati) yerine 
    # geçici Vasfî Zaman'ı (t_vasfi) tetikleyecek şart/nitelik ID'si.
    modal_condition_id: Optional[str] = Field(default=None, description="Şarta bağlı De dicto kiplikler için ontolojik vasıf ID'si")

    # [FAZ 2 ENTEGRASYONU]: İlm-i Beyân ve Maksad-ı Şâri' metrikleri
    husn_u_mucerred: bool = Field(default=False, description="Mutlak ontolojik mükemmellik/noksansızlık kısıtı")
    karine_derecesi: Literal[0, 1, 2, 3] = Field(default=0, description="0: Yok, 1: Mutabakat, 2: Tazammun, 3: İltizam")

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