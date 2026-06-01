from typing import Dict, Optional

class ContextualLexicon:
    """
    N-boyutlu Leksikon Tensörü: (word -> namespace -> ontologic_id)
    'İlm-i Vaz adaptasyonunu destekler. Statik Sözlük yapısını imha eder.
    """
    def __init__(self):
        # Dict formatı: { "istiva": { "Base": "Istiva_Literal", "Ashari": "Istiva_Metaphor" } }
        self._tensor: Dict[str, Dict[str, str]] = {}

    def register_word(self, word: str, namespace: str, ontologic_id: str) -> None:
        """Kelimenin ontolojik izdüşümünü spesifik bir isim alanına kaydeder."""
        word_lower = word.lower()
        if word_lower not in self._tensor:
            self._tensor[word_lower] = {}
        
        # Override işlemi (Defeasibility) burada gerçekleşir
        self._tensor[word_lower][namespace] = ontologic_id

    def resolve_id(self, word: str, active_namespace: str) -> str:
        """
        Gelen kelimeyi aktif isim alanında arar. Bulamazsa 'Base' (İsağoci)
        isim alanına geri çekilir (Fallback). İkisinde de yoksa hata fırlatır.
        """
        word_lower = word.lower()
        if word_lower not in self._tensor:
            raise ValueError(f"[UNKNOWN_VARIABLE] Leksikon Hatası: '{word}' tensörde kayıtlı değil.")

        namespace_map = self._tensor[word_lower]

        # 1. Aktif mezhep/ekol bağlamında ara
        if active_namespace in namespace_map:
            return namespace_map[active_namespace]
        
        # 2. Base ontolojide ara (Kalıtım)
        if "Base" in namespace_map:
            return namespace_map["Base"]
            
        raise ValueError(f"LOGIC_FAILURE_PROBABILITY: HIGH - '{word}' kelimesi '{active_namespace}' veya 'Base' alanlarında çözümlenemedi.")
        
    def dump_tensor(self) -> Dict[str, Dict[str, str]]:
        return self._tensor