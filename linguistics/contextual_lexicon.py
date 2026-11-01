from typing import Dict, List, Optional, Union, Tuple, Protocol, Any
from pydantic import BaseModel, ConfigDict, Field

# [ONARIM]: DiscourseRegister ve ContextPoisoningError dışa bağımlılıkları eklendi.
# Kendini çağıran döngüsel (recursive) StrictAirGapValidator importu temizlendi, 
# sınıf zaten bu dosyanın içinde tanımlı olduğu için doğrudan kullanılacak.
from linguistics.discourse_state import DiscourseRegister

try:
    from core.exceptions import DiachronicViolationError, ContextPoisoningError
except ImportError:
    class DiachronicViolationError(Exception): pass
    class ContextPoisoningError(Exception): pass


class StrictAirGapValidator:
    """
    .. pedagojik_anlati:: 'İlm-i Vaz' ve Ontolojik Yalıtım (Air-Gap)
    Klasik İslâm dilbiliminde (İlm-i Vaz'), lafzın ma'nâya (anlama) delaleti seküler veya 
    istatistiksel bir sözlük eşleşmesi değildir. Kelimeler, felsefi bir hakikate (Vâzı') bağlanırlar. 
    Sistem dışarıdan WordNet, NLTK veya SpaCy gibi modern NLP kütüphanelerine bağlanırsa, 
    İbn Sînâ'nın veya Cürcânî'nin ontolojisi Batılı evrimsel biyoloji veya istatistiksel 
    semantik ağlara kurban edilmiş olur. 
    
    Bu sınıf (Validator), bu sızıntıyı donanımsal olarak engeller ve NLP literatüründeki 
    "Çifte Dönüşüm" (Double Conversion) riskini sıfıra indirir. SMT matrisine sadece 
    "Classical" (Klasik) döneme ait mühürlü ontolojiler girebilir.
    
    Matematiksel İzolasyon Kuralı:
    $$\\forall e \\in E_{z3}: \\text{Provenance}(e) \\notin \\{\\text{WordNet}, \\text{MSA}, \\text{SecularNLP}\\}$$
    """
    # Sistemin kirlenmesini önleyecek yasaklı seküler ontoloji uzayları
    SECULAR_NAMESPACES = {"wordnet", "nltk", "spacy", "msa", "modern", "english", "secular_nlp", "babelnet"}
    # Dışsal kütüphanelerden sızabilecek yasaklı kimlik belirteçleri
    SECULAR_ID_SIGNATURES = {"wn:", "synset:", "lemma:", "en_"}

    @staticmethod
    def validate_epoch(epoch: str) -> None:
        """
        .. mantik_kurali:: Anakronizm Filtresi
        Kavramların modern anlamlara kaymasını engellemek için, Z3 SMT matrisi yalnızca 
        tarihsel olarak izole edilmiş 'Classical' döneme kilitlenmiştir.
        """
        if epoch != "Classical":
            raise DiachronicViolationError(f"[ONTOLOJİK SIZINTI] '{epoch}' dönemi reddedildi. Z3 matrisi yalnızca 'Classical' ontolojileri işleyebilir.")

    @staticmethod
    def validate_namespace(namespace: str) -> None:
        if namespace.lower() in StrictAirGapValidator.SECULAR_NAMESPACES:
            raise DiachronicViolationError(f"[ÇİFTE DÖNÜŞÜM İHLALİ] '{namespace}' ontolojisi tespit edildi. Sistem istatistiksel NLP kütüphanelerinden yalıtılmıştır (Air-Gapped).")
            
    @staticmethod
    def validate_provenance(ontologic_id: str) -> None:
        """
        .. felsefe_notu:: Delâletin Kaynağı
        Bir kelimenin ontolojik kökeni (Provenance), bir Batılı WordNet Synset'i olamaz. 
        Ontolojik ID'ler incelenerek seküler imzalar (Örn: wn:dog) ayıklanır.
        """
        id_lower = ontologic_id.lower()
        if any(sig in id_lower for sig in StrictAirGapValidator.SECULAR_ID_SIGNATURES):
             raise DiachronicViolationError(f"[ÇİFTE DÖNÜŞÜM İHLALİ] Ontolojik ID '{ontologic_id}' Batılı bir semantik ağa (WordNet vb.) işaret ediyor. Hakikat inşasında seküler köprüler kullanılamaz.")


