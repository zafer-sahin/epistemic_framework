import pytest
from linguistics.contextual_lexicon import ContextualLexicon, StrictAirGapValidator, LocalOntoLexSemanticClient
from linguistics.discourse_state import DiscourseRegister, DenialLevel
from linguistics.pragmatics import MaaniSpeechActAnalyzer, MuktazaHalAnalyzer
from core.exceptions import DiachronicViolationError, ContextPoisoningError

"""
.. felsefe_notu:: Literate Testing ve İlm-i Ma'ânî / İlm-i Vaz' İspatları
    Z3 SMT motoru, Boolean ('True/False') çalışan seküler bir deterministtir. Ancak 
    İslâm felsefesinde 'Hakikat', salt sözlük anlamı (Lügat) değil; zamanın (Epoch), 
    usûlün (Namespace) ve muhatabın (Sâil) psikolojik durumunun (Muktazâ el-Hâl) 
    matematiksel bir kesişimidir.
    
    Bu test modülü;
    1. Sistemin 'WordNet' veya 'MSA' gibi modern/seküler ağlara (Çifte Dönüşüm) 
       bağlanmasının donanımsal olarak engellendiğini (Air-Gap),
    2. 'Mu'aradah' (Diyalektik Çarpışma) esnasında Sâil'in, Mucîb'in felsefi matrisinden 
       kavram çalamayacağını (Lexical Poisoning / Bağlam Zehirlenmesi),
    3. İnşâî (Soru/Emir) yapıların retorik formlarının 'İstifham-ı İnkârî' mekanizmasıyla 
       katı Z3 mantıksal ret matrislerine (Universal Negation) döküldüğünü ispatlar.
"""

