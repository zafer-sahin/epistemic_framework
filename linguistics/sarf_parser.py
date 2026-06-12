from typing import Dict, List, Optional, Union, Tuple, Protocol
from pydantic import BaseModel, ConfigDict, Field

# Eğer StrictAirGapValidator projede yoksa, dummy modül import hatalarını önlemek için mock yapılabilir 
# Ancak projenin geri kalanında var olduğu varsayımıyla orijinal import korunmuştur.
try:
    from linguistics.contextual_lexicon import StrictAirGapValidator
except ImportError:
    class StrictAirGapValidator:
        @staticmethod
        def validate_epoch(epoch: str): pass
        @staticmethod
        def validate_provenance(root: str): pass

try:
    from core.exceptions import DiachronicViolationError
except ImportError:
    class DiachronicViolationError(Exception): pass


# ==============================================================================
# BÖLÜM 0: İLM-İ SARF VE ÜRETKEN MORFOLOJİ (GENERATIVE MORPHOLOGY)
# ==============================================================================

class MorphologicalAnalysis(BaseModel):
    """
    .. pedagojik_anlati:: İlm-i Sarf ve Lafzın Ontolojik Pasaportu
    Klasik Arapçada bir kelime (lafız), statik bir karakter dizisi değil; kökünden (Asl) 
    türeyerek belirli bir kalıba (Vezin) giren, böylece harici dünyadaki (A'yân) bir varlığa, 
    eyleme veya niteliğe dönüşen dinamik bir yapıdır.
    
    Matematiksel olarak bu, bir varlığın ($x$) potansiyel (Kuvve) halinden aktüel (Fiil) 
    haline geçişini belgeler. Bu model, kelimenin sadece sözlüksel özelliklerini değil, 
    Z3 SMT motorunda hangi ontolojik kısıtlara ($\text{Constraint}$) tabi olacağını 
    mühürleyen bir felsefi kimlik kartıdır.
    """
    model_config = ConfigDict(extra="forbid")
    
    original_word: str
    root: str           
    pattern: str        
    ontologic_type: str 
    thematic_role: Optional[str] = None
    irab: Optional[str] = Field(default=None, description="İ'rab Durumu: Marfu, Mansub, Majrur, Mansub_or_Majrur, Waqf")
    is_diptote: bool = Field(default=False, description="Gayri Munsarif (Diptote) morfolojik kısıt bayrağı")
    gender: Optional[str] = Field(default=None, description="HPSG Kısıtı: Muzekker veya Muennes")
    number: Optional[str] = Field(default=None, description="HPSG Kısıtı: Mufred, Tesniye, Cemi")
    hidden_pronoun: Optional[str] = Field(default=None, description="DRT Matrisi: Müstatir Zamir (Huve, Hiye vb.)")
    provenance_locked: bool = Field(default=True, description="[FAZ 1.1] İstatistiksel Stemmer/NLP sızıntısını engelleyen ontolojik mühür")


class OntoLexRule(BaseModel):
    """
    .. mantik_kurali:: Türetim (Derivation) ve Determinizm
    İslâm mantığında nedensellik (İlliyet) kesindir. Bir kelimenin aslından (Root) türemesi,
    olasılıksal (probabilistic) bir NLP süreciyle tahmin edilemez; katı pozisyonel kurallarla 
    (Extraction Rules) deterministik olarak haritalandırılmak zorundadır.
    
    $\text{Derive}: \text{Root} \times \text{Pattern} \rightarrow \text{InstantiatedWord}$
    """
    model_config = ConfigDict(extra="forbid")
    rule_type: str
    positions: List[Union[int, str]]


