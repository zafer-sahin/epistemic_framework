from typing import List
from linguistics.contextual_lexicon import StrictAirGapValidator

class EpistemicTokenizer:
    """
    Epistemik Derleyici İçin Gelişmiş Tokenizer.
    Faz 10.3: Clitic Splitting (Bitişik Edat Ayrıştırma) entegre edildi.
    Faz 2 - Adım 2.2: Lam-ı Tevkîd ('la') ön eki sisteme tanıtıldı.
    Faz 2 - İlm-i Ma'ânî: Kasr edatlarının (İnnemâ, İllâ) bitişik formlardan korunması.
    'wa-', 'fa-', 'bi-', 'li-', 'ka-', 'la-' gibi ön ekleri (Prefixes) gövdeden
    ayırarak Sarf motorunun yapısal imza (C-V) algoritmasını korur.
    
    [FAZ 11 ENTEGRASYONU]: İstatistiksel/Regex tabanlı ayıklama (re modülü) 
    donanımsal olarak yasaklanmış; yerine karakter tabanlı cebirsel dizi 
    (algebraic sequence traversal) mantığı getirilmiştir. Air-Gapped izolasyon 
    gereği, metin parçalama işlemi deterministik sınırlarla mühürlenmiştir.
    """
    def __init__(self):
        # Bitişik yazılan edat ve bağlaçlar (Harf-i Cer, Atıf harfleri ve Lam-ı Tevkîd)
        self.clitic_prefixes = ['wa', 'fa', 'bi', 'li', 'ka', 'la']
        # Kasr edatları yapısal olarak bölünmemelidir.
        self.protected_particles = ['innema', 'illa']
        
    def _algebraic_extract_tokens(self, sentence: str) -> List[str]:
        """
        Regex (re.findall) yerine, cebirsel karakter taraması (State Machine).
        Olasılıksal sınır kaymalarını engeller ve deterministik parçalama sağlar.
        """
        tokens = []
        current_token = []
        # Klasik transliterasyon harfleri (i'rab ve uzatma şapkaları dahil)
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzâêîôûıöüçşğ_'-")
        
        for char in sentence.lower():
            if char in allowed_chars:
                current_token.append(char)
            else:
                if current_token:
                    tokens.append("".join(current_token))
                    current_token = []
        if current_token:
            tokens.append("".join(current_token))
        return tokens
        
    def tokenize(self, sentence: str, epoch: str = "Classical") -> List[str]:
        # [FAZ 11] Tokenizasyon katmanında da tarihsel (epoch) izolasyon doğrulaması
        StrictAirGapValidator.validate_epoch(epoch)
        
        if not sentence:
            return []
            
        # 1. Noktalama işaretlerini ayıkla ve cebirsel diziye göre böl
        raw_tokens = self._algebraic_extract_tokens(sentence)
        
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