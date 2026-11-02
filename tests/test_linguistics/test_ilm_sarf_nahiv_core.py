import unittest
import z3
import networkx as nx

from linguistics.sarf_parser import SarfEngine, MorphologicalAnalysis
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.discourse_state import DiscourseRegister, DenialLevel
from core.logic_parser import Z3ExpressionBuilder
from core.exceptions import ContextPoisoningError

class TestIlmSarfNahivCore(unittest.TestCase):
    """
    .. pedagojik_anlati:: Faz 1 - Çekirdek Gramer ve Ontolojik Bütünlük Testleri
    Bu test paketi, Dars-i Nizâmî müfredatındaki Sarf ve Nahiv kaidelerinin 
    deterministik SMT (Satisfiability Modulo Theories) motoruna kayıpsız aktarımını denetler.
    Semantik kaymaları (Semantic Shift), failsiz eylem çökmelerini (Ex Falso Quodlibet) 
    ve bağlam zehirlenmelerini (Context Poisoning) simüle eder.
    """

    def setUp(self):
        self.sarf_engine = SarfEngine()
        self.nahiv_compiler = NahivDependencyCompiler()
        self.discourse_register = DiscourseRegister()
        self.z3_builder = Z3ExpressionBuilder(max_depth=15)

    def test_01_gayri_munsarif_diptote_constraint(self):
        """
        .. mantik_kurali:: İ'rab Kısıtları ve Semantic Shift Engeli
        Gayri Munsarif kelimelerin fetha alarak cer durumunda kalabilmesi kuralının, 
        AST tarafından yanlışlıkla Meful (Mansub) sanılmasını engelleyecek is_diptote bayrağının denetimi.
        """
        # "makkaha" (Mekke'de/Mekke'ye) - Normalde 'a' ile biterse Mansub olur, ancak diptote olduğu için Majrur da olabilir.
        lexicon = self.sarf_engine.derive_lexicon(["makkaha"])
        analysis = lexicon.get("makkaha")
        
        self.assertIsNotNone(analysis)
        self.assertTrue(analysis.is_diptote, "Gayri Munsarif kelime otonom olarak tespit edilemedi.")
        self.assertEqual(analysis.irab, "Mansub_or_Majrur", "İ'rab kısıtı fetha durumunda yanlış atandı.")

    def test_02_inne_epistemic_operator_and_zero_copula(self):
        """
        .. mantik_kurali:: Epistemik Zorunluluk ve Kadiyye-i Hamliyye
        'İnne' amilinin epistemik (Necessity) kilit yaratması ve isim cümlesindeki 
        görünmez Rabıta (Zero-Copula) düğümünün AST'ye otonom olarak zerk edilmesi.
        """
        tokens = ["inne", "zeydan", "kaimun"]
        
        # Test izole lexicon mock'laması (Sarf'ın tam entegre çalışması beklenmeden saf AST denetimi)
        lexicon = {
            "inne": MorphologicalAnalysis(original_word="inne", root="inne", pattern="Harf_Inne", ontologic_type="Harf_Inne", thematic_role="Epistemic_Operator"),
            "zeydan": MorphologicalAnalysis(original_word="zeydan", root="zeyd", pattern="Alem", ontologic_type="Ism", thematic_role="Entity", irab="Mansub", gender="Muzekker", number="Mufred"),
            "kaimun": MorphologicalAnalysis(original_word="kaimun", root="kaim", pattern="Fa'il", ontologic_type="Ism", thematic_role="Agent", irab="Marfu", gender="Muzekker", number="Mufred")
        }
        
        dependencies = self.nahiv_compiler.suggest_dependencies(tokens, lexicon)
        ast_graph = self.nahiv_compiler.build_ast(tokens, dependencies, lexicon)
        
        # İnne'nin amel denetimi
        edges = list(ast_graph.edges(data=True))
        inne_ism_edge = next((e for e in edges if e[0] == "inne" and e[1] == "zeydan"), None)
        inne_haber_edge = next((e for e in edges if e[0] == "inne" and e[1] == "kaimun"), None)
        
        self.assertIsNotNone(inne_ism_edge)
        self.assertEqual(inne_ism_edge[2]['irab'], "Mansub")
        self.assertEqual(inne_ism_edge[2]['z3_mapping'], "ModalNecessity")
        
        self.assertIsNotNone(inne_haber_edge)
        self.assertEqual(inne_haber_edge[2]['irab'], "Marfu")

    def test_03_mutaallak_space_sort_allocation(self):
        """
        .. mantik_kurali:: Zarf-ı Mustakar ve SpaceSort Mührü
        Eğer cümlede açık bir fiil yoksa harf-i cer'in (Mekân zarfı), ontolojik olarak 
        Kainun_Virtual (Zımni Mevcudiyet) düğümüne bağlanıp bağlanmadığının denetimi.
        """
        tokens = ["zeydun", "fi", "al_beyt"]
        lexicon = {
            "zeydun": MorphologicalAnalysis(original_word="zeydun", root="zeyd", pattern="Alem", ontologic_type="Ism", thematic_role="Entity", irab="Marfu"),
            "fi": MorphologicalAnalysis(original_word="fi", root="fi", pattern="Harf", ontologic_type="Harf"),
            "al_beyt": MorphologicalAnalysis(original_word="al_beyt", root="beyt", pattern="Alem", ontologic_type="Ism", thematic_role="Entity", irab="Majrur")
        }
        
        dependencies = self.nahiv_compiler.suggest_dependencies(tokens, lexicon)
        ast_graph = self.nahiv_compiler.build_ast(tokens, dependencies, lexicon)
        
        # Kainun_Virtual düğümü otomatik üretilmeli ve fi ona bağlanmalı (Zarf_Mustakar)
        self.assertTrue(ast_graph.has_node("Kainun_Virtual"))
        mutaallak_edge = ast_graph.get_edge_data("Kainun_Virtual", "fi")
        
        self.assertIsNotNone(mutaallak_edge)
        self.assertEqual(mutaallak_edge['relation'], "Muteallak_Mekan")
        self.assertEqual(mutaallak_edge['z3_mapping'], "SpaceSortConstraint")

    def test_04_drt_virtual_minting_and_context_sealing(self):
        """
        .. mantik_kurali:: Müstatir Zamir İrcâsı ve Bağlam Zehirlenmesi (Context Poisoning) Zırhı
        1. Failsiz eyleme sanal (Virtual) DRT düğümü basılması.
        2. Çapraz mu'aradah (itiraz) esnasında rakip uzayına atıf yapılmasının engellenmesi.
        """
        # Mucîb'in kendi uzayına eylem ve müstatir zamir basması
        self.discourse_register.set_agent("Mujib")
        virtual_fail_id = self.discourse_register.mint_virtual_entity("huve", "Eshari_Usul")
        
        # Sâil'in kendi sırasına geçip, Mucîb'in failine atıf yapmaya çalışması (Context Poisoning denemesi)
        self.discourse_register.set_agent("Sail")
        self.discourse_register.add_mention(word="daraba", ontologic_id="Action_01", active_namespace="Salafi_Usul")
        
        with self.assertRaises(ContextPoisoningError) as context:
            # Sâil, kasten Mucîb'in usûl uzayına uzanmaya çalışıyor
            self.discourse_register.resolve_pronoun("huve", enforcement_namespace="Eshari_Usul")
            
        self.assertIn("Bağlam Zehirlenmesi", str(context.exception))

    def test_05_z3_kripke_space_time_sort_compilation(self):
        """
        .. mantik_kurali:: Çok Boyutlu N-Ary Yüklem Derlemesi
        Logic Parser'ın herhangi bir predikat çağrısında (Örn: Daraba);
        w (World), t_zati (TimeZati), t_vasfi (TimeVasfi) ve s (Space) matrislerini 
        otomatik arite artırımı (+4) ile derleyebildiğinin testi.
        """
        # Logic uzayında 2 ariteli bir fiil bildirimi (Daraba(x, y))
        predicate = self.z3_builder.get_or_create_predicate("Daraba", arity=2)
        
        # Beklenen: Z3 motorunda bu fonksiyon aslında 6 boyutlu olmalıdır (4 Kripke sabitesi + 2 argüman)
        self.assertEqual(predicate.arity(), 6, "Z3 Expression Builder arite genişletmesini (Space/Time) yapamadı.")
        
        # AST'den gelen string formatlı bir Kripke eşlemesinin parse edilmesi
        try:
            expr = self.z3_builder.parse("Daraba(Zeyd, Amr)")
            self.assertIsInstance(expr, z3.ExprRef, "Z3 parse operasyonu başarısız.")
        except Exception as e:
            self.fail(f"Z3 Kripke Uzay derlemesi hata fırlattı: {e}")

if __name__ == '__main__':
    unittest.main()