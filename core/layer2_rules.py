from typing import Dict, Any, List

class Layer2RuleEngine:
    """
    DSL (Domain Specific Language) Tabanlı Deterministik Kural Motoru.
    Faz 11: Boolean bazlı ilkel yetkilendirme (allow_tevil) iptal edildi.
    Usûl sınıflarının zerk ettiği 'ruleset' sözdizimi ayrıştırılarak 
    düğüm (Node) bazlı teolojik kısıtlamalar uygulanır.
    """
    def enforce_rules(self, is_metaphor_likely: bool, ruleset: Dict[str, Any], flagged_elements: List[str] = None) -> Dict[str, Any]:
        if flagged_elements is None:
            flagged_elements = []

        if not is_metaphor_likely:
            return {
                "action": "PROCEED_LITERAL",
                "reason": "Karîne tespit edilmedi. Doğrudan Z3 Ontolojisine (Hakikat) yollanacak."
            }

        # 1. Mutlak Sıfır-Transformasyon (Zero-Transformation) Kısıtı
        if not ruleset.get("allow_tevil", False):
            return {
                "action": "BLOCK",
                "reason": f"Usûl kuralları te'vili (mecazı) mutlak reddeder. İhlal Verisi: {flagged_elements}"
            }
            
        # 2. Düğüm (Node) Bazlı Teolojik Yasaklar (DSL Otoritesi)
        blocked_nodes = ruleset.get("blocked_nodes", [])
        for element in flagged_elements:
            # L1'den gelen Rel_ edge verisini (Örn: Yed_Allah) parçala
            nodes = element.split('_')
            for node in nodes:
                if node in blocked_nodes:
                    return {
                        "action": "BLOCK",
                        "reason": f"[L2 Otorite İhlali] '{node}' düğümü üzerinde te'vil yapılması Usûl DSL'i tarafından spesifik olarak yasaklanmıştır."
                    }

        return {
            "action": "OVERRIDE_APPROVED",
            "reason": f"Karîne-i Mânia Usûl tarafından onaylandı. Spesifik bir düğüm yasağına takılmadı. Etkilenenler: {flagged_elements}"
        }