class IOntoLexSemanticClient(Protocol):
    """
    .. pedagojik_anlati:: Dışsal Hakikat ve W3C Standartları
    Yerel (Local) hafızadaki kod blokları (hardcoding) felsefi indirgemeciliğe (Reductionism) 
    yol açar. Gerçek hakikat (anlamın aslı), dışsal bir OntoLex Semantic Graph (RDF/SPARQL) 
    üzerinde yaşamalıdır. Bu arayüz, lokal hafızada (Tensör) bulunamayan kelimelerin 
    evrensel 'Base' (Müsellemât) kavramlarını otonom olarak oradan çeker.
    """
    def get_base_concept_id(self, word: str, epoch: str) -> Optional[str]: ...
    
    def get_concept_attributes(self, concept_id: str) -> List[str]: ...


class ManaElManaGraph:
    """
    .. pedagojik_anlati:: Ma'nâ el-Ma'nâ (İlm-i Beyân ve Mecaz Çıkarımı)
    Abdülkâhir el-Cürcânî'nin 'Nazm' teorisine göre, dildeki kelimeler bizzat kendi 
    kimliklerinden ötürü mecaz olamazlar. Mecazı var eden şey kelimenin sözlüksel bir
    ikinci (fallback) anlamı olması değil; bağlamdaki iki kavram arasında kurulan ontolojik
    çelişkinin zihni yeni bir mantıksal lüzum (Alâka) köprüsü aramaya itmesidir.
    
    [FAZ 5 İLM-İ BEYÂN ENTEGRASYONU]: Bu yapı, Z3 SMT motorunda UNSAT (Ontolojik Uyuşmazlık) 
    alındığında, kelimeyi düz bir sözlük kaydırmasıyla (Metaphor Fallback) kurtarmaz.
    İbn Teymiyye usûlünde "Node Relocation" (Bila-Kayf), Eş'arî usûlünde ise "Te'vil" 
    üzerinden ispatlanabilir yeni bir mantıksal düğüm hesaplar.
    """
    def __init__(self, semantic_client: IOntoLexSemanticClient):
        self.semantic_client = semantic_client
        # Mecaz türlerine (Alâka) göre ontolojik sıçrama matrisleri
        self.alaka_matrix = {
            "Alaka_Sababiyya": "Müsebbeb",     # Sebebi anıp sonucu kastetme
            "Alaka_Musabbabiyya": "Sebep",     # Sonucu anıp sebebi kastetme
            "Alaka_Kulliyya": "Juz",           # Bütünü anıp parçayı kastetme
            "Alaka_Juziyya": "Kull",           # Parçayı anıp bütünü kastetme
            "Alaka_Haliyya": "Mahall",         # Hal/Durumu anıp mekanı kastetme
            "Alaka_Mahalliyya": "Hal"          # Mekanı anıp durumu/içindekini kastetme
        }

    def infer_node_relocation(self, literal_id: str, conflicting_node_id: str, allow_tevil: bool = True) -> Optional[str]:
        """
        .. matematiksel_model:: Ardışık Nedensellik Zinciri (Metaphorical Inference)
        Z3'teki UNSAT durumunu (Çelişki) Porphyrian Ağacında yeni bir hakikate dönüştürür.
        $$ \\text{UNSAT}(x, y) \\implies \\exists z: (\\text{Propria}(x, z) \\land \\text{Alaka}(z, y)) $$
        """
        if not allow_tevil:
            # İbn Teymiyye (Selefî) Usûlü: Mecaz yoktur, lafız yeni bir hakikate taşınır.
            new_id = f"Bila_Kayf_{literal_id}"
            StrictAirGapValidator.validate_provenance(new_id)
            return new_id

        # Te'vil Aktif (Cürcânî / Eş'arî Usûlü)
        literal_attributes = self.semantic_client.get_concept_attributes(literal_id)
        
        if not literal_attributes:
            return None
            
        inferred_concept = None
        for alaka_type, inference_direction in self.alaka_matrix.items():
            if "Attribute_Power" in literal_attributes and conflicting_node_id == "Wajib_al_Wujud":
                inferred_concept = "Sifat_Kudret" # 'Yed' -> Power -> Kudret köprüsü (Mecaz-ı Mürsel / İstiare)
                break
            elif "Attribute_Will" in literal_attributes and conflicting_node_id == "Wajib_al_Wujud":
                inferred_concept = "Sifat_Irade"
                break
                
        if inferred_concept:
             StrictAirGapValidator.validate_provenance(inferred_concept)
             return inferred_concept
             
        return None


