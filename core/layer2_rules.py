from typing import Dict, Any, List

class Layer2RuleEngine:
    """
    DSL (Domain Specific Language) Tabanlı Deterministik Kural Motoru.
    Faz 3 - Adım 3: Te'vil döngüleri için rekürsif limitasyon entegrasyonu.
    Usûl sınıflarının belirlediği 'max_tevil_retries' limitini denetler.
    """
    def enforce_rules(self, is_metaphor_likely: bool, ruleset: Dict[str, Any], flagged_elements: List[str] = None, current_attempt: int = 0) -> Dict[str, Any]:
        if flagged_elements is None:
            flagged_elements = []

        # 1. Te'vil Rekürsiyon Limiti Kontrolü (Infinite Loop Koruması)
        max_retries = ruleset.get("max_tevil_retries", 1)
        if current_attempt > max_retries:
            return {
                "action": "BLOCK",
                "reason": f"[L2 Otorite İhlali] Te'vil deneme limiti ({max_retries}) aşıldı. Sonsuz döngü engellendi."
            }

        if not is_metaphor_likely and current_attempt == 0:
            return {
                "action": "PROCEED_LITERAL",
                "reason": "Karîne tespit edilmedi. Doğrudan Z3 Ontolojisine (Hakikat) yollanacak."
            }

        # 2. Mutlak Sıfır-Transformasyon (Zero-Transformation) Kısıtı
        if not ruleset.get("allow_tevil", False):
            return {
                "action": "BLOCK",
                "reason": f"Usûl kuralları te'vili (mecazı) mutlak reddeder. İhlal Verisi: {flagged_elements}"
            }
            
        # 3. Düğüm (Node) Bazlı Teolojik Yasaklar (DSL Otoritesi)
        blocked_nodes = ruleset.get("blocked_nodes", [])
        for element in flagged_elements:
            # [LOGIC FIX]: L1 Graph'tan gelen 'amil::mamul' formatını '_' yerine '::' ile ayırarak ontolojik kimlikleri (Örn: 'Tekvin') izole et
            nodes = element.split('::')
            for node in nodes:
                if node in blocked_nodes:
                    return {
                        "action": "BLOCK",
                        "reason": f"[L2 Otorite İhlali] '{node}' düğümü üzerinde te'vil yapılması Usûl DSL'i tarafından spesifik olarak yasaklanmıştır."
                    }

        return {
            "action": "OVERRIDE_APPROVED",
            "reason": f"Karîne-i Mânia Usûl tarafından onaylandı. (Deneme: {current_attempt}/{max_retries}). Etkilenenler: {flagged_elements}"
        }