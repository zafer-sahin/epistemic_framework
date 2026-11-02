import unittest
import networkx as nx
from typing import Dict, Any, List, Tuple

from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.pragmatics import MaaniSpeechActAnalyzer
from linguistics.discourse_state import DiscourseRegister, DenialLevel
from linguistics.sarf_parser import MorphologicalAnalysis

"""
.. felsefe_notu:: Red-Teaming ve İmkânsızın Sınanması (Muhâl)
    İslâm mantığında "Muhâl" (İmkânsız), zihnin tasavvur edebildiği ancak dış dünyada 
    veya mantıksal uzayda tahakkuk edemeyecek durumları ifade eder. Z3 SMT çözücüsü 
    bir "Muhâl" ile (örneğin hem kesin zorunlu hem de anlık değişime tabi bir varlık) 
    karşılaştığında sonsuz kısıt yayılımına (Infinite Propagation) girerek kilitlenir. 
    Bu test paketi, sistemi bu tür teolojik ve mantıksal paradokslarla kasıtlı olarak 
    vurarak (Red-Teaming), Asiklik Bariyerlerin ve Çapraz Katman Sağlık Denetiminin 
    (Cross-Layer Health Barrier) düzgün çalışıp çalışmadığını doğrular.
"""

class TestCombinatorialExplosion(unittest.TestCase):
    
    def setUp(self):
        """
        [FAZ 14 E2E STRESS TEST SETUP]
        Test izolasyonunu sağlamak için boş bir Söylem Belleği (DiscourseRegister)
        ve taze derleyici örnekleri (Compiler Instances) ayağa kaldırılır.
        """
        self.discourse = DiscourseRegister()
        self.nahiv_compiler = NahivDependencyCompiler()
        self.maani_analyzer = MaaniSpeechActAnalyzer(self.discourse)

    def test_epistemic_collapse_inne_and_fa(self):
        """
        .. mantik_kurali:: Epistemic Collapse (Zorunluluk vs Dinamik Geçiş)
        Senaryo: Bir önermede 'İnne' (Mutlak Zorunluluk) ve 'Fâ-i Füzâiyye' 
        (Ani Durum Geçişi) aynı AST üzerinde Z3'e yollanmaya çalışılırsa, sistem 
        "Ontolojik Çelişki" vererek durmalıdır.
        """
        # Manuel AST Simülasyonu
        ast = nx.DiGraph()
        ast.add_node("inne", virtual=False)
        ast.add_node("zeyden", virtual=False)
        ast.add_node("fa", virtual=False)
        ast.add_node("cae", virtual=False)
        
        ast.add_edge("inne", "zeyden", relation="Amel_Inne_Ism", irab="Mansub")
        ast.add_edge("zeyden", "cae", relation="Rel_Fa_Fuzaiyye", irab="Dynamic_Transition")
        
        # Nahiv Sağlık Taraması (İzolasyon)
        health_meta = self.nahiv_compiler.run_e2e_health_check(ast)
        isolated_phases = health_meta["isolated_phases"]
        
        # Pragmatik Meta Simülasyonu
        pragmatics_meta = {"is_valid": True, "type": "Khabari", "epistemic_modality": "Epistemic_Necessity"}
        
        # Cross-Layer Check
        with self.assertRaises(ValueError) as context:
            self.maani_analyzer.enforce_pragmatic_syntax_consistency(pragmatics_meta, isolated_phases)
            
        self.assertIn("[LOGIC_FAILURE_PROBABILITY: HIGH] Ontolojik Çelişki", str(context.exception))
        self.assertIn("Epistemic Collapse", str(context.exception))

    def test_context_poisoning_muktaza_el_hal(self):
        """
        .. mantik_kurali:: Bağlam Zehirlenmesi (Context Poisoning)
        Senaryo: Sâil'in (Muhatabın) zihni Khali_al_Zihn (Boş/Şüphesiz) iken, 
        Tevkid (Pekiştirme) edatı kullanılırsa, Z3 Kripke uzayında gereksiz bir 
        zorunluluk kısıtı (Combinatorial Load) yaratılır. Sistem bunu engellemelidir.
        """
        # Muhatap durumunu simüle et
        self.discourse.set_opponent_epistemic_state(DenialLevel.KHALI_AL_ZIHN)
        
        # Tevkid içeren bağımlılık listesi
        tokens = ["inna", "zeyden", "kaimun"]
        dependencies = [
            ("inna", "zeyden", "Amel_Inne_Ism", "Mansub"),
            ("inna", "kaimun", "Amel_Inne_Haber", "Marfu")
        ]
        
        # Pragmatik Analiz
        pragmatics_meta = self.maani_analyzer.analyze_pragmatics(tokens, dependencies)
        
        self.assertFalse(pragmatics_meta["is_valid"])
        self.assertEqual(pragmatics_meta["type"], "MAANI_VIOLATION")
        
        # Cross-Layer Enforcement 
        isolated_phases = {"PHASE_3_NECESSITY_SCOPE": [("inna", "zeyden", {"relation": "Amel_Inne_Ism"})]}
        
        with self.assertRaises(ValueError) as context:
            self.maani_analyzer.enforce_pragmatic_syntax_consistency(pragmatics_meta, isolated_phases)
            
        self.assertIn("Bağlam Zehirlenmesi", str(context.exception))

    def test_cyclic_dependency_dag_enforcement(self):
        """
        .. mantik_kurali:: Asiklik Bağımlılık Zorlayıcı (Acyclic Constraint)
        Senaryo: Sentaktik ağaçta (AST) yanlışlık veya Bedel/Rabıta çakışması 
        nedeniyle ontolojik bir döngü (Cycle) oluşursa, Z3 sonsuz yayılıma girer. 
        Topolojik sıralayıcı (DAG Enforcer) bunu tespit etmeli ve Hard Fail fırlatmalıdır.
        """
        ast = nx.DiGraph()
        # Döngü (Cycle) Yaratımı: A -> B -> C -> A
        ast.add_edge("Zeyd", "Akhuka", relation="Bedel_Identity")
        ast.add_edge("Akhuka", "Daribun", relation="Fail")
        ast.add_edge("Daribun", "Zeyd", relation="Rabita_Predication") 
        
        with self.assertRaises(ValueError) as context:
            self.nahiv_compiler.run_e2e_health_check(ast)
            
        self.assertIn("AST içerisinde ontolojik döngü", str(context.exception))
        self.assertIn("Cyclic Dependency", str(context.exception))

    def test_kasr_and_bedel_alias_warning(self):
        """
        .. felsefe_notu:: İşaretçi Eşitleme (Pointer Aliasing) Hiper-Kombinasyonu
        Senaryo: Cümlede hem Evrensel Dışlama (Kasr) hem de Ontolojik Kimlik 
        Eşitleme (Bedel) varsa, DiscourseRegister uyarılmalıdır. Aksi takdirde SMT, 
        bedel olan değişkeni evrensel kümeden yanlışlıkla dışlayabilir.
        """
        ast = nx.DiGraph()
        ast.add_edge("innema", "zeydun", relation="Kasr_Modifier")
        ast.add_edge("zeydun", "akhuka", relation="Bedel_Identity")
        
        isolated_phases = self.nahiv_compiler._isolate_smt_constraints(ast)
        
        # Simüle edilmiş bağımlılık listesi ve pragmatik analiz
        dependencies = [
            ("innema", "zeydun", "Kasr_Modifier", "Mevsuf_to_Sifat"),
            ("zeydun", "akhuka", "Bedel_Identity", "Tabi_Identity")
        ]
        pragmatics_meta = self.maani_analyzer.analyze_pragmatics(["innema", "zeydun", "akhuka"], dependencies)
        
        # SMT İzolasyon matrisleriyle pragmatiği birleştir
        self.maani_analyzer.enforce_pragmatic_syntax_consistency(pragmatics_meta, isolated_phases)
        
        # Uyarı enjekte edilmiş olmalı
        self.assertIn("alias_warning", pragmatics_meta)
        self.assertIn("[ADAB_WARNING] Kasr (Evrensel Dışlama) ve Bedel (Pointer Aliasing)", pragmatics_meta["alias_warning"])

if __name__ == '__main__':
    unittest.main()