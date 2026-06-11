import pytest
from linguistics.tokenizer import EpistemicTokenizer
from linguistics.sarf_parser import SarfEngine
from core.exceptions import DiachronicViolationError

"""
.. felsefe_notu:: Literate Testing ve İspat-ı Vücûd
    Yazılım mühendisliğindeki 'Birim Testleri' (Unit Tests), deterministik bir çıkarım motorunda 
    (Epistemic Framework) 'Mantıksal İspat' (Proof of Concept) işlevi görür. Bu modül; 
    1. Kasr edatlarının (İnnema, İlla) bölünemez (Monadic) bütünlüğünü,
    2. İstatiksel kelime ayırıcıların (Stemmer) reddedilip cebirsel ayrıştırmanın (Hadd-i Lafzî) çalıştığını,
    3. Gayri Munsarif (Diptotes) lafızlardaki i'rab istisnalarının 'Semantic Shift' 
       (Fail-Meful kayması) üretmeden Z3 uzayına kilitlendiğini matematiksel olarak doğrular.
"""

class TestIlmIImlaVeSarf:
    
    def setup_method(self):
        """
        Her test öncesi yalıtılmış (Air-Gapped) İmlâ ve Sarf motorları sıfırdan ayağa kaldırılır.
        """
        self.tokenizer = EpistemicTokenizer()
        self.sarf_engine = SarfEngine()

    def test_monadic_integrity_of_kasr_particles(self):
        """
        .. mantik_kurali:: Cüz-i Lâyetecezzâ (Bölünemeyen Monad)
        'İnnema' (Sadece/Ancak) kelimesi yapısal olarak 'inna' ve 'ma' parçalarından 
        oluşsa da, İlm-i Ma'ânî'de 'Hasr' (Evrensel Dışlama - Universal Exclusion) 
        operatörüne dönüştüğü için ontolojik olarak bölünemez bir bütündür.
        Test, tokenizasyonun bu parçacığı 'inna' ve 'ma' olarak istatistiksel bir hatayla 
        parçalamadığını (Monadic Integrity) ispatlar.
        """
        sentence = "innema zeydun kaimun"
        tokens = self.tokenizer.tokenize(sentence)
        
        # 'innema' monadının parçalanmadığı ve tek bir cevher olarak korunduğu ispatlanmalıdır.
        assert "innema" in tokens
        assert "inna" not in tokens
        assert "ma" not in tokens
        assert len(tokens) == 3

    def test_clitic_extraction_araz_from_cevher(self):
        """
        .. pedagojik_anlati:: Araz'ın Cevherden Ayrılması (Clitic Extraction)
        'wazeydun' (ve Zeyd) lafzında 'wa' (ve) bağımsız bir varlık (Cevher) değil, 
        iki düğümü birbirine bağlayan mantıksal bir kenardır (Araz/Edge). 
        Bu test, deterministik ayrıştırıcının harf-i atıfları asıl varlıktan 
        başarıyla izole ederek AST yapraklarını temizlediğini doğrular.
        """
        sentence = "wazeydun fazeydun bimaradin"
        tokens = self.tokenizer.tokenize(sentence)
        
        expected_tokens = ["wa", "zeydun", "fa", "zeydun", "bi", "maradin"]
        assert tokens == expected_tokens

    def test_diachronic_violation_rejection(self):
        """
        .. felsefe_notu:: Anakronizm Filtresi (Air-Gapped Validation)
        Z3 SMT matrisine modern seküler veya MSA (Modern Standard Arabic) 
        kavramlarının sızması (Double Conversion) sistemi zehirler. 
        Test, 'Modern' zaman damgasıyla gelen her türlü tokenizasyon 
        girişiminin donanımsal olarak reddedildiğini ispatlar.
        """
        with pytest.raises(DiachronicViolationError) as exc_info:
            self.tokenizer.tokenize("zeydun", epoch="Modern")
            
        assert "Classical" in str(exc_info.value)
        assert "reddedildi" in str(exc_info.value)

    def test_generative_morphology_and_hidden_pronoun(self):
        """
        .. mantik_kurali:: Müstatir Zamir İnjeksiyonu (DRT Axiom Verification)
        'Her eylemin bir faili vardır' (Ex Falso Quodlibet'ten kaçış) aksiyomu gereği, 
        yalın bir fiil (Örn: 'Daraba' - Vurdu) Sarf motorundan geçirildiğinde, kalıbının 
        (CaCaCa -> Fa'ala) tespit edilip içeriğindeki gizli failin ('Huve') DRT varoluşsal 
        düğümü olarak dışarı kusulması gerekir.
        """
        # "daraba" kelimesi CaCaCa (Fa'ala) kalıbındadır.
        words = ["daraba"]
        lexicon = self.sarf_engine.derive_lexicon(words)
        
        morph = lexicon.get("daraba")
        assert morph is not None
        assert morph.ontologic_type == "Fiil"
        assert morph.pattern == "Fa'ala"
        # Ontolojik failsizlik krizini önleyen müstatir zamirin ('Huve') varlığı ispatlanır:
        assert morph.hidden_pronoun == "Huve"

    def test_diptote_semantic_shift_prevention(self):
        """
        .. felsefe_notu:: İlleteyn ve Gayri Munsarif (Diptotes) Zırhı
        Özel isimler ('ibrahim', 'makkah') gibi iki illete sahip kelimeler cer (majrur) 
        durumunda fetha ('a') alırlar. İstatistiksel NLP bu 'a' sesini görünce kelimeyi 
        Meful (nesne) zannederek cümlenin ontolojik yönünü (Semantic Shift) tersine çevirir.
        Test, Sarf motorunun bu lafızları 'is_diptote=True' bayrağıyla mühürleyip 
        Z3 SMT motorunda yaşanacak bir Combinatorial Explosion'u engellediğini doğrular.
        """
        # 'ibrahima' cer durumunda esre yerine fetha almış bir Gayri Munsarif kelimesidir.
        words = ["ibrahima"]
        lexicon = self.sarf_engine.derive_lexicon(words)
        
        morph = lexicon.get("ibrahima")
        assert morph is not None
        assert morph.is_diptote is True
        # Asl'a (köke) rücu edilmiştir:
        assert morph.root == "ibrahim"
        # SMT'yi çökertmemek için sentaktik çözücüye çoklu olasılık (Mansub_or_Majrur) bırakılır:
        assert morph.irab == "Mansub_or_Majrur"

    def test_nominal_ending_resolution(self):
        """
        .. mantik_kurali:: İ'rabın Deterministik Tespiti
        Sarf motoru, Münevven (Tenvinli) kelimelerin i'rabını doğru süzerek 
        Kripke uzayında amil-mamul ağacı için gerekli olan hareke kodlamasını 
        (Marfu, Mansub, Majrur) netleştirmelidir.
        """
        words = ["zeydun", "zeydan", "zeydin"]
        lexicon = self.sarf_engine.derive_lexicon(words)
        
        assert lexicon["zeydun"].irab == "Marfu"
        assert lexicon["zeydan"].irab == "Mansub"
        assert lexicon["zeydin"].irab == "Majrur"
        assert lexicon["zeydun"].pattern == "Alem/Camid_Munevven"