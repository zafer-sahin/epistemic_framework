import pytest
import networkx as nx
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.sarf_parser import MorphologicalAnalysis

"""
.. felsefe_notu:: Literate Testing ve İlm-i Nahiv'in Matematiksel İspatı
    İbn el-Hâcib'in Kafiye'sinde ve İbn Mâlik'in Elfiye'sinde vaz edilen Amil-Mamul ilişkileri, 
    Z3 SMT motorunda katı 'First-Order Logic' (FOL) yüklemlerine (Predicates) dönüşür. 
    Bu test modülü;
    1. İslâm felsefesinde reddedilen 'Devir' (Döngüsel Nedensellik) safsatasının DAG algoritmasıyla 
       (Directed Acyclic Graph) engellendiğini,
    2. 'İnne' edatının sıradan bir söz edimi değil, Modal Mantıktaki 'Epistemik Zorunluluk' 
       (Necessity: $\square$) olduğunu,
    3. 'Fâ-i Füzâiyye'nin zamanı bükerek 'Dinamik Durum Geçişi' (Dynamic State Transition) 
       yarattığını matematiksel teorem ispatları (Proof of Concept) şeklinde doğrular.
"""

class TestNahivASTAndOntology:

    def setup_method(self):
        """
        Her test öncesi Kripke uzayına (Z3) hazırlık yapan sentaktik derleyici (Nahiv) sıfırlanır.
        """
        self.compiler = NahivDependencyCompiler()
        
        # Testlerde kullanılacak donanımsal ontolojik mühürleri (Lexicon) simüle ediyoruz.
        self.mock_lexicon = {
            "inna": MorphologicalAnalysis(original_word="inna", root="inna", pattern="Harf_Inne", ontologic_type="Harf_Inne"),
            "zeydan": MorphologicalAnalysis(original_word="zeydan", root="zeyd", pattern="Alem/Camid_Munevven", ontologic_type="Ism", irab="Mansub", gender="Muzekker", number="Mufred", thematic_role="Entity"),
            "kaimun": MorphologicalAnalysis(original_word="kaimun", root="kym", pattern="Fâ'ilun", ontologic_type="Ism", irab="Marfu", gender="Muzekker", number="Mufred", thematic_role="Agent"),
            "daraba": MorphologicalAnalysis(original_word="daraba", root="drb", pattern="Fa'ala", ontologic_type="Fiil", hidden_pronoun="Huve"),
            "fa": MorphologicalAnalysis(original_word="fa", root="fa", pattern="Harf", ontologic_type="Harf"),
            "amrun": MorphologicalAnalysis(original_word="amrun", root="amr", pattern="Alem/Camid_Munevven", ontologic_type="Ism", irab="Marfu", gender="Muzekker", number="Mufred"),
            "fi": MorphologicalAnalysis(original_word="fi", root="fi", pattern="Harf", ontologic_type="Harf"),
            "beytin": MorphologicalAnalysis(original_word="beytin", root="beyt", pattern="Alem/Camid_Munevven", ontologic_type="Ism", irab="Majrur", thematic_role="Entity")
        }

    def test_epistemic_necessity_of_inne(self):
        """
        .. mantik_kurali:: Tahkik ve Modal Zorunluluk (Epistemic Necessity)
        "İnne zeyden kaimun" (Şüphesiz Zeyd ayaktadır) önermesinde İnne, 
        Zeyd ile Ayakta Olmak arasındaki bağı sıradan bir varoluştan (Exists), 
        Kripke uzayında mutlak bir zorunluluğa (ForAll: Bütün mümkün dünyalarda geçerlidir) çevirir.
        Test, AST düğümlerine 'ModalNecessity' Z3 haritalamasının işlendiğini ispatlar.
        """
        tokens = ["inna", "zeydan", "kaimun"]
        dependencies = self.compiler.suggest_dependencies(tokens, self.mock_lexicon)
        ast = self.compiler.build_ast(tokens, dependencies, self.mock_lexicon)
        
        # 'inna' düğümünün AST'de EpistemicOperatorNode olarak türediği kanıtlanmalıdır.
        assert ast.nodes["inna"]["ast_node_class"] == "EpistemicOperatorNode"
        
        # İnne'nin Zeyd'i (İsmini) ve Kaim'i (Haberini) ontolojik olarak zorunlu kıldığı ispatlanır.
        inne_ism_edge = ast.edges["inna", "zeydan"]
        inne_haber_edge = ast.edges["inna", "kaimun"]
        
        assert inne_ism_edge["relation"] == "Amel_Inne_Ism"
        assert inne_ism_edge["z3_mapping"] == "ModalNecessity"
        
        assert inne_haber_edge["relation"] == "Amel_Inne_Haber"
        assert inne_haber_edge["z3_mapping"] == "ModalNecessity"

    def test_dynamic_state_transition_fuzaiyye(self):
        """
        .. pedagojik_anlati:: Fâ-i Füzâiyye ve Dinamik Mantık (Dynamic Logic)
        "Daraba zeydun fa amrun" (Zeyd vurdu, derken aniden Amr [belirdi/vurdu]).
        Buradaki 'fa', statik bir 've' bağlacı değil, Kripke uzayında $W_t \implies W_{t+1}$ 
        sırtlamasını tetikleyen bir zaman ve durum bükücüdür (Dynamic Transition).
        Test, sentaktik derleyicinin bu felsefi sıçramayı otonom tespit ettiğini doğrular.
        """
        tokens = ["daraba", "zeydan", "fa", "amrun"]
        dependencies = self.compiler.suggest_dependencies(tokens, self.mock_lexicon)
        ast = self.compiler.build_ast(tokens, dependencies, self.mock_lexicon)
        
        # 'zeydan' ve 'amrun' arasında 'fa' üzerinden bir dinamik geçiş kenarı bulunmalıdır.
        fa_edge = ast.edges["zeydan", "amrun"]
        assert fa_edge["relation"] == "Rel_Fa_Fuzaiyye"
        assert fa_edge["z3_mapping"] == "DynamicStateTransition"

    def test_spatial_muteallak_constraint(self):
        """
        .. mantik_kurali:: Uzaysal Bağımlılık (SpaceSort) ve Zarf-ı Lağv
        "Daraba zeydun fi beytin" (Zeyd evde vurdu).
        Harf-i cerler (fi), ontolojik olarak askıda kalamaz. Eylemin üzerine 
        SpaceSort (Uzay Boyutu) kısıtı olarak bağlanmak (Müteallak) zorundadır.
        FOL Karşılığı: LocatedIn(Daraba_Event, Beyt, World).
        """
        tokens = ["daraba", "zeydan", "fi", "beytin"]
        dependencies = self.compiler.suggest_dependencies(tokens, self.mock_lexicon)
        ast = self.compiler.build_ast(tokens, dependencies, self.mock_lexicon)
        
        # 'fi' edatının 'daraba' eylemine Muteallak (Bağlantı) olarak mühürlendiği ispatlanır.
        muteallak_edge = ast.edges["daraba", "fi"]
        assert muteallak_edge["relation"] == "Muteallak_Mekan"
        assert muteallak_edge["z3_mapping"] == "SpaceSortConstraint"
        
        # Mecruriyet ispatı
        mecrur_edge = ast.edges["fi", "beytin"]
        assert mecrur_edge["relation"] == "Harf_Mecrur"

    def test_dag_enforcement_and_cycle_rejection(self):
        """
        .. felsefe_notu:: 'Devir' Safsatasının Engellenmesi (Ex Falso Quodlibet)
        İslâm kelâmında A'nın B'yi, B'nin de A'yı var etmesi (Devir) ontolojik bir imkânsızlıktır.
        SMT matrislerinde bu durum sonsuz döngüye (Combinatorial Explosion) yol açar.
        Test, AST'ye suni bir döngü enjekte edildiğinde sistemin "LOGIC_FAILURE_PROBABILITY: HIGH" 
        ile işlemi kilitlediğini matematiksel olarak doğrular.
        """
        # Sahte ve döngüsel bir AST (A -> B, B -> A) inşa ediliyor
        cyclic_ast = nx.DiGraph()
        cyclic_ast.add_node("Zeyd")
        cyclic_ast.add_node("Amr")
        cyclic_ast.add_edge("Zeyd", "Amr", relation="Sifat_Mevsuf")
        cyclic_ast.add_edge("Amr", "Zeyd", relation="Bedel_Identity")
        
        with pytest.raises(ValueError) as exc_info:
            self.compiler.run_e2e_health_check(cyclic_ast)
            
        # Hatada ontolojik döngü uyarısının bulunduğu ispatlanmalıdır
        assert "LOGIC_FAILURE_PROBABILITY: HIGH" in str(exc_info.value)
        assert "Cyclic Dependency" in str(exc_info.value)

    def test_zero_copula_injection(self):
        """
        .. pedagojik_anlati:: Görünmez Yüklem (Kadiyye-i Hamliyye Rabıtası)
        Arapça isim cümlelerinde 'dır/dir' (Copula) görünmezdir. SMT motoru için bu 
        ontolojik bir kopukluk demektir. Test, "Zeyd Kaimun" (Zeyd ayaktadır) cümlesinde 
        derleyicinin araya sanal bir 'Rabita_Virtual' (Kainun_Virtual) düğümü zerk ederek 
        ilişkiyi onardığını ispatlar.
        """
        # Fiil olmayan, sadece mübteda ve haberden oluşan bir dizi
        tokens = ["zeydan", "kaimun"] 
        dependencies = self.compiler.suggest_dependencies(tokens, self.mock_lexicon)
        ast = self.compiler.build_ast(tokens, dependencies, self.mock_lexicon)
        
        # Sanal Rabıta düğümünün AST'ye ZeroCopulaNode olarak eklendiği doğrulanmalıdır
        assert "Rabita_Virtual" in ast.nodes
        assert ast.nodes["Rabita_Virtual"]["ast_node_class"] == "ZeroCopulaNode"
        
        # Eşdeğerlik veya Predication kısıtlarının kurulduğu ispatlanır
        predication_edge = ast.edges["kaimun", "zeydan"]
        assert predication_edge["relation"] == "Rabita_Predication"
        assert predication_edge["z3_mapping"] == "SetInclusion"