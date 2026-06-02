from typing import Dict, Optional, Any
from linguistics.discourse_state import DiscourseRegister

class ContextualLexicon:
    """
    N-boyutlu Leksikon Tensörü: (word -> namespace -> proposition_type -> {default, context_triggers})
    'İlm-i Vaz adaptasyonunu destekler.
    Faz 3 - Adım 1: Siyak-Sibak (Bağlam Avcısı) Genişletmesi.
    Kelimenin anlamı, Söylem Belleğindeki (DiscourseRegister) geçmiş kelimelere (Sibak) göre dinamik değişir.
    """
    def __init__(self):
        self._tensor: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = {}

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

    def _scan_discourse_for_sibak(self, discourse: DiscourseRegister, triggers: Dict[str, str]) -> Optional[str]:
        if not discourse or not triggers:
            return None
        
        frames = discourse.mujib_frames if discourse.active_agent == "Mujib" else discourse.sail_frames
        for frame in reversed(frames):
            for mention in reversed(frame):
                if mention.word.lower() in triggers:
                    return triggers[mention.word.lower()]
        return None

    def resolve_id(self, word: str, active_namespace: str, proposition_type: str = "Kadiyye-i_Hamliyye", discourse: DiscourseRegister = None) -> str:
        word_lower = word.lower()
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
                context_id = self._scan_discourse_for_sibak(discourse, target_map.get("context_triggers", {}))
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