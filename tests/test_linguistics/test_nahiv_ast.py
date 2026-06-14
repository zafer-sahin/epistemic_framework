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
       yarattığını,
    4. [FAZ 2 ENTEGRASYONU]: Edilgen eylemlerde (Mebnî lil-Meçhul) failsiz eylem safsatasını 
       önlemek üzere ontolojik sanal failin (Unknown_Agent_Virtual) grafiğe zerk edildiğini 
       matematiksel teorem ispatları (Proof of Concept) şeklinde doğrular.
    5. [FAZ 3 ENTEGRASYONU]: İsm-i Mevsûl (Sıla) ve Cümle-i Fiiliye Haber matrislerinin
       Kripke uzayında deterministik alt-kapsüller (SubClause/PointerAlias) ürettiğini kanıtlar.
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
            "duriba": MorphologicalAnalysis(original_word="duriba", root="drb", pattern="Fu'ila", ontologic_type="Fiil", voice="Passive", hidden_pronoun="Huve"),
            "fa": MorphologicalAnalysis(original_word="fa", root="fa", pattern="Harf", ontologic_type="Harf"),
            "amrun": MorphologicalAnalysis(original_word="amrun", root="amr", pattern="Alem/Camid_Munevven", ontologic_type="Ism", irab="Marfu", gender="Muzekker", number="Mufred"),
            "fi": MorphologicalAnalysis(original_word="fi", root="fi", pattern="Harf", ontologic_type="Harf"),
            "beytin": MorphologicalAnalysis(original_word="beytin", root="beyt", pattern="Alem/Camid_Munevven", ontologic_type="Ism", irab="Majrur", thematic_role="Entity"),
            "daima": MorphologicalAnalysis(original_word="daima", root="daim", pattern="Zarf", ontologic_type="Harf"),
            "in": MorphologicalAnalysis(original_word="in", root="in", pattern="Harf_Shart", ontologic_type="Harf"),
            # FAZ 3 Test Verileri: İsm-i Mevsûl ve Geniş Zaman Fiili
            "ellezi": MorphologicalAnalysis(original_word="ellezi", root="ellezi", pattern="Ism_Mevsul", ontologic_type="Ism_Mevsul", is_definite=True),
            "yansuru": MorphologicalAnalysis(original_word="yansuru", root="nsr", pattern="Yaf'ulu", ontologic_type="Fiil", hidden_pronoun="Huve")
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

    def test_shamsiyye_modalities_and_luzumi_shart(self):
        """
        [FAZ 2 ENTEGRASYONU]: Şemsiyye Kiplikleri ve Lüzumî Şart İspatı
        'Dâimâ' gibi kelimelerin Zâtî zorunluluğa, 'İn' gibi şartların Modus Ponens'e 
        (Strict Implication) çevrilerek Kripke uzayına mühürlenmesi doğrulanır.
        """
        # 1. Daime-i Mutlaka Modalitesi
        tokens_modal = ["daima", "zeydan", "kaimun"]
        deps_modal = self.compiler.suggest_dependencies(tokens_modal, self.mock_lexicon)
        ast_modal = self.compiler.build_ast(tokens_modal, deps_modal, self.mock_lexicon)
        
        assert "ModalOperatorNode" == ast_modal.nodes["daima"]["ast_node_class"]
        assert ast_modal.edges["daima", "zeydan"]["z3_mapping"] == "Modal_Daime_i_Mutlaka"

        # 2. Şart-ı Lüzumî (Katı Nedensellik / Modus Ponens)
        tokens_shart = ["in", "daraba", "zeydan", "fa", "amrun"]
        deps_shart = self.compiler.suggest_dependencies(tokens_shart, self.mock_lexicon)
        ast_shart = self.compiler.build_ast(tokens_shart, deps_shart, self.mock_lexicon)
        
        assert "EpistemicOperatorNode" == ast_shart.nodes["in"]["ast_node_class"]
        assert ast_shart.edges["in", "daraba"]["z3_mapping"] == "StrictImplication_Luzumi"
        
        # Şart cümlesinde gelen 'fa' artık Füzâiyye değil, Sebebiyye'dir (A -> B Lüzum bağı)
        assert ast_shart.edges["daraba", "amrun"]["z3_mapping"] == "DynamicStateTransition" # Rel_Fa_Sebebiyye (Modus Ponens Chain)
        
    def test_mebni_lil_mechul_naib_fail_and_virtual_agent(self):
        """
        .. mantik_kurali:: Mebnî lil-Meçhul ve Ontolojik Fail Gizlenmesi (Naib Fâil)
        [FAZ 2 ENTEGRASYONU]: "Duriba amrun" (Amr vuruldu) önermesinde eylemi yapan (Fail) 
        formel olarak gizlenmiştir. Kelâmî nedensellik (İlliyet) aksiyomu gereği failsiz 
        eylem olamayacağı için, SMT uzayına `Unknown_Agent_Virtual` zerk edilir ve merfu 
        öge (Amr) `Role_Patient` izdüşümü alacak şekilde `Naib_Fail` ilişkisiyle bağlanır.
        """
        tokens = ["duriba", "amrun"]
        dependencies = self.compiler.suggest_dependencies(tokens, self.mock_lexicon)
        ast = self.compiler.build_ast(tokens, dependencies, self.mock_lexicon)
        
        # Amr'ın (merfu isim) Naib_Fail olarak raptedildiği ispatlanmalıdır.
        naib_fail_edge = ast.edges["duriba", "amrun"]
        assert naib_fail_edge["relation"] == "Naib_Fail"
        assert naib_fail_edge["irab"] == "Marfu"
        
        # Failsiz eylem paradoksunun sanal aktör ile (Unknown_Agent_Virtual) kapatıldığı ispatlanmalıdır.
        assert "Unknown_Agent_Virtual" in ast.nodes
        virtual_agent_edge = ast.edges["duriba", "Unknown_Agent_Virtual"]
        assert virtual_agent_edge["relation"] == "Fail"
        assert virtual_agent_edge["irab"] == "Marfu_Virtual"
        assert ast.nodes["Unknown_Agent_Virtual"]["ast_node_class"] == "DRT_ExistentialNode"

    def test_ism_mevsul_and_sila_subclause(self):
        """
        .. mantik_kurali:: İsm-i Mevsûl ve Sıla Cümlesi (Lambda Soyutlaması)
        [FAZ 3 ENTEGRASYONU]: "Zeydan ellezi daraba" (O Zeyd ki vurdu).
        Arapçada 'Ellezî' (Mevsûl) sıradan bir varlık değil, Z3 Kripke uzayında Lambda 
        ($\lambda x. \Phi(x)$) işlevi gören bir işaretçidir. Test, Mevsûl'den fiile 
        'Rel_Sila' bağının çekildiğini ve sanal Âid zamirinin Pointer Aliasing 
        (Hafıza eşitlemesi) için otonom olarak üretildiğini ispatlar.
        """
        tokens = ["zeydan", "ellezi", "daraba"]
        dependencies = self.compiler.suggest_dependencies(tokens, self.mock_lexicon)
        ast = self.compiler.build_ast(tokens, dependencies, self.mock_lexicon)
        
        # Ellezi düğümünün LambdaAbstractionNode olarak işaretlendiğini doğrula
        assert ast.nodes["ellezi"]["ast_node_class"] == "LambdaAbstractionNode"
        
        # Sıla bağının SubClausePredicate olarak mühürlendiğini doğrula
        sila_edge = ast.edges["ellezi", "daraba"]
        assert sila_edge["relation"] == "Rel_Sila"
        assert sila_edge["z3_mapping"] == "SubClausePredicate"
        
        # Âid zamirinin sanal olarak türetilip Pointer Alias yapıldığını doğrula
        assert "daraba_Aid_Virtual" in ast.nodes
        aid_edge = ast.edges["ellezi", "daraba_Aid_Virtual"]
        assert aid_edge["relation"] == "Rel_Aid"
        assert aid_edge["z3_mapping"] == "PointerAlias"

    def test_cumle_i_fiiliye_haber_and_action_rabita(self):
        """
        .. pedagojik_anlati:: Cümle-i Fiiliye Haber
        [FAZ 3 ENTEGRASYONU]: "Zeydan yansuru" (Zeyd yardım eder).
        Mübteda (Zeyd) ile Haber olan Fiil (Yansuru) arasındaki bağın sıradan bir 
        özellik aidiyeti (Predication) değil, doğrudan aksiyon yüklemi (Rabita_Cümle_Fiiliye)
        olarak Kripke uzayına (SubClausePredicate) yansıdığını ispatlar.
        """
        tokens = ["zeydan", "yansuru"]
        dependencies = self.compiler.suggest_dependencies(tokens, self.mock_lexicon)
        ast = self.compiler.build_ast(tokens, dependencies, self.mock_lexicon)
        
        # Mübteda ile Cümle-i Fiiliye haberi bağlandığını doğrula
        action_edge = ast.edges["yansuru", "zeydan"]
        assert action_edge["relation"] == "Rabita_Cümle_Fiiliye"
        assert action_edge["z3_mapping"] == "SubClausePredicate"