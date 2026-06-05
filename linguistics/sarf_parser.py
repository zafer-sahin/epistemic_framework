from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

class MorphologicalAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    original_word: str
    root: str           
    pattern: str        
    ontologic_type: str 
    thematic_role: Optional[str] = None  

class OntoLexRule(BaseModel):
    """OntoLex-Morph standardında kelime üretim/çekim kuralları"""
    model_config = ConfigDict(extra="forbid")
    rule_type: str
    positions: List[Union[int, str]]

class OntoLexMorphEntry(BaseModel):
    """OntoLex-Morph RDF/Graf düğümü karşılığı"""
    model_config = ConfigDict(extra="forbid")
    pattern_id: str
    ontologic_type: str
    thematic_role: Optional[str] = None
    extraction_rules: OntoLexRule

class SarfEngine:
    """
    Üretken Morfoloji Motoru ('İlm-i Sarf).
    [FAZ 3 ENTEGRASYONU]: OntoLex-Morph RDF standartlarına uygun katı durum makinesi.
    Statik wazan_matrix sözlüğü, manipüle edilemez OntoLex kural grafına dönüştürülmüştür.
    """
    def __init__(self):
        self.vowels = {'a', 'e', 'i', 'ı', 'o', 'ö', 'u', 'ü'}
        
        # Kapalı Küme (Closed-Set) Edatlar
        self.harf_set = {
            "fi", "min", "ila", "ala", "bi", "li", "wa", "au", "summe", "in",
            "hal", "a", "mata", "kayfa", "man", "ma", "eyne",  
            "illa", "lam", "lan"   
        }
        
        self.tevkid_set = {"inna", "kad", "qad", "la", "nun"}
        self.kasr_set = {"innema", "illa"}
        
        # OntoLex-Morph Kural Grafı
        self.ontolex_graph: Dict[str, OntoLexMorphEntry] = {
            "CaCaCa": OntoLexMorphEntry(
                pattern_id="Fa'ala", ontologic_type="Fiil", thematic_role="Action",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[0, 2, 4])
            ),
            "yaCCiCu": OntoLexMorphEntry(
                pattern_id="Yaf'ilu", ontologic_type="Fiil", thematic_role="Action",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])
            ),
            "yaCCaCu": OntoLexMorphEntry(
                pattern_id="Yaf'alu", ontologic_type="Fiil", thematic_role="Action",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])
            ),
            "yaCCuCu": OntoLexMorphEntry(
                pattern_id="Yaf'ulu", ontologic_type="Fiil", thematic_role="Action",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])
            ),
            "CaaCa": OntoLexMorphEntry(
                pattern_id="Fa'ala_Ecvef", ontologic_type="Fiil", thematic_role="Action",
                extraction_rules=OntoLexRule(rule_type="Ilal_Ecvef", positions=[0, 'W_Y', 3])
            ),
            "yaCooCu": OntoLexMorphEntry(
                pattern_id="Yaf'ulu_Ecvef", ontologic_type="Fiil", thematic_role="Action",
                extraction_rules=OntoLexRule(rule_type="Ilal_Ecvef", positions=[2, 'W', 4])
            ),
            "yaCeeCu": OntoLexMorphEntry(
                pattern_id="Yaf'ilu_Ecvef", ontologic_type="Fiil", thematic_role="Action",
                extraction_rules=OntoLexRule(rule_type="Ilal_Ecvef", positions=[2, 'Y', 4])
            ),
            "CaCaa": OntoLexMorphEntry(
                pattern_id="Fa'ala_Nakis", ontologic_type="Fiil", thematic_role="Action",
                extraction_rules=OntoLexRule(rule_type="Ilal_Nakis", positions=[0, 2, 'W_Y'])
            ),
            "iCCaCaCa": OntoLexMorphEntry(
                pattern_id="Ifta'ala_Ibdal", ontologic_type="Fiil", thematic_role="Action",
                extraction_rules=OntoLexRule(rule_type="Ibdal", positions=['IBDAL', 4, 6])
            ),
            "CaCiCun": OntoLexMorphEntry(
                pattern_id="Fâ'ilun", ontologic_type="Ism", thematic_role="Agent",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[0, 2, 4])
            ),
            "maCCuCun": OntoLexMorphEntry(
                pattern_id="Maf'ûlun", ontologic_type="Ism", thematic_role="Patient",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])
            ),
        }

    def _generate_structural_signature(self, word: str) -> str:
        sig = ""
        word_lower = word.lower()
        length = len(word_lower)
        
        for i, char in enumerate(word_lower):
            if char in self.vowels:
                sig += char
            elif char in ['m', 'y', 'a', 't'] and i == 0:
                sig += char
            elif char == 'n' and i == length - 1 and word_lower[i-1] in ['u', 'a', 'i']:
                sig += char
            else:
                sig += 'C'
        return sig

    def _apply_ontolex_rules(self, word: str, rule: OntoLexRule) -> str:
        word_lower = word.lower()
        resolved_root = ""
        
        try:
            for pos in rule.positions:
                if isinstance(pos, int):
                    resolved_root += word_lower[pos]
                elif pos == 'W_Y':
                    resolved_root += "w" 
                elif pos == 'W':
                    resolved_root += "w"
                elif pos == 'Y':
                    resolved_root += "y"
                elif pos == 'IBDAL':
                    if word_lower[1] == 't' and word_lower[2] == 't':
                        resolved_root += "w"
                    elif word_lower[1] == 'd' and word_lower[2] == 'd':
                        resolved_root += "d"
                    else:
                        resolved_root += word_lower[1] 
                else:
                    raise ValueError(f"Geçersiz OntoLex-Morph kural parametresi: {pos}")
            return resolved_root
        except IndexError:
            raise ValueError(f"[İ'LÂL HATASI] '{word}' kelimesinin yapısal indeksi OntoLex kural sınırlarını taştı.")

    def _derive_morphology(self, word: str) -> MorphologicalAnalysis:
        word_lower = word.lower()
        
        if word_lower in self.kasr_set:
            return MorphologicalAnalysis(
                original_word=word_lower, root=word_lower, pattern="Harf_Kasr",
                ontologic_type="Harf_Kasr", thematic_role=None
            )

        if word_lower in self.tevkid_set:
            return MorphologicalAnalysis(
                original_word=word_lower, root=word_lower, pattern="Harf_Tevkid",
                ontologic_type="Harf_Tevkid", thematic_role=None
            )

        if word_lower in self.harf_set:
            return MorphologicalAnalysis(
                original_word=word_lower, root=word_lower, pattern="Harf",
                ontologic_type="Harf", thematic_role=None 
            )

        signature = self._generate_structural_signature(word_lower)
        
        if signature in self.ontolex_graph:
            entry = self.ontolex_graph[signature]
            extracted_root = self._apply_ontolex_rules(word_lower, entry.extraction_rules)
            return MorphologicalAnalysis(
                original_word=word_lower, root=extracted_root, pattern=entry.pattern_id,
                ontologic_type=entry.ontologic_type, thematic_role=entry.thematic_role
            )
            
        if word_lower.endswith(("un", "an", "in")):
            return MorphologicalAnalysis(
                original_word=word_lower, root=word_lower[:-2], pattern="Alem/Camid_Munevven",
                ontologic_type="Ism", thematic_role=None 
            )
        elif word_lower.endswith(("u", "a", "i")):
            return MorphologicalAnalysis(
                original_word=word_lower, root=word_lower[:-1], pattern="Alem/Camid_Mudaf",
                ontologic_type="Ism", thematic_role=None
            )

        raise ValueError(f"[SARF ÇÖKÜŞÜ] '{word}' (İmza: {signature}) kelimesi OntoLex-Morph grafında doğrulanamadı. MSA/Modern türetim reddedildi.")

    def derive_lexicon(self, words: List[str]) -> Dict[str, MorphologicalAnalysis]:
        derived_lexicon = {}
        for word in words:
            derived_lexicon[word] = self._derive_morphology(word)
        return derived_lexicon