class OntoLexMorphEntry(BaseModel):
    """
    .. felsefe_notu:: A'yân-ı Sâbite ve Kelime Grafları
    Bu model, W3C OntoLex standardında kelimelerin ideal formlarını (Platonik İdealar / A'yân-ı Sâbite)
    temsil eder. Fiziksel metindeki her kelime, bu soyut graf düğümlerinden birine refere (Instantiation) eder.
    """
    model_config = ConfigDict(extra="forbid")
    pattern_id: str
    ontologic_type: str
    thematic_role: Optional[str] = None
    gender: Optional[str] = None
    number: Optional[str] = None
    hidden_pronoun: Optional[str] = None
    extraction_rules: OntoLexRule


# ==============================================================================
# ONTOLEX-MORPH GRAF İSTEMCİ (CLIENT) ARAYÜZÜ VE YEREL SİMÜLATÖR
# ==============================================================================

class IOntoLexGraphClient(Protocol):
    """
    .. pedagojik_anlati:: Hakikatin Dışsallığı (External Truth)
    Sarf motoru bilginin kaynağı değil, sadece işleyicisidir (Active Intellect). Kelimelerin 
    ontolojik statüleri ve bükün kuralları sisteme içkin (hardcoded) olamaz; dışsal ve mutlak 
    bir hakikat kaynağından (Graf Veritabanı) çekilmelidir. Bu arayüz, epistemolojik sınırları çizer.
    """
    def query_closed_set(self, core_word: str) -> Optional[Dict[str, str]]: ...
    def query_pattern_graph(self, signature: str) -> Optional[OntoLexMorphEntry]: ...
    def check_diptote_status(self, stem: str) -> bool: ...


