from typing import Dict, Optional

class ContextualLexicon:
    """
    N-boyutlu Leksikon Tensörü: (word -> namespace -> proposition_type -> ontologic_id)
    'İlm-i Vaz adaptasyonunu destekler.
    Faz 3 - Adım 1: Şemsiyye Önermesel Bağlam (Propositional Context) genişletmesi.
    Kelimenin anlamı salt ekole değil, içinde bulunduğu önerme türüne (Hamliyye/Şartiyye) göre değişir.
    """
    def __init__(self):
        # 3 Boyutlu Dict formatı: 
        # { "istiva": { "Ashari": { "Kadiyye-i_Hamliyye": "Istiva_Metaphor", "Kadiyye-i_Sartiyye": "Istiva_Literal" } } }
        self._tensor: Dict[str, Dict[str, Dict[str, str]]] = {}

    def register_word(self, word: str, namespace: str, ontologic_id: str, proposition_type: str = "Kadiyye-i_Hamliyye") -> None:
        """Kelimenin ontolojik izdüşümünü spesifik bir isim alanı ve önerme türü bağlamında kaydeder."""
        word_lower = word.lower()
        if word_lower not in self._tensor:
            self._tensor[word_lower] = {}
            
        if namespace not in self._tensor[word_lower]:
            self._tensor[word_lower][namespace] = {}
        
        # Override (Defeasibility) önerme katmanında gerçekleşir
        self._tensor[word_lower][namespace][proposition_type] = ontologic_id

    def resolve_id(self, word: str, active_namespace: str, proposition_type: str = "Kadiyye-i_Hamliyye") -> str:
        """
        Gelen kelimeyi aktif isim alanında ve önerme bağlamında arar.
        Bulamazsa 'Kadiyye-i_Hamliyye' (Varsayılan Hüküm) tipine, ardından
        'Base' (İsağoci Kalıtımı) isim alanına geri çekilir (Fallback).
        """
        word_lower = word.lower()
        if word_lower not in self._tensor:
            raise ValueError(f"[UNKNOWN_VARIABLE] Leksikon Hatası: '{word}' tensörde kayıtlı değil.")

        namespace_map = self._tensor[word_lower]

        def get_from_namespace(ns: str) -> Optional[str]:
            if ns in namespace_map:
                prop_map = namespace_map[ns]
                if proposition_type in prop_map:
                    return prop_map[proposition_type]
                # İlgili önerme türü yoksa, mutlak (Hamliyye) anlama fallback yap
                elif "Kadiyye-i_Hamliyye" in prop_map:
                    return prop_map["Kadiyye-i_Hamliyye"]
            return None

        # 1. Aktif mezhep/ekol bağlamında ara
        resolved = get_from_namespace(active_namespace)
        if resolved:
            return resolved
        
        # 2. Base ontolojide ara (Kalıtım)
        resolved_base = get_from_namespace("Base")
        if resolved_base:
            return resolved_base
            
        raise ValueError(f"LOGIC_FAILURE_PROBABILITY: HIGH - '{word}' kelimesi '{active_namespace}' veya 'Base' alanlarında '{proposition_type}' bağlamında çözümlenemedi.")
        
    def dump_tensor(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        return self._tensor