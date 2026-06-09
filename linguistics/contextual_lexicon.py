from typing import Dict, Optional, Any, List, Tuple, Protocol
from linguistics.discourse_state import DiscourseRegister
from core.exceptions import DiachronicViolationError

class IOntoLexSemanticClient(Protocol):
    """
    [FAZ 10] Dışsal OntoLex Semantic Graph (Sense/Reference) Arayüzü.
    İhtilafsız (Base) kök kelimelerin ontolojik ID'lerini RDF üzerinden sorgular.
    """
    def get_base_concept_id(self, word: str, epoch: str) -> Optional[str]: ...


class LocalOntoLexSemanticClient:
    """
    [FAZ 10] RAM üzerinde çalışan, dışsal semantik graf simülatörü.
    Manuel register_word yükünü sıfırlayarak temel İslâm ontolojisini (Base) otonom bağlar.
    """
    def __init__(self):
        self._base_ontology_map = {
            "allah": "Wajib_al_Wujud",
            "cemad": "Cemad",
            "nam": "Nami",
            "zeyd": "Insan",
            "drb": "Bats",
            "masiy": "Masi",
            "fi": "GrammarNode_Fi",
            "bi": "GrammarNode_Bi",
            "beyt": "Cism",
            "sema": "Cism",
            "dar": "Cism",
            "haza": "GrammarNode_Haza"
        }
    
    def get_base_concept_id(self, word: str, epoch: str) -> Optional[str]:
        if epoch != "Classical":
            return None
        return self._base_ontology_map.get(word.lower())

# ==============================================================================
# LEKSİKON VE İLM-İ VAZ' (CONTEXTUAL LEXICON)
# ==============================================================================

"""
.. felsefe_notu::
    Klasik İslâm Dilbilimi'nde lafzın ma'nâya delaleti statik bir sözlük eşleşmesi değil, 
    dinamik bir ontolojik atama (Vaz') işlemidir. Bu modül, bir lafzın bağlam 
    ve usûl profiline göre kazandığı ontolojik ağırlığı (ID) deterministik olarak bulur.
"""