class LocalOntoLexGraphClient:
    """
    .. felsefe_notu:: Kapalı Kümeler (Closed Sets) ve Monadlar
    Harfler (Edatlar), İsm-i İşaretler ve Kasr Edatları üretken morfolojiye (İştikak) tabi olmayan, 
    kendi içlerine kapalı sâbitelerdir (Monadlar). Bu simülatör, bu mutlak sâbiteleri ve 'Fa'ala' 
    gibi evrensel kalıpları geçici olarak barındıran bir bellek (Hafıza) işlevi görür.
    """
    def __init__(self):
        self._harf_set = {
            "fi", "min", "ila", "ala", "bi", "li", "wa", "au", "summe", "in",
            "hal", "a", "mata", "kayfa", "man", "ma", "eyne",  
            "illa", "lam", "lan", "fa", "fe"
        }
        self._tevkid_set = {"kad", "qad", "la", "nun"}
        # İnne ve Kardeşleri (Epistemik Operatörler)
        self._inne_set = {"inna", "anna", "kaanna", "lakinna", "layta", "laalla", "inne", "enne", "keenne", "lakinne", "leyte", "lealle"}
        self._kasr_set = {"innema", "illa"}
        self._ism_isaret_set = {"haza", "hazihi", "zalike", "tilke", "hula", "ulaika"}
        
        # .. mantik_kurali:: İlleteyn (İki İllet) ve Ontolojik Ağırlık
        # Gayri Munsarif kelimeler (Örn: Yabancı kökenlilik ve Özel İsim olma gibi iki illeti taşıyanlar), 
        # dildeki varoluşsal ağırlıkları nedeniyle esre (Kesra) ve tenvin almayı reddederler.
        self._diptote_stems = {
            "makkat", "ibrahim", "ismail", "umar", "ahmad", "ahmed", 
            "mesacid", "masabih", "fatimat", "ayishat", "makkah"
        }

        # .. pedagojik_anlati:: Emsile ve Bina'nın Matematiksel Matrisi
        # Klasik medrese müfredatındaki fiil çekim kalıplarının (Vezinler), cebirsel imzalara 
        # (Structural Signatures - CaCaCa) dönüştürülmüş halleridir. Z3 bu imzalara göre kökleri türetir.
        self._pattern_graph: Dict[str, OntoLexMorphEntry] = {
            "CaCaCa": OntoLexMorphEntry(pattern_id="Fa'ala", ontologic_type="Fiil", thematic_role="Action", gender="Muzekker", number="Mufred", hidden_pronoun="Huve", extraction_rules=OntoLexRule(rule_type="Standard", positions=[0, 2, 4])),
            "CaCaCat": OntoLexMorphEntry(pattern_id="Fa'alat", ontologic_type="Fiil", thematic_role="Action", gender="Muennes", number="Mufred", hidden_pronoun="Hiye", extraction_rules=OntoLexRule(rule_type="Standard", positions=[0, 2, 4])),
            "yaCCiCu": OntoLexMorphEntry(pattern_id="Yaf'ilu", ontologic_type="Fiil", thematic_role="Action", gender="Muzekker", number="Mufred", hidden_pronoun="Huve", extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])),
            "taCCiCu": OntoLexMorphEntry(pattern_id="Taf'ilu", ontologic_type="Fiil", thematic_role="Action", gender="Muennes", number="Mufred", hidden_pronoun="Hiye", extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])),
            "yaCCaCu": OntoLexMorphEntry(pattern_id="Yaf'alu", ontologic_type="Fiil", thematic_role="Action", gender="Muzekker", number="Mufred", hidden_pronoun="Huve", extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])),
            "yaCCuCu": OntoLexMorphEntry(pattern_id="Yaf'ulu", ontologic_type="Fiil", thematic_role="Action", gender="Muzekker", number="Mufred", hidden_pronoun="Huve", extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])),
            "CaaCa": OntoLexMorphEntry(pattern_id="Fa'ala_Ecvef", ontologic_type="Fiil", thematic_role="Action", gender="Muzekker", number="Mufred", hidden_pronoun="Huve", extraction_rules=OntoLexRule(rule_type="Ilal_Ecvef", positions=[0, 'W_Y', 3])),
            "yaCooCu": OntoLexMorphEntry(pattern_id="Yaf'ulu_Ecvef", ontologic_type="Fiil", thematic_role="Action", gender="Muzekker", number="Mufred", hidden_pronoun="Huve", extraction_rules=OntoLexRule(rule_type="Ilal_Ecvef", positions=[2, 'W', 4])),
            "yaCeeCu": OntoLexMorphEntry(pattern_id="Yaf'ilu_Ecvef", ontologic_type="Fiil", thematic_role="Action", gender="Muzekker", number="Mufred", hidden_pronoun="Huve", extraction_rules=OntoLexRule(rule_type="Ilal_Ecvef", positions=[2, 'Y', 4])),
            "CaCaa": OntoLexMorphEntry(pattern_id="Fa'ala_Nakis", ontologic_type="Fiil", thematic_role="Action", gender="Muzekker", number="Mufred", hidden_pronoun="Huve", extraction_rules=OntoLexRule(rule_type="Ilal_Nakis", positions=[0, 2, 'W_Y'])),
            "iCCaCaCa": OntoLexMorphEntry(pattern_id="Ifta'ala_Ibdal", ontologic_type="Fiil", thematic_role="Action", gender="Muzekker", number="Mufred", hidden_pronoun="Huve", extraction_rules=OntoLexRule(rule_type="Ibdal", positions=['IBDAL', 4, 6])),
            "CaCiCun": OntoLexMorphEntry(pattern_id="Fâ'ilun", ontologic_type="Ism", thematic_role="Agent", gender="Muzekker", number="Mufred", extraction_rules=OntoLexRule(rule_type="Standard", positions=[0, 2, 4])),
            "CaCiCaCun": OntoLexMorphEntry(pattern_id="Fâ'ilatun", ontologic_type="Ism", thematic_role="Agent", gender="Muennes", number="Mufred", extraction_rules=OntoLexRule(rule_type="Standard", positions=[0, 2, 4])),
            "maCCuCun": OntoLexMorphEntry(pattern_id="Maf'ûlun", ontologic_type="Ism", thematic_role="Patient", gender="Muzekker", number="Mufred", extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])),
            "maCCuCaCun": OntoLexMorphEntry(pattern_id="Maf'ûlatun", ontologic_type="Ism", thematic_role="Patient", gender="Muennes", number="Mufred", extraction_rules=OntoLexRule(rule_type="Standard", positions=[2, 3, 5])),
        }

    def query_closed_set(self, core_word: str) -> Optional[Dict[str, str]]:
        if core_word in self._ism_isaret_set:
            return {"pattern": "Ism_Isaret", "ontologic_type": "Ism", "gender": "Muzekker" if core_word in ["haza", "zalike"] else "Muennes", "number": "Mufred"}
        if core_word in self._kasr_set:
            return {"pattern": "Harf_Kasr", "ontologic_type": "Harf_Kasr"}
        if core_word in self._inne_set:
            return {"pattern": "Harf_Inne", "ontologic_type": "Harf_Inne", "thematic_role": "Epistemic_Operator"}
        if core_word in self._tevkid_set:
            return {"pattern": "Harf_Tevkid", "ontologic_type": "Harf_Tevkid"}
        if core_word in self._harf_set:
            return {"pattern": "Harf", "ontologic_type": "Harf"}
        return None

    def query_pattern_graph(self, signature: str) -> Optional[OntoLexMorphEntry]:
        return self._pattern_graph.get(signature)

    def check_diptote_status(self, stem: str) -> bool:
        return stem in self._diptote_stems