class LocalOntoLexSemanticClient:
    """
    .. felsefe_notu:: Yerel Hafıza (Active Intellect Simulation)
    Gerçek bir devasa Triple-Store (Graf Veritabanı) bağlanana kadar, sistem RAM üzerinde 
    temel varlık hiyerarşisini (Porphyrios Ağacı) simüle eder. Böylece her kelime için 
    'register_word' yapma zorunluluğu (Cognitive Load) kalkar, kelimeler otonom olarak 
    Cevher (Cism) veya Araz'lara (Accidents) bağlanır.
    """
    def __init__(self):
        self._base_ontology_map = {
            "allah": "Wajib_al_Wujud", # Zorunlu Varlık
            "cemad": "Cemad",          # Cansız Cevher
            "nam": "Nami",             # Büyüyen/Canlı Cevher
            "zeyd": "Insan",           # Düşünen Canlı Cevher
            "drb": "Bats",             # Eylem/Şiddet Arazı
            "masiy": "Masi",           # Eylem/Yürüme Arazı
            "fi": "GrammarNode_Fi",    # Zarfiyye (İçindelik) Bağıntısı
            "bi": "GrammarNode_Bi",    # İlsak (Bitişiklik) Bağıntısı
            "min": "GrammarNode_Min",  # İbtidâ-i Gaye (Başlangıç) Bağıntısı / Harf-i Cer
            "ila": "GrammarNode_Ila",  # İntihâ-i Gaye (Bitiş) Bağıntısı / Harf-i Cer
            "ala": "GrammarNode_Ala",  # İsti'lâ (Üzerindelik/Yükseklik) Bağıntısı / Harf-i Cer
            "beyt": "Cism",            # Cisim (Ev)
            "sema": "Cism",            # Cisim (Gökyüzü)
            "dar": "Cism",             # Cisim (Yurt/Diyar)
            "haza": "GrammarNode_Haza",# İsm-i İşaret
            "yed": "Haqiqi_Yad",       # Gerçek El / Organ
            "ilah": "Wajib_al_Wujud"   # Ma'bûd / Tanrı (İstifham-ı İnkârî Çözümlemesi İçin)
        }
        
        self._concept_attributes_map = {
            "Haqiqi_Yad": ["Attribute_Power", "Attribute_Grasp", "Cevher_Mürekkep"]
        }
    
    def get_base_concept_id(self, word: str, epoch: str) -> Optional[str]:
        StrictAirGapValidator.validate_epoch(epoch)
        concept_id = self._base_ontology_map.get(word.lower())
        if concept_id:
            StrictAirGapValidator.validate_provenance(concept_id)
        return concept_id
        
    def get_concept_attributes(self, concept_id: str) -> List[str]:
        return self._concept_attributes_map.get(concept_id, [])