class TestPragmaticsAndLexicon:

    def setup_method(self):
        """
        Her test öncesi DRT (Söylem Belleği), Leksikon ve İlm-i Ma'ânî analizörleri 
        'Tabula Rasa' (Boş Zihin) konumuna getirilir.
        """
        self.discourse = DiscourseRegister()
        self.lexicon = ContextualLexicon()
        self.maani_analyzer = MaaniSpeechActAnalyzer(self.discourse)
        self.muktaza_analyzer = MuktazaHalAnalyzer(self.discourse)

    def test_strict_air_gap_validation_secular_leak(self):
        """
        .. mantik_kurali:: Anakronizm ve Sekülerizm Filtresi
        Bir İslâm mantık ispatlayıcısına 'WordNet' gibi seküler evrimsel ontolojiler sızdırılırsa, 
        İbn Sînâcı "Wajib_al_Wujud" kavramı teslis inancına ait "God" kavramına (Semantic Shift) dönüşür. 
        Test, 'StrictAirGapValidator'ın bu dışsal saldırıları ölümcül hata ile durdurduğunu ispatlar.
        """
        # Modern çağ (Epoch) sızıntısı testi
        with pytest.raises(DiachronicViolationError) as exc_info1:
            StrictAirGapValidator.validate_epoch("Modern_MSA")
        assert "reddedildi" in str(exc_info1.value)

        # Seküler kelime ağı (Namespace) sızıntısı testi
        with pytest.raises(DiachronicViolationError) as exc_info2:
            StrictAirGapValidator.validate_namespace("wordnet")
        assert "ÇİFTE DÖNÜŞÜM İHLALİ" in str(exc_info2.value)

        # Ontolojik Mühür (Provenance) sızıntısı testi
        with pytest.raises(DiachronicViolationError) as exc_info3:
            StrictAirGapValidator.validate_provenance("wn:dog")
        assert "seküler köprüler kullanılamaz" in str(exc_info3.value)

    def test_lexical_poisoning_prevention_in_dialectic(self):
        """
        .. pedagojik_anlati:: Mu'aradah (Çapraz İtiraz) ve Bağlam Zehirlenmesi Zırhı
        Münazara sırasında Sâil ve Mucîb'in DRT yığıtları (Kripke Uzayları) fiziksel olarak yalıtılmıştır. 
        Eğer Sâil, kendi usûl uzayında (Örn: Selefî) bir kelimeyi (Örn: Yed) çağırırken, dönen 
        Ontolojik ID aslında Mucîb tarafından başka bir uzayda (Örn: Eş'arî) mühürlenmişse; 
        Sâil arka kapıdan (backdoor) rakibinin argümanını 'çalmış' olur. 
        Test, bu ontolojik hırsızlığın (Context Poisoning) engellendiğini ispatlar.
        """
        # Mucîb (Eş'arî uzayında) bir kavramı mühürlüyor
        self.discourse.set_agent("Mujib")
        self.discourse.add_mention(word="Yedullah", ontologic_id="Onto_Kudret_1", active_namespace="Ashari")
        
        # Test için 'Yedullah' kavramı aynı ontolojik ID ile 'Salafi' uzayına gizlice kaydediliyor
        self.lexicon.register_word("Yedullah", "Salafi", "Onto_Kudret_1")
        
        # Diyalektik nöbet Sâil'e (Selefî) geçiyor
        self.discourse.set_agent("Sail")
        
        # Sâil, kendi uzayında bu kavramı çağırdığında, motor bu ID'nin Mucîb tarafından 
        # farklı bir uzayda mühürlendiğini (Bipartite Graph sızıntısı) tespit edip durmalıdır.
        with pytest.raises(ContextPoisoningError) as exc_info:
            self.lexicon.resolve_id("Yedullah", "Salafi", discourse=self.discourse)
            
        assert "Lexical Poisoning (Leksikal Zehirlenme) Tespit Edildi" in str(exc_info.value)
        assert "arka kapı (backdoor) eşdeğerliği engellendi" in str(exc_info.value)

    def test_muktaza_el_hal_entropy_and_tevkid_balance(self):
        """
        .. mantik_kurali:: Tevkîd (Pekiştirme) ve Zihinsel Entropi (Muktazâ el-Hâl)
        Sa'deddin et-Taftazânî'nin Mutavvel eserine göre, muhatabın zihni boşsa (Khali_al_Zihn) 
        cümleyi "İnne" (Şüphesiz/Muhakkak) gibi epistemik zorunluluklarla kurmak retorik bir 
        israftır ve Kripke uzayında sahte kombinatoryal yük yaratır. Eğer muhatap inkâr 
        makamındaysa (Munkir), cümleyi tevkîdsiz kurmak hakikati savunmada zafiyettir.
        Test, bu denge hakeminin SMT öncesi devrede olduğunu doğrular.
        """
        # Durum 1: Zihin boş (KHALI_AL_ZIHN) iken Tevkîd kullanımı (HATA)
        self.discourse.set_opponent_epistemic_state(DenialLevel.KHALI_AL_ZIHN)
        # Tevkid_Modifier bağımlılığı enjekte ediliyor
        deps_israf = [("amil", "mamul", "Tevkid_Modifier", "None")]
        
        res_israf = self.muktaza_analyzer.evaluate_balance(deps_israf)
        assert res_israf["is_valid"] is False
        assert "Khali_al_Zihn" in res_israf["message"]
        
        # Durum 2: Muhatap Munkir (İnkârcı) iken Tevkîd TERKİ (HATA)
        self.discourse.set_opponent_epistemic_state(DenialLevel.MUNKIR)
        # Hiçbir pekiştirme içermeyen basit bir cümle bağımlılığı
        deps_zafiyet = [("zeyd", "kaimun", "Mubteda_Haber", "Marfu")]
        
        res_zafiyet = self.muktaza_analyzer.evaluate_balance(deps_zafiyet)
        assert res_zafiyet["is_valid"] is False
        assert "Munkir" in res_zafiyet["message"]

    def test_istifham_i_inkari_existential_negation(self):
        """
        .. felsefe_notu:: İstifham-ı İnkârî ve Z3 Universal Negation
        Soru cümleleri (İnşâî) mantıksal değer taşımaz. Ancak bir soru, olumsuzluk (Nefy) edatıyla 
        geliyorsa ("Allah'tan başka ilah mı var?"), bu gerçek bir soru değil, kesin bir retorik 
        reddir (İstifham-ı İnkârî). 
        Test, İlm-i Ma'ânî analizörünün bunu basit bir 'Soru' olarak çöpe atmayıp, Z3 motoru için 
        Evrensel/Varoluşsal ret (z3.Not / Universal_Negation) kapsülüne çevirdiğini ispatlar.
        """
        tokens = ["hal", "min", "ilahin", "illa", "allah"]
        # 'hal' (mı/mi) sorudur, 'illa' (başka/hariç) ise nefy/kasr içerir.
        
        res = self.maani_analyzer.analyze_pragmatics(tokens, [])
        
        # Gerçek soru (İstifham_Hakiki) olarak değerlendirilip silinmediği ispatlanmalıdır.
        assert res["type"] == "Istifham_i_Inkari"
        assert res["z3_operator_hint"] == "Universal_Negation"
        assert "z3.Not" in res["message"]