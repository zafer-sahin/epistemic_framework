import re
from typing import List

class EpistemicTokenizer:
    """
    Epistemik Derleyici İçin Gelişmiş Tokenizer.
    Faz 10.3: Clitic Splitting (Bitişik Edat Ayrıştırma) entegre edildi.
    'wa-', 'fa-', 'bi-', 'li-', 'ka-' gibi ön ekleri (Prefixes) gövdeden
    ayırarak Sarf motorunun yapısal imza (C-V) algoritmasını korur.
    """
    def __init__(self):
        # Bitişik yazılan edat ve bağlaçlar (Harf-i Cer ve Atıf harfleri)
        self.clitic_prefixes = ['wa', 'fa', 'bi', 'li', 'ka']
        
    def tokenize(self, sentence: str) -> List[str]:
        if not sentence:
            return []
            
        # 1. Noktalama işaretlerini ayıkla ve boşluklara göre böl
        raw_tokens = re.findall(r'\b\w+\b', sentence.lower())
        
        normalized_tokens = []
        for token in raw_tokens:
            split_occurred = False
            # 2. Clitic Splitting (Ön ek ayrıştırma)
            for prefix in self.clitic_prefixes:
                # Eğer kelime prefix ile başlıyorsa ve geriye kalan kısım 
                # tek başına anlamlı bir sülâsî kök/isim olabilecek uzunluktaysa (>2)
                if token.startswith(prefix) and len(token) > len(prefix) + 2:
                    normalized_tokens.append(prefix)
                    normalized_tokens.append(token[len(prefix):])
                    split_occurred = True
                    break
            
            if not split_occurred:
                normalized_tokens.append(token)
                
        return normalized_tokens