import unittest
from unittest.mock import MagicMock

from linguistics.discourse_state import DiscourseRegister, DenialLevel
from linguistics.contextual_lexicon import ContextualLexicon, StrictAirGapValidator, LocalOntoLexSemanticClient
from linguistics.ilm_wad_adapter import IlmWadAdapter, SemanticStatementIR, NestedPredicate
from linguistics.pragmatics import MaaniSpeechActAnalyzer, MuktazaHalAnalyzer
from core.exceptions import DiachronicViolationError, ContextPoisoningError

class TestEpic3VazAndMaani(unittest.TestCase):
    """
    .. pedagojik_anlati:: Epik 3 Çapraz Katman Denetimleri
    Bu test suiti, İlm-i Vaz' (Leksikal Atama) ve İlm-i Ma'ânî (Pragmatik) disiplinlerinin 
    matematiksel sınırlarını zorlar. Z3 SMT matrislerinin seküler ontolojilere 
    (Air-Gap Violation), kombinatoryal patlamalara veya teolojik çelişkilere 
    girip girmediğini otonom olarak doğrular.
    """

    def setUp(self):
        # Söylem (Discourse) ve Leksikon (Lexicon) durum makinesi simülasyonları
        self.discourse = MagicMock(spec=DiscourseRegister)
        self.discourse.active_agent = "Sail"
        self.discourse.get_opponent_epistemic_state.return_value = DenialLevel.MUNKIR
        self.discourse.resolve_pronoun.return_value = None

        self.semantic_client = LocalOntoLexSemanticClient()
        self.lexicon = ContextualLexicon(semantic_client=self.semantic_client)
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)

    def test_faz3_1_vaz_nevi_structural_roles(self):
        """
        .. mantik_kurali:: Vaz' Nev'î (Kalıpsal Atama) Doğrulaması
        'Dârib' gibi İsm-i Fail (Fa'il) veznindeki bir kelimenin, sadece kökünden değil 
        girdiği morfolojik kalıptan ötürü Z3 matrisine otonom 'Role_Agent' yüklemi fırlatıp 
        fırlatmadığını denetler.
        """
        # [DÜZELTME]: Tevkîd (pekiştirme) olmayan yalın bir önermenin (Mubteda_Haber) 
        # Muktazâ el-Hâl filtresinden geçebilmesi için muhatabın zihninin boş olması gerekir.
        # Aksi halde sistem MUNKIR tespiti yapıp AST'yi Z3'e girmeden imha eder.
        self.discourse.get_opponent_epistemic_state.return_value = DenialLevel.KHALI_AL_ZIHN
        
        # Sarf motoru çıktısını simüle et
        mock_morph_darib = MagicMock()
        mock_morph_darib.root = "drb"
        mock_morph_darib.pattern = "Fa'il" # Vaz' Nev'î İsm-i Fail kalıbı
        mock_morph_darib.ontologic_type = "Ism"
        
        auto_lexicon = {"darib": mock_morph_darib}
        tokens = ["darib", "zeyd"]
        dependencies = [("darib", "zeyd", "Mubteda_Haber", "Raf")]
        
        # Test: SMT IR Derlemesi
        ir = self.adapter.generate_ir(
            tokens=tokens, 
            dependencies=dependencies, 
            active_namespace="Base", 
            auto_lexicon=auto_lexicon,
            epoch="Classical"
        )
        
        # Beklenti: Role_Agent (Fa'il kalıbından ötürü) matrise eklenmiş olmalıdır.
        has_agent_role = any(
            isinstance(pred, tuple) and pred[0] == "Role_Agent" 
            for pred in ir.predicates
        )
        self.assertTrue(has_agent_role, "Vaz' Nev'î: İsm-i Fail kalıbı Role_Agent üretemedi.")

    def test_faz3_2_istifham_i_inkari_logical_negation(self):
        """
        .. mantik_kurali:: İstifham-ı İnkârî Kapsülü
        Soru edatı ve nefy (olumsuzluk) edatının yan yana gelmesinin sıradan bir soru değil, 
        evrensel bir red (Universal Negation) ürettiğini doğrular.
        """
        tokens = ["hal", "min", "ilah", "illa", "allah"]
        dependencies = [("hal", "ilah", "Tevkid_Modifier", "None")]
        
        # Pragmatik Analiz
        res = self.adapter.pragmatics.analyze_pragmatics(tokens, dependencies)
        
        self.assertTrue(res["is_valid"], "İstifham-ı İnkârî geçerli bir Kadiyye sayılmalıdır.")
        self.assertEqual(res["type"], "Istifham_i_Inkari")
        self.assertEqual(res.get("z3_operator_hint"), "Universal_Negation")

    def test_faz3_2_muktaza_el_hal_balance(self):
        """
        .. matematiksel_model:: Muktazâ el-Hâl Denge Denetimi
        Muhatabın şüphe düzeyi ile cümlenin tevkîd (pekiştirme) düzeyi uyuşmazsa, 
        sistemin 'MAANI_VIOLATION' (Z3 Kombinatoryal Patlama Riski) fırlattığını doğrular.
        """
        analyzer = MuktazaHalAnalyzer(self.discourse)
        
        # Senaryo 1: Zihni boş (Khali) muhataba gereksiz tevkîd kullanılması
        self.discourse.get_opponent_epistemic_state.return_value = DenialLevel.KHALI_AL_ZIHN
        deps_with_tevkid = [("inne", "zeyd", "Amel_Inne_Ism", "Nasb")]
        
        res1 = analyzer.evaluate_balance(deps_with_tevkid)
        self.assertFalse(res1.get("is_valid", True))
        self.assertEqual(res1.get("type"), "MAANI_VIOLATION")
        
        # Senaryo 2: İnkârcı (Munkir) muhataba tevkîdsiz (yalın) cümle kurulması
        self.discourse.get_opponent_epistemic_state.return_value = DenialLevel.MUNKIR
        deps_without_tevkid = [("zeyd", "kaim", "Mubteda_Haber", "Raf")]
        
        res2 = analyzer.evaluate_balance(deps_without_tevkid)
        self.assertFalse(res2.get("is_valid", True))
        self.assertEqual(res2.get("type"), "MAANI_VIOLATION")

    def test_faz3_3_mana_el_mana_metaphorical_bridge(self):
        """
        .. felsefe_notu:: Abdülkâhir el-Cürcânî Nazm Kuramı (Ma'nâ el-Ma'nâ)
        Literal anlam SMT motorunda UNSAT (Ontolojik Uyuşmazlık) ürettiğinde (Örn: Allah ve Yed),
        sistemin kara-kutu fallback yapmak yerine, arazlar (Attribute_Power) üzerinden 
        ispatlanabilir yeni bir ontolojik düğüm ('Sifat_Kudret') türettiğini test eder.
        """
        # 'Yed' kelimesinin Base karşılığı 'Haqiqi_Yad' (Gerçek organ).
        # Allah'a izafe edildiği an UNSAT varsayılarak Metaphor_Fallback talebi açılır.
        
        inferred_id = self.lexicon.resolve_id(
            word="yed", 
            active_namespace="Base", 
            proposition_type="Metaphor_Fallback", 
            discourse=self.discourse, 
            dependencies=[], 
            epoch="Classical"
        )
        
        # Beklenti: 'Haqiqi_Yad' üzerinden 'Attribute_Power' arazı kullanılarak 'Sifat_Kudret'e sıçranmalı.
        self.assertEqual(inferred_id, "Sifat_Kudret", "Ma'nâ el-Ma'nâ köprüsü lüzum bağını (Alâka) kuramadı.")

    def test_strict_air_gap_validator(self):
        """
        .. felsefe_notu:: Çifte Dönüşüm (Double Conversion) Sızıntı Zırhı
        Z3 evrenine WordNet (wn:...) veya Modern Standart Arapça (MSA) gibi seküler 
        istatistiksel ontolojilerin sızmasının donanımsal olarak reddedildiğini doğrular.
        """
        # 1. Anakronizm Reddi
        with self.assertRaises(DiachronicViolationError):
            StrictAirGapValidator.validate_epoch("Modern")
            
        # 2. Namespace Zehirlenmesi Reddi
        with self.assertRaises(DiachronicViolationError):
            StrictAirGapValidator.validate_namespace("wordnet")
            
        # 3. Provenance (Köken) Reddi
        with self.assertRaises(DiachronicViolationError):
            StrictAirGapValidator.validate_provenance("wn:dog_1")

if __name__ == '__main__':
    unittest.main()