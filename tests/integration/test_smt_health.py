import unittest
import networkx as nx
from typing import Dict, Any, List

from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.pragmatics import MaaniSpeechActAnalyzer
from linguistics.discourse_state import DiscourseRegister

"""
.. felsefe_notu:: Kripke Uzayı ve Varlığın Üç Boyutlu Sınaması (World, Time, Space)
    Kelam felsefesinde arazlar (nitelik, zaman, mekân) cevhere (entity) sonradan ilişir. 
    Z3 SMT çözücüsünde bu durum, EntitySort değişkenlerinin TimeSort, SpaceSort ve 
    WorldSort matrisleriyle sınırlandırılmasıdır (Skolemizasyon). Bu test paketi, 
    Nahiv derleyicisinden çıkan AST fazlarının (Phases), Kripke uzayında eşzamanlı bir 
    mutasyona (aynı anda hem mekân, hem zaman, hem kiplik değişimi) uğradığında 
    ontolojik tutarlılığını (Ontological Integrity) koruyup korumadığını denetler.
"""

class TestSmtKripkeHealth(unittest.TestCase):
    
    def setUp(self):
        """
        [FAZ 14 SMT HEALTH TEST SETUP]
        Z3 kısıt derleyicisini simüle etmek için temiz bir AST ve Compiler ortamı 
        hazırlanır.
        """
        self.discourse = DiscourseRegister()
        self.nahiv_compiler = NahivDependencyCompiler()

    def test_spatio_temporal_convergence(self):
        """
        .. mantik_kurali:: Zaman ve Mekân İctimaı (Spatio-Temporal Convergence)
        Senaryo: "Zeyd cuma günü (zaman) mescitte (mekân) ayaktaydı."
        SMT motorunun TimeSort ve SpaceSort kısıtlarını aynı fazda (PHASE_4) 
        yakalayıp yakalamadığının denetimi. Z3'te bu kısıtlar ardışık z3.And() 
        kapılarına dönüştürülecektir.
        """
        ast = nx.DiGraph()
        # Bağımlılıkların Graf'a eklenmesi
        ast.add_edge("kaimun", "yawmul_juma", relation="Rel_Zarf_Zaman", irab="Mansub")
        ast.add_edge("fi", "masjid", relation="Harf_Mecrur", irab="Majrur")
        ast.add_edge("kaimun", "fi", relation="Muteallak_Mekan", irab="Zarf_Lagv")
        
        health_meta = self.nahiv_compiler.run_e2e_health_check(ast)
        spatial_temporal_phase = health_meta["isolated_phases"]["PHASE_4_SPATIAL_TEMPORAL"]
        
        # Zaman ve Mekân kısıtlarının tek fazda (SMT için eşzamanlı) toplandığını doğrula
        relations = [data.get("relation") for u, v, data in spatial_temporal_phase]
        self.assertIn("Rel_Zarf_Zaman", relations, "Zaman kısıtı Phase 4'e aktarılamadı.")
        self.assertIn("Muteallak_Mekan", relations, "Mekan kısıtı Phase 4'e aktarılamadı.")

    def test_epistemic_world_vs_spatial_confinement(self):
        """
        .. felsefe_notu:: Tahkik ve Tahdîd (Epistemic World vs. Spatial Limits)
        Senaryo: "Muhakkak ki Zeyd (İnne - WorldSort Mutlakiyeti) evdedir (SpaceSort Tahdidi)."
        İnne'nin yarattığı evrensel zorunluluk (PHASE_3), mekânsal daralmadan (PHASE_4) 
        önce derlenmelidir. Aksi takdirde SMT motoru Zeyd'i sadece tek bir Kripke 
        mekânında (evde) var edip, diğer dünyalarda yok sayar (Ex Falso Quodlibet).
        """
        ast = nx.DiGraph()
        ast.add_edge("inna", "zeyden", relation="Amel_Inne_Ism", irab="Mansub")
        ast.add_edge("fi", "dar", relation="Harf_Mecrur", irab="Majrur")
        ast.add_edge("inna", "fi", relation="Amel_Inne_Haber", irab="Marfu_Mahallen")
        ast.add_edge("Kainun_Virtual", "fi", relation="Muteallak_Mekan", irab="Zarf_Mustakar")
        
        health_meta = self.nahiv_compiler.run_e2e_health_check(ast)
        
        phase_3 = health_meta["isolated_phases"]["PHASE_3_NECESSITY_SCOPE"]
        phase_4 = health_meta["isolated_phases"]["PHASE_4_SPATIAL_TEMPORAL"]
        
        self.assertTrue(len(phase_3) > 0, "İnne amel düğümü Phase 3'e aktarılamadı.")
        self.assertTrue(len(phase_4) > 0, "Mekan harf-i ceri Phase 4'e aktarılamadı.")
        
        # Topolojik sırada inna (kök) -> zeyden (yaprak) ilişkisinin çözümlenme sırası denetimi
        # Z3 değişken tanımlamaları yapraklardan köke doğru (Dependency-first) derlenir. 
        # 'zeyden' inna'dan önce gelmeli.
        order = health_meta["compilation_order"]
        self.assertTrue(order.index("zeyden") < order.index("inna"), 
                        "Z3 değişken derleme sırası ontolojik hiyerarşiye (Topological Sort) aykırı.")

    def test_zero_copula_virtual_space_allocation(self):
        """
        .. mantik_kurali:: Sıfır-Rabıta ve Sanal Mekân Ataması (Virtual Space Allocation)
        Senaryo: "Zeyd evdedir" cümlesinde fiil (amil) yoktur. Sistem görünmez 
        Kainun_Virtual (Oluş) düğümünü yaratıp, mekânı (SpaceSort) ona bağlamalıdır.
        Eğer bu bağ kurulmazsa, SMT çözücüsü Zeyd'i Kripke evreninde "askıda (floating)" 
        bırakır ve bellek taşmasına (Memory Leak / Infinite Search) neden olur.
        """
        ast = nx.DiGraph()
        ast.add_edge("Kainun_Virtual", "zeyd", relation="Rabita_Predication", irab="Marfu_Virtual")
        ast.add_edge("fi", "dar", relation="Harf_Mecrur", irab="Majrur")
        ast.add_edge("Kainun_Virtual", "fi", relation="Muteallak_Mekan", irab="Zarf_Mustakar")
        
        health_meta = self.nahiv_compiler.run_e2e_health_check(ast)
        
        # PHASE_2'de Rabita'nın, PHASE_4'te Mekanın çözülmesi gerekir
        phase_2 = health_meta["isolated_phases"]["PHASE_2_IDENTITY_ALIAS"]
        phase_4 = health_meta["isolated_phases"]["PHASE_4_SPATIAL_TEMPORAL"]
        
        phase_2_rels = [data.get("relation") for u, v, data in phase_2]
        phase_4_rels = [data.get("relation") for u, v, data in phase_4]
        
        self.assertIn("Rabita_Predication", phase_2_rels, "Sıfır-Rabıta düğümü Identity fazında çözülemedi.")
        self.assertIn("Muteallak_Mekan", phase_4_rels, "Sanal amilin mekan bağı Temporal fazda çözülemedi.")

if __name__ == '__main__':
    unittest.main()