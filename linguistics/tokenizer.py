from typing import List
from linguistics.contextual_lexicon import StrictAirGapValidator

class EpistemicTokenizer:
    """
    .. pedagojik_anlati:: İlm-i İmlâ ve Ontolojik Ayrıştırma (Hadd-i Lafzî)
    Klasik Arapça felsefesinde 'Lafız' (sözcük), mananın salt bir taşıyıcısı değil, hakikatin
    zihinsel (zihnî) ve haricî (objektif) dünyadaki izdüşümünün (delâlet) yapıtaşıdır. 
    EpistemicTokenizer, salt bir metin parçalayıcı (parser) değil, lafzın ontolojik sınırlarını 
    (Hadd-i Lafzî) tayin eden birinci seviye bir hakemdir. 
    
    [FAZ 5 - LITERATE CHUNKING]: Geleneksel istatistiksel NLP (BPE/WordPiece) yaklaşımlarının 
    olasılıksal (probabilistic) bulanıklığı reddedilmiştir. Kelimeler, Aristotelesçi ve 
    İbn Sînâcı 'Cevher' (Substance) ve 'Araz' (Accident) hiyerarşisine göre deterministik 
    bir şekilde izole edilir.
    """
    def __init__(self):
        # .. mantik_kurali:: Edatların Ontolojik Bağımlılığı (Ma fî Gayrihi)
        # 'wa' (Atıf/Cem), 'fa' (Sebebiyye/Ta'kib), 'bi' (İlsak), 'li' (İhtisas), 
        # 'ka' (Teşbih) ve 'la' (Tevkîd) edatları, felsefi olarak kendi başlarına (müstakil) 
        # bir varlık alanına işaret etmezler. Onlar, Z3 FOL matrisindeki mantıksal 
        # kapıların (And, Implies) ve modal operatörlerin (Zorunluluk) morfolojik arazlarıdır.
        # 
        # Matematiksel Karşılığı (Clitic Splitting):
        # $$ \text{Split}: \text{Lafız} \rightarrow H \times C $$
        # Burada $H \in \text{Huruf-u Meâni}$ (Araz/Bağlaç) ve $C \in \text{Cevher}$ (Kök).
        self.clitic_prefixes = ['wa', 'fa', 'bi', 'li', 'ka', 'la']
        
        # .. felsefe_notu:: Edât-ı Kasr ve Muktazâ el-Hâl'in Korunması
        # 'İnnema' (Sadece/Ancak) ve 'İlla' (İstisna) gibi kasr edatları, İlm-i Ma'ânî'de 
        # hükmü belirli bir varlığa hapsetme (Universal Exclusion) işlevi görür. Bu 
        # parçacıkların yanlışlıkla ayrıştırılması, önermenin sınırlarını yıkarak mantıksal 
        # kapsamı evrenselleştirir. Bu varlıklar yapısal olarak bölünemez monadlar 
        # (cüz-i lâyetecezzâ) hükmündedir.
        self.protected_particles = ['innema', 'illa']
        
    def _algebraic_extract_tokens(self, sentence: str) -> List[str]:
        """
        .. felsefe_notu:: İhtimaliyetin Reddi ve Kesinlik (Yakîn) İnşası
        Batılı kökenli RegEx (Düzenli İfadeler) motorları, doğaları gereği istatistiksel 
        durum makinelerine (NFA/DFA) dayanır ve bağlamsal sapmalara (Zan) açıktır. 
        Klasik mantıkta Zan, hakikati (Yakîn) ikame edemez. 
        
        Bu metod, dışsal Regex kütüphanelerine olan bağımlılığı keserek (Air-Gap), lafızları 
        sadece izin verilen ontolojik transliterasyon alfabesi üzerinden cebirsel (algebraic) 
        bir dizi taramasıyla (Deterministic State Transition) mutlak sınırlarla mühürler.
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

    def _apply_monadic_clitic_splitting(self, token: str) -> List[str]:
        """
        .. mantik_kurali:: Cebirsel Monad Ayrıştırması ve Özyineli Araz Yalıtımı
        Arapçada 'Huruf-u Meâni' (Arazlar/Edatlar) birbirleri üzerine binebilir (Örn: wa-la-innema).
        Bu metod, kelimenin önündeki arazları cebirsel bir özyineleme (recursion) ile soyarken, 
        Kasr edatları gibi korunması gereken monadların (Cevher) bütünlüğünü garanti altına alır.
        
        Birinci seviye tokenizasyonda Kripke uzayına (SMT) gidecek mantıksal operatörlerin 
        (Universal Exclusion) bozulmaması kritik bir zorunluluktur.
        """
        # 1. Monadik Bütünlük Koruması: Token zaten bir monad ise parçalamayı derhal durdur
        if token in self.protected_particles:
            return [token]
            
        # 2. Öncelikli Araz (Clitic) Taraması ve Hiyerarşik Ayrıştırma
        for prefix in self.clitic_prefixes:
            # Tire (-) ile ayrılmış transliterasyon yapıları için temizlik (Örn: wa-innema)
            target_prefix = prefix + "-" if token.startswith(prefix + "-") else prefix
            
            if token.startswith(target_prefix):
                remainder = token[len(target_prefix):]
                
                # a) Kalan kısım korumalı bir monad ise (Örn: wa-innema -> wa, innema)
                if remainder in self.protected_particles:
                    return [prefix, remainder]
                
                # b) Kalan kısım asgari kök (Cevher) olabilecek potansiyeldeyse (en az 3 harf/Sülâsî)
                if len(remainder) >= 3:
                    # Yığılmış arazları (Örn: fa-li-yakul) çözmek için derinlemesine özyineleme (recursion)
                    recursive_split = self._apply_monadic_clitic_splitting(remainder)
                    return [prefix] + recursive_split
                    
        # 3. Hiçbir araz bağıntısı bulunamadıysa lafzı (Cevher) bütünüyle döndür
        return [token]
        
    def tokenize(self, sentence: str, epoch: str = "Classical") -> List[str]:
        """
        .. pedagojik_anlati:: Tokenizasyon Orkestrasyonu
        Sistemin dış dünya (serbest metin) ile ilk temas noktasıdır. 
        
        [FAZ 5: AIR-GAPPED ONTOLOGY]: Tokenizasyon katmanına giren her lafız, belirli bir 
        felsefi dönemin (Classical Epoch) ontolojik kısıtlarına tabidir. Modern seküler 
        (MSA/İngilizce) anlam kaymalarının Z3 matrisine sızmaması için katı (Strict) bir 
        epistemik sınır denetimi (Validation) icra edilir.
        """
        StrictAirGapValidator.validate_epoch(epoch)
        
        if not sentence:
            return []
            
        # Saf lafızların istatistiksel olmayan yollarla elde edilmesi
        raw_tokens = self._algebraic_extract_tokens(sentence)
        
        normalized_tokens = []
        for token in raw_tokens:
            # Edat yığılmalarını (Clitic stacking) ve monadları cebirsel matrise göre ayrıştır
            split_result = self._apply_monadic_clitic_splitting(token)
            normalized_tokens.extend(split_result)
                
        return normalized_tokens