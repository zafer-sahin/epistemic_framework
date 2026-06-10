from typing import List
from linguistics.contextual_lexicon import StrictAirGapValidator

class EpistemicTokenizer:
    """
    .. pedagojik_anlati:: İlm-i İmlâ ve Ontolojik Ayrıştırma
    Klasik Arapça felsefesinde 'Lafız' (sözcük), mananın salt bir taşıyıcısı değil, hakikatin
    zihinsel (zihnî) ve haricî (objektif) dünyadaki izdüşümünün (delâlet) yapıtaşıdır. 
    EpistemicTokenizer, salt bir metin parçalayıcı (parser) değil, lafzın ontolojik sınırlarını 
    (Hadd-i Lafzî) tayin eden birinci seviye bir hakemdir. Geleneksel istatistiksel NLP 
    yaklaşımlarının olasılıksal (probabilistic) bulanıklığını reddederek, kelimeleri 
    Aristotelesçi ve İbn Sînâcı 'Cevher' (Substance) ve 'Araz' (Accident) hiyerarşisine 
    göre deterministik bir şekilde izole eder.
    """
    def __init__(self):
        # .. mantik_kurali:: Edatların Ontolojik Bağımlılığı (Ma fî Gayrihi)
        # 'wa' (Atıf/Cem), 'fa' (Sebebiyye/Ta'kib), 'bi' (İlsak), 'li' (İhtisas), 
        # 'ka' (Teşbih) ve 'la' (Tevkîd) edatları, felsefi olarak kendi başlarına (müstakil) 
        # bir varlık alanına işaret etmezler. Onlar, Z3 FOL matrisindeki mantıksal 
        # kapıların (And, Implies) ve modal operatörlerin (Zorunluluk) morfolojik 
        # yansımalarıdır. Bu eklerin (Araz) kök kelimeden (Cevher) ayrıştırılması, 
        # Sarf motorunun İ'lâl ve İbdâl süreçlerinde Asl'a (kökene) rücu edebilmesi 
        # için matematiksel bir zorunluluktur.
        self.clitic_prefixes = ['wa', 'fa', 'bi', 'li', 'ka', 'la']
        
        # .. felsefe_notu:: Edât-ı Kasr ve Muktazâ el-Hâl'in Korunması
        # 'İnnema' (Sadece/Ancak) ve 'İlla' (İstisna) gibi kasr edatları, İlm-i Ma'ânî'de 
        # hükmü belirli bir varlığa hapsetme (restriction) işlevi görür. Bu parçacıkların 
        # yanlışlıkla ayrıştırılması, önermenin sınırlarını yıkarak mantıksal kapsamı 
        # (scope) evrenselleştirir (Universal Quantification). Bu varlıklar yapısal
        # olarak bölünemez monadlar (cüz-i lâyetecezzâ) hükmündedir.
        self.protected_particles = ['innema', 'illa']
        
    def _algebraic_extract_tokens(self, sentence: str) -> List[str]:
        """
        .. felsefe_notu:: İhtimaliyetin Reddi ve Kesinlik (Yakîn) İnşası
        Batılı kökenli RegEx (Düzenli İfadeler) motorları, doğaları gereği istatistiksel 
        durum makinelerine (NFA/DFA) dayanır ve bağlamsal sapmalara (Zan) açıktır. 
        Klasik mantıkta Zan, hakikati (Yakîn) ikame edemez. Bu metod, dışsal Regex 
        kütüphanelerine olan bağımlılığı keserek (Air-Gap), lafızları sadece izin 
        verilen ontolojik transliterasyon alfabesi üzerinden cebirsel (algebraic) 
        bir dizi taramasıyla (state transition) mutlak deterministik sınırlarla mühürler.
        """
        tokens = []
        current_token = []
        # Harfler, hareke ve i'rab belirteçlerini barındıran kapalı evren kümesi (Closed World Set)
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
        # .. mantik_kurali:: Tarihsel İzole ve Anakronizm Filtresi
        # Tokenizasyon katmanına giren her lafız, belirli bir felsefi dönemin (Classical Epoch) 
        # ontolojik kısıtlarına tabidir. Modern seküler anlam kaymalarının sisteme sızmaması 
        # için katı (Strict) bir epistemik sınır denetimi (Validation) icra edilir.
        StrictAirGapValidator.validate_epoch(epoch)
        
        if not sentence:
            return []
            
        # Saf lafızların istatistiksel olmayan yollarla elde edilmesi
        raw_tokens = self._algebraic_extract_tokens(sentence)
        
        normalized_tokens = []
        for token in raw_tokens:
            # İstisna kuralı: Kasr ve Hasr edatlarının monadik bütünlüğünün korunması
            if token in self.protected_particles:
                normalized_tokens.append(token)
                continue
                
            split_occurred = False
            
            # .. pedagojik_anlati:: Araz'ın Cevher'den Ayrıştırılması (Clitic Splitting)
            # Döngü, bitişik nizamdaki mantıksal operatörleri (Harf) asıl kelimeden (İsim/Fiil) 
            # ayırarak (Splitting), Z3 SMT çözücüsünde kullanılacak soyut sözdizim 
            # ağacının (AST) temel yapraklarını (leaf nodes) oluşturur.
            for prefix in self.clitic_prefixes:
                if token.startswith(prefix) and len(token) > len(prefix) + 2:
                    remainder = token[len(prefix):]
                    
                    # Eğer ayrışma sonucu kalan kısım kendi başına bir monad ise (Örn: wa+innema)
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
            
            # Herhangi bir Araz (ek) taşımayan saf Cevher (kök kelime)
            if not split_occurred:
                normalized_tokens.append(token)
                
        return normalized_tokens