class ContextualLexicon:
    """
    N-boyutlu Leksikon Tensörü: (word -> epoch -> namespace -> proposition_type -> {default, context_triggers})
    'İlm-i Vaz adaptasyonunu destekler.
    [FAZ 1 ENTEGRASYONU]: Diachronic (Tarihsel-Dönemsel) yalıtım eklendi. Yalnızca 'Classical' 
    (Klasik Arapça) zaman damgasına sahip ontolojik düğümlerin Z3 matrisine girmesine izin verilir.
    Faz 6 - Adım 1: Siyak-Sibak (Bağlam Avcısı) AST Sentaks (İzafet) Genişletmesi.
    [FAZ 2 ENTEGRASYONU]: İlm-i Ma'ânî Kasr (Hasr) Operatör Çözümleyicisi Eklendi.
    [FAZ 10 ENTEGRASYONU]: OntoLex Fallback (Geri Dönüş) mekanizması ile otonom RDF sorgulaması entegre edildi.
    
    [FAZ 8 LITERATE PROGRAMMING]: Bilişsel Yükü (Cognitive Load) 4 birimin altında tutmak
    için monolitik parse algoritması hiyerarşik private fonksiyonlara (Chunking) ayrılmıştır.
    Orijinal motorun tarihsel 'Faz' kayıtları, değişkenleri ve akışları %100 korunmuştur.
    """
    def __init__(self, semantic_client: Optional[IOntoLexSemanticClient] = None):
        # 4 Boyutlu Tensör Hiyerarşisi: Word -> Epoch -> Namespace -> PropositionType
        self._tensor: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, Any]]]]] = {}
        # İlm-i Ma'ânî Kasr (Hasr) Operatörleri
        self.kasr_operators = {"innema": "Kasr_Innema", "illa": "Kasr_Illa"}
        # Faz 10 Bağımlılık Enjeksiyonu
        self.semantic_client = semantic_client or LocalOntoLexSemanticClient()

    def register_word(self, word: str, namespace: str, ontologic_id: str, proposition_type: str = "Kadiyye-i_Hamliyye", sibak_trigger: str = None, epoch: str = "Classical") -> None:
        """
        .. pedagojik_anlati::
            Sisteme modern bir kelime veya İngilizce bir terim girmeye çalışılırsa, 
            sistem bunu Diachronic (Tarihsel) bir ihlal kabul eder. Sadece 'Classical'
            kökler Z3 evrenine mühürlenir.
        """
        if epoch != "Classical":
            raise DiachronicViolationError(f"[ONTOLOJİK SIZINTI] '{word}' kelimesi '{epoch}' dönemine ait. Yalnızca 'Classical' (Klasik Arapça) kökleri sisteme kaydedilebilir.")

        word_lower = word.lower()
        self._initialize_tensor_dimensions(word_lower, epoch, namespace, proposition_type)
        
        if sibak_trigger:
            self._tensor[word_lower][epoch][namespace][proposition_type]["context_triggers"][sibak_trigger.lower()] = ontologic_id
        else:
            self._tensor[word_lower][epoch][namespace][proposition_type]["default"] = ontologic_id

    def _initialize_tensor_dimensions(self, word_lower: str, epoch: str, namespace: str, proposition_type: str) -> None:
        """Tensör boyutlarını güvenli (memory-safe) şekilde inşa eder."""
        if word_lower not in self._tensor:
            self._tensor[word_lower] = {}
        if epoch not in self._tensor[word_lower]:
            self._tensor[word_lower][epoch] = {}
        if namespace not in self._tensor[word_lower][epoch]:
            self._tensor[word_lower][epoch][namespace] = {}
        if proposition_type not in self._tensor[word_lower][epoch][namespace]:
            self._tensor[word_lower][epoch][namespace][proposition_type] = {"default": None, "context_triggers": {}}

    def _scan_ast_for_sibak(self, target_word: str, triggers: Dict[str, str], dependencies: List[Tuple[str, str, str, str]] = None) -> Optional[str]:
        """
        İbn Teymiyye'nin Hakikat felsefesine uygun olarak (Faz 6), 
        kelimenin hedef uzaya (Bila_Kayf) taşınabilmesi için rastgele bir 
        aynı-cümle (token) beraberliği değil, kesin bir İzafet (Mudaf) 
        veya Yüklem (Haber) AST bağıntısı aranır.
        """
        if not dependencies or not triggers:
            return None
            
        target_lower = target_word.lower()
        
        for amil, mamul, rel_type, irab in dependencies:
            amil_lower = amil.lower()
            mamul_lower = mamul.lower()
            
            for trigger, ont_id in triggers.items():
                valid_relations = ["Mudaf_MudafIlayh", "Mubteda_Haber", "Fail", "Meful", "Sifat_Mevsuf", "Rel_Ihtisas"]
                
                if rel_type in valid_relations:
                    if (target_lower in amil_lower and trigger in mamul_lower) or \
                       (target_lower in mamul_lower and trigger in amil_lower):
                        return ont_id
                        
        return None

    def _get_from_namespace(self, namespace_map: Dict, ns: str, proposition_type: str, word: str, dependencies: List[Tuple[str, str, str, str]]) -> Optional[str]:
        """İlgili usûl evreninden (Namespace) kelimenin ontolojik kimliğini süzer (Kadiyye türüne göre daraltma)."""
        if ns not in namespace_map:
            return None
            
        prop_map = namespace_map[ns]
        target_map = None
        if proposition_type in prop_map:
            target_map = prop_map[proposition_type]
        elif "Kadiyye-i_Hamliyye" in prop_map:
            target_map = prop_map["Kadiyye-i_Hamliyye"]
        
        if target_map:
            context_id = self._scan_ast_for_sibak(word, target_map.get("context_triggers", {}), dependencies)
            if context_id:
                return context_id
            
            return target_map.get("default")
        return None

    def resolve_id(self, word: str, active_namespace: str, proposition_type: str = "Kadiyye-i_Hamliyye", discourse: DiscourseRegister = None, dependencies: List[Tuple[str, str, str, str]] = None, epoch: str = "Classical") -> str:
        word_lower = word.lower()

        # [FAZ 2 ENTEGRASYONU] Kasr Operatörleri Doğrudan Çözümlenir
        if word_lower in self.kasr_operators:
            return f"Harf_{self.kasr_operators[word_lower]}"

        # Leksikon Tensör Taraması (Theological/Contextual Overrides)
        if word_lower in self._tensor:
            if epoch not in self._tensor[word_lower]:
                raise DiachronicViolationError(f"[ONTOLOJİK SIZINTI] '{word}' kelimesi için '{epoch}' zaman damgasına sahip bir karşılık bulunamadı. Seküler/MSA sızıntısı reddedildi.")

            namespace_map = self._tensor[word_lower][epoch]

            resolved = self._get_from_namespace(namespace_map, active_namespace, proposition_type, word, dependencies)
            if resolved: return resolved
            
            resolved_base = self._get_from_namespace(namespace_map, "Base", proposition_type, word, dependencies)
            if resolved_base: return resolved_base

        # [FAZ 10] OntoLex Semantik Graf (Fallback) Taraması
        fallback_id = self.semantic_client.get_base_concept_id(word_lower, epoch)
        if fallback_id:
            return fallback_id

        if word_lower not in self._tensor:
            raise ValueError(f"[UNKNOWN_VARIABLE] Leksikon Hatası: '{word}' ne yerel tensörde ne de dışsal OntoLex semantik grafında kayıtlı değil.")
            
        raise ValueError(f"LOGIC_FAILURE_PROBABILITY: HIGH - '{word}' kelimesi '{active_namespace}' alanında (Epoch: {epoch}) çözümlenemedi.")
        
    def dump_tensor(self) -> Dict[str, Any]:
        return self._tensor