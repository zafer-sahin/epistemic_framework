from typing import Dict, List, Any, Optional, Union, Tuple
from pydantic import BaseModel, ConfigDict, Field

# ==============================================================================
# BÖLÜM 0: 'İLM-İ SARF VE ÜRETKEN MORFOLOJİ (GENERATIVE MORPHOLOGY)
# ==============================================================================

class MorphologicalAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    original_word: str
    root: str           
    pattern: str        
    ontologic_type: str 
    thematic_role: Optional[str] = None
    irab: Optional[str] = Field(default=None, description="İ'rab Durumu: Marfu, Mansub, Majrur, Waqf")
    is_diptote: bool = Field(default=False, description="Gayri Munsarif (Diptote) morfolojik kısıt bayrağı")
    gender: Optional[str] = Field(default=None, description="HPSG Kısıtı: Muzekker veya Muennes")
    number: Optional[str] = Field(default=None, description="HPSG Kısıtı: Mufred, Tesniye, Cemi")
    hidden_pronoun: Optional[str] = Field(default=None, description="DRT Matrisi: Müstatir Zamir (Huve, Hiye vb.)")

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
    gender: Optional[str] = None
    number: Optional[str] = None
    hidden_pronoun: Optional[str] = None
    extraction_rules: OntoLexRule

