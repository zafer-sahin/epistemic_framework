import re
from typing import List

class EpistemicTokenizer:
    """
    Epistemik Derleyici İçin Gelişmiş Tokenizer.
    Faz 10.3: Clitic Splitting (Bitişik Edat Ayrıştırma) entegre edildi.
    Faz 2 - Adım 2.2: Lam-ı Tevkîd ('la') ön eki sisteme tanıtıldı.
    Faz 2 - İlm-i Ma'ânî: Kasr edatlarının (İnnemâ, İllâ) bitişik formlardan korunması.
    'wa-', 'fa-', 'bi-', 'li-', 'ka-', 'la-' gibi ön ekleri (Prefixes) gövdeden
    ayırarak Sarf motorunun yapısal imza (C-V) algoritmasını korur.
    """
    def __init__(self):
        # Bitişik yazılan edat ve bağlaçlar (Harf-i Cer, Atıf harfleri ve Lam-ı Tevkîd)
        self.clitic_prefixes = ['wa', 'fa', 'bi', 'li', 'ka', 'la']
        # Kasr edatları yapısal olarak bölünmemelidir.
        self.protected_particles = ['innema', 'illa']
        
    def tokenize(self, sentence: str) -> List[str]:
        if not sentence:
            return []
            
        # 1. Noktalama işaretlerini ayıkla ve boşluklara göre böl
        raw_tokens = re.findall(r'\b\w+\b', sentence.lower())
        
        normalized_tokens = []
        for token in raw_tokens:
            if token in self.protected_particles:
                normalized_tokens.append(token)
                continue
                
            split_occurred = False
            # 2. Clitic Splitting (Ön ek ayrıştırma)
            for prefix in self.clitic_prefixes:
                if token.startswith(prefix) and len(token) > len(prefix) + 2:
                    # Eğer kelimenin kalanı korumalı bir edatsa (Örn: wa+innema)
                    remainder = token[len(prefix):]
                    if remainder in self.protected_particles:
                        normalized_tokens.append(prefix)
                        normalized_tokens.append(remainder)
                        split_occurred = True
                        break
                    else:
                        normalized_tokens.append(prefix)
                        normalized_tokens.append(remainder)
                        split_occurred = True
                        break
            
            if not split_occurred:
                normalized_tokens.append(token)
                
        return normalized_tokens