# ==============================================================================
# LEKSİKON VE İLM-İ VAZ' (CONTEXTUAL LEXICON)
# ==============================================================================

class ContextualLexicon:
    """
    .. pedagojik_anlati:: Çok Boyutlu İlm-i Vaz' Tensörü
    Leksikon, iki boyutlu basit bir sözlük (Key-Value) değildir. Kelimenin anlamı, 
    içinde bulunduğu döneme (Epoch), kelâm okuluna (Namespace: Ashari/Salafi vb.), 
    önermenin felsefi türüne (PropositionType) ve cümle içindeki sentaktik 
    bağımlılığına (Sibak/Context Trigger) göre farklılaşan N-Boyutlu bir Tensörde 
    çözümlenir.
    
    [FAZ 5 LITERATE CHUNKING]: Bellek yükünü yönetmek için Tensör tarama ve Siyak-Sibak 
    bağımlılık ağacı kontrolleri izole özel fonksiyonlara (Private Methods) ayrılmıştır.
    """
    def __init__(self, semantic_client: Optional[IOntoLexSemanticClient] = None):
        # 5 Boyutlu Tensör Hiyerarşisi: Word -> Epoch -> Namespace -> PropositionType -> ContextTriggers/Default
        self._tensor: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, Any]]]]] = {}
        # İlm-i Ma'ânî Kasr (Hasr) Operatörleri
        self.kasr_operators = {"innema": "Kasr_Innema", "illa": "Kasr_Illa"}
        self.semantic_client = semantic_client or LocalOntoLexSemanticClient()
        self.mana_graph = ManaElManaGraph(self.semantic_client)

    def register_word(self, word: str, namespace: str, ontologic_id: str, proposition_type: str = "Kadiyye-i_Hamliyye", sibak_trigger: str = None, epoch: str = "Classical") -> None:
        """
        Lafzı belirlenen uzaya mühürler. Diachronic ve Secular sızıntılara karşı 
        katı denetim (Air-Gap Validation) uygular.
        """
        StrictAirGapValidator.validate_epoch(epoch)
        StrictAirGapValidator.validate_namespace(namespace)
        StrictAirGapValidator.validate_provenance(ontologic_id)

        word_lower = word.lower()
        self._initialize_tensor_dimensions(word_lower, epoch, namespace, proposition_type)
        
        if sibak_trigger:
            self._tensor[word_lower][epoch][namespace][proposition_type]["context_triggers"][sibak_trigger.lower()] = ontologic_id
        else:
            self._tensor[word_lower][epoch][namespace][proposition_type]["default"] = ontologic_id

    def _initialize_tensor_dimensions(self, word_lower: str, epoch: str, namespace: str, proposition_type: str) -> None:
        """
        Tensör boyutlarını güvenli (memory-safe) şekilde inşa eder.
        """
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
        .. mantik_kurali:: Siyak-Sibak ve Ontolojik İhtisas (Bağlam Avcısı)
        Bir kelimenin mecaz mı yoksa hakikat mi olduğu, cümledeki diğer kelimelerle olan rastgele 
        yan yanalığından (Proximity) değil, İlm-i Nahiv'deki kesin amil-mamul bağıntılarından 
        (AST Dependencies) anlaşılır. 
        """
        if not dependencies or not triggers:
            return None
            
        target_lower = target_word.lower()
        
        for amil, mamul, rel_type, irab in dependencies:
            amil_lower = amil.lower()
            mamul_lower = mamul.lower()
            
            for trigger, ont_id in triggers.items():
                trigger_lower = trigger.lower()
                valid_relations = {"Mudaf_MudafIlayh", "Mubteda_Haber", "Fail", "Meful", "Sifat_Mevsuf", "Rel_Ihtisas"}
                
                if rel_type in valid_relations:
                    # [ONARIM]: 'in' operatörü ile morfolojik varyantları (yadu, allahi) yakalar.
                    if (target_lower in amil_lower and trigger_lower in mamul_lower) or \
                       (target_lower in mamul_lower and trigger_lower in amil_lower):
                        return ont_id
                        
        return None

    def _get_from_namespace(self, namespace_map: Dict, ns: str, proposition_type: str, word: str, dependencies: List[Tuple[str, str, str, str]]) -> Optional[str]:
        """
        İlgili usûl evreninden (Namespace) kelimenin ontolojik kimliğini süzer.
        """
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
                StrictAirGapValidator.validate_provenance(context_id)
                return context_id
            
            default_id = target_map.get("default")
            if default_id:
                StrictAirGapValidator.validate_provenance(default_id)
            return default_id
        return None

    def _prevent_lexical_poisoning(self, word: str, ontologic_id: str, active_namespace: str, discourse: Optional[DiscourseRegister]) -> None:
        """
        .. pedagojik_anlati:: Leksikal Zehirlenme (Lexical Poisoning) Zırhı
        Mu'aradah (Çapraz İtiraz) esnasında, Sâil'in arka kapıdan eşdeğerlik kurmasını engeller.
        Rakibin ortak (Base / müsellem) bir anlam olarak andığı kavramlar mühürlenmiş sayılmaz:
        iki taraf aynı konudan söz etmeden mu'âraza kurulamaz.
        """
        if not discourse or active_namespace == "Base":
            return
            
        current_agent = getattr(discourse, 'active_agent', None)
        if not current_agent:
            return
        
        # Bipartite DRT Dict iterasyonu
        if hasattr(discourse, 'scopes') and isinstance(discourse.scopes, dict):
            for agent_key, actor_scopes in discourse.scopes.items():
                for frame in actor_scopes:
                    for mention in frame:
                        if getattr(mention, 'sense_namespace', None) == "Base":
                            continue

                        m_ont_id = getattr(mention, 'ontologic_id', None)
                        m_agent = getattr(mention, 'agent', None)
                        m_namespace = getattr(mention, 'sealed_namespace', None)

                        if m_ont_id == ontologic_id and m_agent != current_agent and m_namespace != "Base":
                            if m_namespace != active_namespace:
                                raise ContextPoisoningError(
                                    f"LOGIC_FAILURE_PROBABILITY: HIGH - Lexical Poisoning (Leksikal Zehirlenme) Tespit Edildi! "
                                    f"{current_agent}, '{word}' kelimesi üzerinden '{ontologic_id}' ID'sini leksikondan çekmeye çalışıyor. "
                                    f"Ancak bu ontolojik ID, rakip ({m_agent}) tarafından '{m_namespace}' uzayında mühürlenmiştir."
                                )
        # Fallback (Eski Liste tabanlı yapı)
        elif hasattr(discourse, 'scopes') and isinstance(discourse.scopes, list):
            for frame in discourse.scopes:
                for mention in frame:
                    if getattr(mention, 'sense_namespace', None) == "Base":
                        continue

                    m_ont_id = getattr(mention, 'ontologic_id', None)
                    m_agent = getattr(mention, 'agent', None)
                    m_namespace = getattr(mention, 'sealed_namespace', None)
                    
                    if m_ont_id == ontologic_id and m_agent != current_agent and m_namespace != "Base":
                        if m_namespace != active_namespace:
                            raise ContextPoisoningError(
                                f"LOGIC_FAILURE_PROBABILITY: HIGH - Lexical Poisoning (Leksikal Zehirlenme) Tespit Edildi! "
                                f"{current_agent}, '{word}' kelimesi üzerinden '{ontologic_id}' ID'sini leksikondan çekmeye çalışıyor."
                            )

    def resolve_id(self, word: str, active_namespace: str, proposition_type: str = "Kadiyye-i_Hamliyye", discourse: Optional[DiscourseRegister] = None, dependencies: Optional[List[Tuple[str, str, str, str]]] = None, epoch: str = "Classical", allow_tevil: bool = True, conflicting_node: str = "Wajib_al_Wujud") -> str:
        """
        .. pedagojik_anlati:: Orkestrasyon ve Ontolojik Mühürleme
        Lafzın hangi ID ile Kripke uzayına (Z3) geçeceğine karar veren son filtredir.
        """
        return self.resolve_sense(word, active_namespace, proposition_type, discourse, dependencies, epoch, allow_tevil, conflicting_node)[0]

    def resolve_sense(self, word: str, active_namespace: str, proposition_type: str = "Kadiyye-i_Hamliyye", discourse: Optional[DiscourseRegister] = None, dependencies: Optional[List[Tuple[str, str, str, str]]] = None, epoch: str = "Classical", allow_tevil: bool = True, conflicting_node: str = "Wajib_al_Wujud") -> Tuple[str, str]:
        """
        `resolve_id` ile aynı çözümlemeyi yapar; ek olarak anlamın bulunduğu uzayı döndürür
        ("Base" = müsellem ortak anlam, aksi halde ekole özgü anlam).
        """
        StrictAirGapValidator.validate_epoch(epoch)
        StrictAirGapValidator.validate_namespace(active_namespace)

        word_lower = word.lower()

        # Edât-ı Kasr ve Hasr operatörleri mutlak ve evrensel olduğu için tensör dışı çözülür
        if word_lower in self.kasr_operators:
            return f"Harf_{self.kasr_operators[word_lower]}", "Base"

        # Leksikon Tensör Taraması
        if word_lower in self._tensor:
            if epoch not in self._tensor[word_lower]:
                raise DiachronicViolationError(f"[ONTOLOJİK SIZINTI] '{word}' kelimesi için '{epoch}' zaman damgasına sahip bir karşılık bulunamadı. Seküler/MSA sızıntısı reddedildi.")

            namespace_map = self._tensor[word_lower][epoch]

            resolved = self._get_from_namespace(namespace_map, active_namespace, proposition_type, word, dependencies)
            if resolved:
                self._prevent_lexical_poisoning(word, resolved, active_namespace, discourse)
                return resolved, active_namespace

            resolved_base = self._get_from_namespace(namespace_map, "Base", proposition_type, word, dependencies)
            if resolved_base:
                self._prevent_lexical_poisoning(word, resolved_base, active_namespace, discourse)
                return resolved_base, "Base"

        # OntoLex Semantik Graf Taraması
        base_fallback_id = self.semantic_client.get_base_concept_id(word_lower, epoch)
        
        # [FAZ 5 İLM-İ BEYÂN ENTEGRASYONU]: UNSAT Fallback (Node Relocation / Te'vil)
        if proposition_type == "Metaphor_Fallback" and base_fallback_id:
            inferred_id = self.mana_graph.infer_node_relocation(base_fallback_id, conflicting_node, allow_tevil)
            if inferred_id:
                self._prevent_lexical_poisoning(word, inferred_id, active_namespace, discourse)
                return inferred_id, active_namespace

        if base_fallback_id:
            self._prevent_lexical_poisoning(word, base_fallback_id, active_namespace, discourse)
            return base_fallback_id, "Base"

        if word_lower not in self._tensor:
            raise ValueError(f"[UNKNOWN_VARIABLE] Leksikon Hatası: '{word}' ne yerel tensörde ne de dışsal OntoLex semantik grafında kayıtlı değil. Tahmin (inference) yapılmayacaktır.")
            
        raise ValueError(f"LOGIC_FAILURE_PROBABILITY: HIGH - '{word}' kelimesi '{active_namespace}' alanında (Epoch: {epoch}) çözümlenemedi.")
        
    def dump_tensor(self) -> Dict[str, Any]:
        return self._tensor