class SarfEngine:
    """
    Üretken Morfoloji Motoru ('İlm-i Sarf).
    [FAZ 1 ENTEGRASYONU]: Gayri Munsarif (Diptotes) bükün sınıfları eklendi.
    [FAZ 2 ENTEGRASYONU]: Müstatir zamirler (Hidden Pronouns), Cinsiyet (Gender) ve Sayı (Number) HPSG kısıtları OntoLex grafına işlendi.
    [FAZ 3 ENTEGRASYONU]: Huruf-u Müşebbehe bil-Fiil (İnne ve kardeşleri) izole edilerek Epistemic Operator sınıfı tanımlandı.
    [FAZ 6 ENTEGRASYONU]: İsm-i İşaretler (Demonstrative Pronouns) kapalı kümeye eklendi. Harf-i Ta'rif (al_/el_) kök soyutlaması yapıldı.
    
    [FAZ 8 BÜTÜNCÜL (HOLISTIC) GÜNCELLEME]: Bilişsel yükü parçalama (Chunking) uygulanmıştır.
    Sarf motoru, tanınmayan veya harekesiz yazılan kelimeleri (Waqf) çökerterek reddetmek yerine,
    'Alem/Camid_Waqf' formunda işaretler. Ontolojik meşruiyet denetimini İlm-i Vaz'a (Lexicon) devreder.
    """
    def __init__(self):
        self.vowels = {'a', 'e', 'i', 'ı', 'o', 'ö', 'u', 'ü'}
        
        # Kapalı Küme (Closed-Set) Edatlar (Yaygın transliterasyon varyasyonları eklendi)
        self.harf_set = {
            "fi", "min", "ila", "ala", "bi", "li", "wa", "au", "summe", "in",
            "hal", "a", "mata", "kayfa", "man", "ma", "eyne",  
            "illa", "lam", "lan", "fa", "fe"
        }
        
        # [FAZ 3 ENTEGRASYONU]: "inna" buradan çıkarılarak inne_set'e aktarıldı.
        self.tevkid_set = {"kad", "qad", "la", "nun"}
        
        # [FAZ 3 ENTEGRASYONU]: İnne ve Kardeşleri (Huruf-u Müşebbehe bil-Fiil)
        self.inne_set = {"inna", "anna", "kaanna", "lakinna", "layta", "laalla", "inne", "enne", "keenne", "lakinne", "leyte", "lealle"}
        
        self.kasr_set = {"innema", "illa"}

        # [FAZ 6 ENTEGRASYONU]: İsm-i İşaretler (Demonstrative Pronouns)
        self.ism_isaret_set = {"haza", "hazihi", "zalike", "tilke", "hula", "ulaika"}
        
        # FAZ 1: Gayri Munsarif (Diptote) Gövde/Kök Havuzu.
        self.diptote_stems = {
            "makkat", "ibrahim", "ismail", "umar", "ahmad", 
            "mesacid", "masabih", "fatimat", "ayishat", "makkah"
        }
        
        # OntoLex-Morph Kural Grafı
        self.ontolex_graph: Dict[str, OntoLexMorphEntry] = {
            "CaCaCa": OntoLexMorphEntry(
                pattern_id="Fa'ala", ontologic_type="Fiil", thematic_role="Action",
                gender="Muzekker", number="Mufred", hidden_pronoun="Huve",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[0, 2, 4])
            ),
            "CaCaCat": OntoLexMorphEntry(
                pattern_id="Fa'alat", ontologic_type="Fiil", thematic_role="Action",
                gender="Muennes", number="Mufred", hidden_pronoun="Hiye",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[0, 2, 4])
            ),
            "yaCCiCu": OntoLexMorphEntry(
                pattern_id="Yaf'ilu", ontologic_type="Fiil", thematic_role="Action",
                gender="Muzekker", number="Mufred", hidden_pronoun="Huve",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])
            ),
            "taCCiCu": OntoLexMorphEntry(
                pattern_id="Taf'ilu", ontologic_type="Fiil", thematic_role="Action",
                gender="Muennes", number="Mufred", hidden_pronoun="Hiye",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])
            ),
            "yaCCaCu": OntoLexMorphEntry(
                pattern_id="Yaf'alu", ontologic_type="Fiil", thematic_role="Action",
                gender="Muzekker", number="Mufred", hidden_pronoun="Huve",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])
            ),
            "yaCCuCu": OntoLexMorphEntry(
                pattern_id="Yaf'ulu", ontologic_type="Fiil", thematic_role="Action",
                gender="Muzekker", number="Mufred", hidden_pronoun="Huve",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])
            ),
            "CaaCa": OntoLexMorphEntry(
                pattern_id="Fa'ala_Ecvef", ontologic_type="Fiil", thematic_role="Action",
                gender="Muzekker", number="Mufred", hidden_pronoun="Huve",
                extraction_rules=OntoLexRule(rule_type="Ilal_Ecvef", positions=[0, 'W_Y', 3])
            ),
            "yaCooCu": OntoLexMorphEntry(
                pattern_id="Yaf'ulu_Ecvef", ontologic_type="Fiil", thematic_role="Action",
                gender="Muzekker", number="Mufred", hidden_pronoun="Huve",
                extraction_rules=OntoLexRule(rule_type="Ilal_Ecvef", positions=[2, 'W', 4])
            ),
            "yaCeeCu": OntoLexMorphEntry(
                pattern_id="Yaf'ilu_Ecvef", ontologic_type="Fiil", thematic_role="Action",
                gender="Muzekker", number="Mufred", hidden_pronoun="Huve",
                extraction_rules=OntoLexRule(rule_type="Ilal_Ecvef", positions=[2, 'Y', 4])
            ),
            "CaCaa": OntoLexMorphEntry(
                pattern_id="Fa'ala_Nakis", ontologic_type="Fiil", thematic_role="Action",
                gender="Muzekker", number="Mufred", hidden_pronoun="Huve",
                extraction_rules=OntoLexRule(rule_type="Ilal_Nakis", positions=[0, 2, 'W_Y'])
            ),
            "iCCaCaCa": OntoLexMorphEntry(
                pattern_id="Ifta'ala_Ibdal", ontologic_type="Fiil", thematic_role="Action",
                gender="Muzekker", number="Mufred", hidden_pronoun="Huve",
                extraction_rules=OntoLexRule(rule_type="Ibdal", positions=['IBDAL', 4, 6])
            ),
            "CaCiCun": OntoLexMorphEntry(
                pattern_id="Fâ'ilun", ontologic_type="Ism", thematic_role="Agent",
                gender="Muzekker", number="Mufred",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[0, 2, 4])
            ),
            "CaCiCaCun": OntoLexMorphEntry(
                pattern_id="Fâ'ilatun", ontologic_type="Ism", thematic_role="Agent",
                gender="Muennes", number="Mufred",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[0, 2, 4])
            ),
            "maCCuCun": OntoLexMorphEntry(
                pattern_id="Maf'ûlun", ontologic_type="Ism", thematic_role="Patient",
                gender="Muzekker", number="Mufred",
                extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])
            ),
            "maCCuCaCun": OntoLexMorphEntry(
                pattern_id="Maf'ûlatun", ontologic_type="Ism", thematic_role="Patient",
                gender="Muennes", number="Mufred",
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
            elif char == 'n' and i == length - 1 and word_lower[i-1] in ['u', 'a', 'i', 'e', 'ı', 'o', 'ö', 'ü']:
                sig += char
            elif char == 't' and i == length - 1 and word_lower[i-1] in ['a', 'e']:
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

    def _strip_definite_article(self, original_word: str) -> Tuple[str, bool]:
        core_word = original_word
        if core_word.startswith("al_"):
            return core_word[3:], True
        elif core_word.startswith("el_"):
            return core_word[3:], True
        return core_word, False

    def _evaluate_closed_sets(self, original_word: str, core_word: str) -> Optional[MorphologicalAnalysis]:
        if core_word in self.ism_isaret_set:
            return MorphologicalAnalysis(
                original_word=original_word, root=core_word, pattern="Ism_Isaret",
                ontologic_type="Ism", thematic_role=None, is_diptote=False,
                gender="Muzekker" if core_word in ["haza", "zalike"] else "Muennes",
                number="Mufred"
            )

        if core_word in self.kasr_set:
            return MorphologicalAnalysis(
                original_word=original_word, root=core_word, pattern="Harf_Kasr",
                ontologic_type="Harf_Kasr", thematic_role=None, is_diptote=False
            )

        if core_word in self.inne_set:
            return MorphologicalAnalysis(
                original_word=original_word, root=core_word, pattern="Harf_Inne",
                ontologic_type="Harf_Inne", thematic_role="Epistemic_Operator", is_diptote=False
            )

        if core_word in self.tevkid_set:
            return MorphologicalAnalysis(
                original_word=original_word, root=core_word, pattern="Harf_Tevkid",
                ontologic_type="Harf_Tevkid", thematic_role=None, is_diptote=False
            )

        if core_word in self.harf_set:
            return MorphologicalAnalysis(
                original_word=original_word, root=core_word, pattern="Harf",
                ontologic_type="Harf", thematic_role=None, is_diptote=False
            )
        return None

    def _evaluate_ontolex_graph(self, original_word: str, core_word: str) -> Optional[MorphologicalAnalysis]:
        signature = self._generate_structural_signature(core_word)

        if signature in self.ontolex_graph:
            entry = self.ontolex_graph[signature]
            extracted_root = self._apply_ontolex_rules(core_word, entry.extraction_rules)
            
            return MorphologicalAnalysis(
                original_word=original_word, root=extracted_root, pattern=entry.pattern_id,
                ontologic_type=entry.ontologic_type, thematic_role=entry.thematic_role,
                is_diptote=False, gender=entry.gender, number=entry.number,
                hidden_pronoun=entry.hidden_pronoun
            )
        return None

    def _evaluate_nominal_endings_and_diptotes(self, original_word: str, core_word: str, has_al_prefix: bool) -> MorphologicalAnalysis:
        # Gayri Munsarif Kontrolü
        stem_1 = core_word[:-1]
        if stem_1 in self.diptote_stems and core_word[-1] in ("u", "a", "e", "i", "ı"):
            irab_val = "Marfu" if core_word[-1] in ("u", "ü") else "Mansub_or_Majrur"
            return MorphologicalAnalysis(
                original_word=original_word, root=stem_1, pattern="Gayri_Munsarif",
                ontologic_type="Ism", thematic_role=None, irab=irab_val, is_diptote=True,
                gender="Muzekker", number="Mufred"
            )

        # Münevven (Tenvinli) İsimler
        if core_word.endswith(("un", "ün")):
            return MorphologicalAnalysis(original_word=original_word, root=core_word[:-2], pattern="Alem/Camid_Munevven", ontologic_type="Ism", irab="Marfu", gender="Muzekker", number="Mufred")
        elif core_word.endswith(("an", "en")):
            return MorphologicalAnalysis(original_word=original_word, root=core_word[:-2], pattern="Alem/Camid_Munevven", ontologic_type="Ism", irab="Mansub", gender="Muzekker", number="Mufred")
        elif core_word.endswith(("in", "ın")):
            return MorphologicalAnalysis(original_word=original_word, root=core_word[:-2], pattern="Alem/Camid_Munevven", ontologic_type="Ism", irab="Majrur", gender="Muzekker", number="Mufred")
            
        # Mudaf (Tenvinsiz) İsimler
        elif core_word.endswith(("u", "ü")):
            return MorphologicalAnalysis(original_word=original_word, root=core_word[:-1], pattern="Alem/Camid_Mudaf", ontologic_type="Ism", irab="Marfu", gender="Muzekker", number="Mufred")
        elif core_word.endswith(("a", "e")):
            return MorphologicalAnalysis(original_word=original_word, root=core_word[:-1], pattern="Alem/Camid_Mudaf", ontologic_type="Ism", irab="Mansub", gender="Muzekker", number="Mufred")
        elif core_word.endswith(("i", "ı")):
            return MorphologicalAnalysis(original_word=original_word, root=core_word[:-1], pattern="Alem/Camid_Mudaf", ontologic_type="Ism", irab="Majrur", gender="Muzekker", number="Mufred")
        
        # BÜTÜNCÜL ÇÖZÜM: HAREKESİZ İSİMLER (WAQF / DURAKLAMA) ZIRHI
        # Tanınmayan veya harekesiz girilen tüm kelimeler çökmek yerine sükun (Waqf) 
        # halinde bir isim olarak sisteme kabul edilir. Ontolojik denetimi Lexicon yapar.
        return MorphologicalAnalysis(
            original_word=original_word, root=core_word, pattern="Alem/Camid_Waqf",
            ontologic_type="Ism", thematic_role=None, irab="Waqf", is_diptote=False,
            gender="Muzekker", number="Mufred"
        )

    def _derive_morphology(self, word: str) -> MorphologicalAnalysis:
        original_word = word.lower()
        core_word, has_al_prefix = self._strip_definite_article(original_word)
            
        res_closed = self._evaluate_closed_sets(original_word, core_word)
        if res_closed: return res_closed

        res_ontolex = self._evaluate_ontolex_graph(original_word, core_word)
        if res_ontolex: return res_ontolex

        return self._evaluate_nominal_endings_and_diptotes(original_word, core_word, has_al_prefix)

    def derive_lexicon(self, words: List[str]) -> Dict[str, MorphologicalAnalysis]:
        derived_lexicon = {}
        for word in words:
            derived_lexicon[word] = self._derive_morphology(word)
        return derived_lexicon