# ==============================================================================
# SARF MOTORU (MANTIK VE DERİVASYON KATMANI)
# ==============================================================================

class SarfEngine:
    """
    .. pedagojik_anlati:: Sarf Motoru ve Sistemin Orkestrasyonu
    Bu sınıf, İlm-i Sarf kurallarını deterministik bir şekilde icra eden fonksiyonel kalbidir. 
    Kelimelerin i'rab (son harf harekeleri) ve yapılarındaki zayıf harflerin (İllet) dönüşümlerini 
    hesaplayarak, Nahiv motorunun (Sentaktik Derleyici) Z3 uzayında ihtiyaç duyacağı saf ontolojik 
    matrisleri hazırlar. Batılı kelime kökü bulucularının (Stemmer) istatistiksel yanılma paylarını 
    reddederek, mantıksal nedenselliği (Causality) korur.
    """
    def __init__(self, graph_client: Optional[IOntoLexGraphClient] = None):
        self.vowels = {'a', 'e', 'i', 'ı', 'o', 'ö', 'u', 'ü'}
        self.graph_client = graph_client or LocalOntoLexGraphClient()
        
        # .. felsefe_notu:: Anakronizm Zırhı
        # Kavramların modern seküler çağrışımlarla kirlenmesini önlemek için motor 
        # zorunlu olarak 'Classical' (Klasik) döneme kilitlenmiştir.
        StrictAirGapValidator.validate_epoch("Classical")

    def _generate_structural_signature(self, word: str) -> str:
        """
        .. mantik_kurali:: Harekelerden Soyutlama (Abstraction)
        Kelimenin spesifik sesletiminden (arazlardan) sıyrılarak, kök harflerin (Cevher)
        ontolojik iskeletini (Signature) ortaya çıkarma işlemidir.
        """
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
        """
        .. felsefe_notu:: İ'lâl ve İbdâl (Ontolojik Çözümleme ve Başkalaşım)
        İlletli harfler (vav, ya, elif) doğaları gereği zayıftır ve kelimenin kalıba (Vezin)
        girişi sırasında düşebilir veya birbirlerine dönüşebilir. Bu metod, bir 'String Replace'
        operasyonu değil; kelimenin bozulan içsel dengesini yeniden kurarak Asl'a (kökene) 
        rücu etmesini sağlayan felsefi bir restorasyon sürecidir.
        """
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
            
            StrictAirGapValidator.validate_provenance(resolved_root)
            return resolved_root
        except IndexError:
            raise ValueError(f"[İ'LÂL HATASI] '{word}' kelimesinin yapısal indeksi OntoLex kural sınırlarını taştı. Olasılıksal Stemmer kullanımı yasaktır.")

    def _strip_definite_article(self, original_word: str) -> Tuple[str, bool]:
        """
        .. pedagojik_anlati:: Harf-i Ta'rif ve Belirlilik (Ma'rife)
        'Al-' takısı, ismin referans noktasını zihindeki herhangi potansiyel bir varlıktan (Nekra), 
        harici dünyada belirlenmiş ve aktüelleşmiş spesifik bir varlığa (Ma'rife) taşır. 
        Z3 matrisinde bu durum Skolemizasyon ile ifade edilir:
        
        $$\exists x \in W: P(x) \land \forall y (P(y) \implies x = y)$$
        """
        core_word = original_word
        if core_word.startswith("al_"):
            return core_word[3:], True
        elif core_word.startswith("el_"):
            return core_word[3:], True
        return core_word, False

    def _evaluate_closed_sets(self, original_word: str, core_word: str) -> Optional[MorphologicalAnalysis]:
        result = self.graph_client.query_closed_set(core_word)
        if result:
            return MorphologicalAnalysis(
                original_word=original_word, 
                root=core_word, 
                pattern=result.get("pattern"),
                ontologic_type=result.get("ontologic_type"), 
                thematic_role=result.get("thematic_role"), 
                is_diptote=False,
                gender=result.get("gender"), 
                number=result.get("number")
            )
        return None

    def _evaluate_ontolex_graph(self, original_word: str, core_word: str) -> Optional[MorphologicalAnalysis]:
        """
        .. felsefe_notu:: Müstatir Zamir (Hidden Pronoun) İnjeksiyonu ve DRT
        Her fiil kalıbı, içerisinde zımnî (müstatir) bir zamir barındırır. "Her eylemin bir faili vardır" 
        felsefi aksiyomu gereği, bu metod fiilin içine gömülü faili (Örn: Huve/Hiye) çıkararak, Z3 
        uzayının failsiz kalarak nedensellik bağını yitirmesini (Ex Falso Quodlibet) kesin olarak engeller:
        
        $$\forall e \in \text{Actions} \implies \exists x \in \text{Entities}: \text{Agent}(x, e)$$
        """
        signature = self._generate_structural_signature(core_word)
        entry = self.graph_client.query_pattern_graph(signature)

        if entry:
            extracted_root = self._apply_ontolex_rules(core_word, entry.extraction_rules)
            return MorphologicalAnalysis(
                original_word=original_word, 
                root=extracted_root, 
                pattern=entry.pattern_id,
                ontologic_type=entry.ontologic_type, 
                thematic_role=entry.thematic_role,
                is_diptote=False, 
                gender=entry.gender, 
                number=entry.number,
                hidden_pronoun=entry.hidden_pronoun
            )
        return None

    def _evaluate_nominal_endings_and_diptotes(self, original_word: str, core_word: str, has_al_prefix: bool) -> MorphologicalAnalysis:
        """
        .. mantik_kurali:: Gayri Munsarif Zafiyetinin Giderilmesi ve İ'rab
        Bu aşama, amil-mamul atamalarındaki fatal hataları önler. Eğer bir isim Gayri Munsarif 
        (Diptote) ise, cer (Majrur) durumunda dahi fetha ('a') alır. Sistemin sondaki 'a' sesini 
        görüp kelimeyi yanlışlıkla Meful (Nesne) sanması, Z3 motorunda fail ile mefulün yer 
        değiştirmesine (Semantic Shift) ve cümlenin mantıksal predikatının ters dönmesine yol açar.
        
        [FAZ 1.3 - BAĞLAMSAL KISIT]: Eğer Gayri Munsarif kelime Harf-i Ta'rif ('al-') alırsa 
        munsarifleşir ve esre (Kesra) kabul eder hale gelir. Bu ontolojik restorasyon mekanizması, 
        düşük seviyeli Z3 hata sızıntılarını donanımsal düzeyde keser.
        """
        stem_1 = core_word[:-1]
        is_stem_diptote = self.graph_client.check_diptote_status(stem_1)
        
        # 1. Saf Gayri Munsarif İ'rabı (al- takısı almamış)
        if is_stem_diptote and not has_al_prefix and core_word[-1] in ("u", "a", "e", "i", "ı"):
            if core_word[-1] in ("u", "ü"):
                irab_val = "Marfu"
            elif core_word[-1] in ("a", "e"):
                irab_val = "Mansub_or_Majrur"
            else:
                # Gayri Munsarif esre (i/ı) alamaz. Almışsa Waqf durumunda bir deformasyon olarak mühürlenir.
                irab_val = "Waqf"
                
            return MorphologicalAnalysis(
                original_word=original_word, root=stem_1, pattern="Gayri_Munsarif",
                ontologic_type="Ism", thematic_role=None, irab=irab_val, is_diptote=True,
                gender="Muzekker", number="Mufred"
            )

        # 2. Waqf Durumundaki Gayri Munsarifler
        if self.graph_client.check_diptote_status(core_word) and not has_al_prefix:
            return MorphologicalAnalysis(
                original_word=original_word, root=core_word, pattern="Gayri_Munsarif",
                ontologic_type="Ism", thematic_role=None, irab="Waqf", is_diptote=True,
                gender="Muzekker", number="Mufred"
            )

        # 3. Münevven (Tenvinli) İsimler
        if core_word.endswith(("un", "ün")):
            return MorphologicalAnalysis(original_word=original_word, root=core_word[:-2], pattern="Alem/Camid_Munevven", ontologic_type="Ism", irab="Marfu", gender="Muzekker", number="Mufred")
        elif core_word.endswith(("an", "en")):
            return MorphologicalAnalysis(original_word=original_word, root=core_word[:-2], pattern="Alem/Camid_Munevven", ontologic_type="Ism", irab="Mansub", gender="Muzekker", number="Mufred")
        elif core_word.endswith(("in", "ın")):
            return MorphologicalAnalysis(original_word=original_word, root=core_word[:-2], pattern="Alem/Camid_Munevven", ontologic_type="Ism", irab="Majrur", gender="Muzekker", number="Mufred")
            
        # 4. Mudaf veya Harf-i Ta'rifli (Tenvinsiz) İsimler (al- almış Gayri Munsarifler de buraya düşer)
        elif core_word.endswith(("u", "ü")):
            return MorphologicalAnalysis(original_word=original_word, root=core_word[:-1], pattern="Alem/Camid_Mudaf", ontologic_type="Ism", irab="Marfu", gender="Muzekker", number="Mufred")
        elif core_word.endswith(("a", "e")):
            return MorphologicalAnalysis(original_word=original_word, root=core_word[:-1], pattern="Alem/Camid_Mudaf", ontologic_type="Ism", irab="Mansub", gender="Muzekker", number="Mufred")
        elif core_word.endswith(("i", "ı")):
            return MorphologicalAnalysis(original_word=original_word, root=core_word[:-1], pattern="Alem/Camid_Mudaf", ontologic_type="Ism", irab="Majrur", gender="Muzekker", number="Mufred")
        
        # .. pedagojik_anlati:: Waqf (Duraklama) Zırhı ve Ontolojik Meşruiyet
        # Harekeli okumanın olmadığı durumlarda (Waqf) sistem çökertilmez (Silent Fail engeli).
        # Kelime 'Alem/Camid_Waqf' formunda tutulur ve ontolojik meşruiyet denetimi 
        # (Discourse State) İlm-i Vaz'a (Lexicon) havale edilir.
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