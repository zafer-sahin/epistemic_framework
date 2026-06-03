from typing import Dict, Optional, Any, List, Tuple
from linguistics.discourse_state import DiscourseRegister

class ContextualLexicon:
    """
    N-boyutlu Leksikon Tensörü: (word -> namespace -> proposition_type -> {default, context_triggers})
    'İlm-i Vaz adaptasyonunu destekler.
    Faz 6 - Adım 1: Siyak-Sibak (Bağlam Avcısı) AST Sentaks (İzafet) Genişletmesi.
    Kelimelerin sadece yan yana gelmesi (lookahead) değil, doğrudan yapısal (AST) 
    olarak birbirlerine bağlanması (Mudaf_MudafIlayh vb.) denetlenir.
    [FAZ 2 ENTEGRASYONU]: İlm-i Ma'ânî Kasr (Hasr) Operatör Çözümleyicisi Eklendi.
    """
    def __init__(self):
        self._tensor: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = {}
        # İlm-i Ma'ânî Kasr (Hasr) Operatörleri
        self.kasr_operators = {"innema": "Kasr_Innema", "illa": "Kasr_Illa"}

    def register_word(self, word: str, namespace: str, ontologic_id: str, proposition_type: str = "Kadiyye-i_Hamliyye", sibak_trigger: str = None) -> None:
        word_lower = word.lower()
        if word_lower not in self._tensor:
            self._tensor[word_lower] = {}
        if namespace not in self._tensor[word_lower]:
            self._tensor[word_lower][namespace] = {}
        if proposition_type not in self._tensor[word_lower][namespace]:
            self._tensor[word_lower][namespace][proposition_type] = {"default": None, "context_triggers": {}}
        
        if sibak_trigger:
            self._tensor[word_lower][namespace][proposition_type]["context_triggers"][sibak_trigger.lower()] = ontologic_id
        else:
            self._tensor[word_lower][namespace][proposition_type]["default"] = ontologic_id

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

    def resolve_id(self, word: str, active_namespace: str, proposition_type: str = "Kadiyye-i_Hamliyye", discourse: DiscourseRegister = None, dependencies: List[Tuple[str, str, str, str]] = None) -> str:
        word_lower = word.lower()

        # [FAZ 2 ENTEGRASYONU] Kasr Operatörleri Doğrudan Çözümlenir
        if word_lower in self.kasr_operators:
            return f"Harf_{self.kasr_operators[word_lower]}"

        if word_lower not in self._tensor:
            raise ValueError(f"[UNKNOWN_VARIABLE] Leksikon Hatası: '{word}' tensörde kayıtlı değil.")

        namespace_map = self._tensor[word_lower]

        def get_from_namespace(ns: str) -> Optional[str]:
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

        resolved = get_from_namespace(active_namespace)
        if resolved: return resolved
        
        resolved_base = get_from_namespace("Base")
        if resolved_base: return resolved_base
            
        raise ValueError(f"LOGIC_FAILURE_PROBABILITY: HIGH - '{word}' kelimesi '{active_namespace}' alanında çözümlenemedi.")
        
    def dump_tensor(self) -> Dict[str, Any]:
        return self._tensor