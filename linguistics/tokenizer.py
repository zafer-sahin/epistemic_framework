import re
from typing import List

class EpistemicTokenizer:
    """
    Ham metni temizleyerek sentaktik ve morfolojik analiz 
    için hazır token dizilerine (stream) dönüştürür.
    """
    def __init__(self):
        # Kelime sonlarındaki i'rab alametlerini ve özel karakterleri izole etme pattern'i
        self.clean_pattern = re.compile(r'[^\w\s]')

    def tokenize(self, text: str) -> List[str]:
        # Metni temizle ve boşluklara göre böl
        clean_text = self.clean_pattern.sub('', text)
        tokens = clean_text.strip().split()
        
        if not tokens:
            raise ValueError("[TOKEN HATASI] Boş veya geçersiz metin girdisi.")
            
        return tokens