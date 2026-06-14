import networkx as nx
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum
from linguistics.sarf_parser import MorphologicalAnalysis

"""
.. felsefe_notu:: İlm-i Nahiv ve Dilin Ontolojik Mimarisi (Kafiye ve Molla Cami Perspektifi)
    Klasik İslâm gramerinde (Dars-i Nizâmî müfredatı) kelimeler zihinde veya metinde 
    başıboş (bağımsız) dolaşamazlar. İbn el-Hacib'in 'Kafiye' eserinde ve İbn Malik'in 
    'Elfiye'sinde mutlaklaştırıldığı üzere, her cümle bir "Amil" (etken/yöneten) ve "Mamul" 
    (edilgen/yönetilen) ağıdır. Bu yapı, Aristotelesçi "Muharrik" (Hareket Ettirici) ve 
    "Müteharrik" (Hareket Eden) felsefesinin ve kelâmî nedensellik (İlliyet) ilkesinin 
    doğrudan dilbilimsel izdüşümüdür.
    
    Bu modül, ardışık doğal dil dizgilerini Z3 SMT çözücüsünün Kripke uzayında işleyebileceği 
    Hiyerarşik Bağımlılık Ağaçlarına (Directed Graph - AST) çevirerek, cümlenin mantıksal 
    anatomisini çıkarır.
"""

class NahivDependencyCompiler:
    """
    .. pedagojik_anlati:: Sentaktik Derleyici (Amil-Mamul Orkestrasyonu)
    Bu sınıf, kelimelerin i'rab (son hareke) durumlarına ve ontolojik tiplerine bakarak, 
    onların Kripke uzayında birbirlerine nasıl bağlanacağını (Dependency) tespit eder. 
    Geleneksel bilgisayar bilimlerindeki AST (Abstract Syntax Tree) mantığının aksine, 
    buradaki her düğüm (node) bir varlığı (Entity/World), her kenar (edge) ise 
    ontolojik bir kısıtı (Constraint/Relation) temsil eder.
    
    [FAZ 5 - LITERATE CHUNKING]: Bilişsel Yükü (Cognitive Load) asgari seviyede tutmak ve 
    "Hesaplanabilir Gramer Kitabı" vizyonunu gerçekleştirmek için, karmaşık çözümleme 
    algoritması hiyerarşik alt fonksiyonlara (Private Methods) yalıtılmıştır. 
    
    [FAZ 1 ENTEGRASYONU]: Tüm yüzeysel .endswith() metotları silinmiş, yerine 
    SarfEngine'den beslenen Tip-Güvenli (Type-safe) HPSG Feature Matrisleri (Irab, Number, Gender) 
    entegre edilmiştir. Bu, Kırık Çoğullar (Cemi Mükesser) ve İ'rab bi-l-Huruf vakalarında 
    Z3 kilitlenmelerini kökünden engeller.
    
    [FAZ 3 ENTEGRASYONU]: İsm-i Mevsûl (Sıla Cümleleri), Şibh-i Cümle Haberleri ve 
    Cümle-i Fiiliye Haberleri, karmaşık yönlü asiklik çizge (DAG) topolojisinde alt-kısıtlar 
    (Sub-graph Constraints) olarak bağlanmıştır.

    [FAZ 4 ENTEGRASYONU]: Bağlamsal Belirlilik (Contextual Definiteness) özyinelemesi ve
    Hâl (Araz) / Temyiz (Zâtî Netlik) ayrımları ontolojik kalıp üzerinden ayrıştırılmıştır.
    """
    def __init__(self):
        self.definite_article = ("al_", "el_") 
        self.dependency_graph = nx.DiGraph()
        
        # .. mantik_kurali:: Şemsiyye Kiplikleri (Temporal ve Modal Triggers)
        self.temporal_triggers = ["Rel_Hal", "Rel_Zarf_Zaman", "Rel_Shart", "Rel_Shart_Luzumi"]
        
        # Kadiyye-i Şartiyye (Hipotetik Önerme) için Fasıl (Ayrılma) ve Vasıl (Birleşme)
        self.atif_particles = ["wa", "fa", "aw", "summe", "am", "bal", "la", "lakin"]
        
        # [FAZ 2 ENTEGRASYONU]: Necmeddin el-Kâtibî Şemsiyye Mantığı Kısıt Edatları 
        self.shart_luzumi = ["in", "iza", "law", "amma"] # Katı Zorunluluk / Modus Ponens
        self.munfasila_inadi = ["imma", "aw"] # Katı Ayrıklık / XOR (Hakikiyye/Mâniatü'l-Cem'/Hulüvv)
        
        # [FAZ 2 ENTEGRASYONU]: Şemsiyye Yüzey Kiplikleri (Surface Modalities)
        self.modal_adverbs = {
            "daima": "Daime_i_Mutlaka",         # Zamanın tamamında zorunluluk (De re)
            "qat'an": "Zaruriyye_i_Mutlaka",      # Mutlak zâtî zorunluluk
            "zaruretan": "Zaruriyye_i_Mutlaka",   # Mutlak zâtî zorunluluk
            "rubbema": "Mumkine_i_Amme",          # Olasılık uzayında mevcudiyet
            "qad": "Mumkine_i_Amme",              # Olasılık uzayında mevcudiyet
            "abadan": "Daime_i_Mutlaka",          # Sonsuz zaman uzayında zorunluluk
            "muhalan": "Mustahil"                 # Kripke dünyalarında erişilemezlik (UNSAT)
        }
        
        # .. felsefe_notu:: Uzaysal/Bağıntısal Kısıtlar (SpaceSort Operators)
        # Harf-i cerler (Prepositions) basit bağlaçlar değildir. Varlığın (Entity) 
        # Kripke dünyasında (WorldSort) hangi uzaysal düzleme yerleştiğini tayin ederler.
        self.harf_i_cerler = {
            "fi": "Zarfiyye",           # İçindelik kısıtı (Inclusion)
            "ala": "Isti_la",           # Üzerindelik kısıtı (Superiority)
            "min": "Ibtida_i_Gaye",     # Başlangıç noktası (Origin)
            "ila": "Intiha_i_Gaye",     # Bitiş/Gaye noktası (Destination)
            "bi": "Ilsak_Alet",         # Bitişiklik veya araçsallık (Instrumental)
            "li": "Ihtisas_Mulk",       # Aidiyet/Mülkiyet bağıntısı (Possession)
            "inde": "Zarfiyye",
            "tahta": "Zarfiyye",
            "fawqa": "Zarfiyye",
            "beyne": "Zarfiyye",
            "khalf": "Zarfiyye",
            "amam": "Zarfiyye",
            "an": "Mucaveze"            # Uzaklaşma/Aşma kısıtı (Transcendence)
        }

    def _get_irab_val(self, morph: MorphologicalAnalysis) -> str:
        """HPSG matrisinden irab değerini güvenli şekilde çeker."""
        if not morph.hpsg or not morph.hpsg.irab:
            return "Unknown"
        if isinstance(morph.hpsg.irab, Enum):
            return morph.hpsg.irab.value
        return str(morph.hpsg.irab)

    def _get_gender_val(self, morph: MorphologicalAnalysis) -> str:
        if not morph.hpsg or not morph.hpsg.gender: return "Unknown"
        return morph.hpsg.gender.value if isinstance(morph.hpsg.gender, Enum) else str(morph.hpsg.gender)

    def _get_number_val(self, morph: MorphologicalAnalysis) -> str:
        if not morph.hpsg or not morph.hpsg.number: return "Unknown"
        return morph.hpsg.number.value if isinstance(morph.hpsg.number, Enum) else str(morph.hpsg.number)

    def _is_definite(self, token: str, lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]], visited: Optional[set] = None) -> bool:
        """
        .. mantik_kurali:: Ma'rife ve Nekra (Belirlilik ve Belirsizlik)
        Bir varlığın 'al-' takısı alması, onun evrensel kümeden (Universal Set) çekilip, 
        dış dünyada aktüelleşmiş spesifik bir varlığa (Instantiated Entity) dönüşmesidir.
        
        $$\exists x \in \text{World}: P(x) \land \forall y (P(y) \implies x = y)$$
        Bu durum Z3 SMT'de Skolemizasyon sürecini doğrudan etkiler; nekra lafızlar varoluşsal 
        (Exists), ma'rife lafızlar ise spesifik sabitler (Constants) olarak derlenir.

        [FAZ 1 - BAĞLAMSAL KISIT]: Yalnızca 'al-' takısına bakılmaz. "Marifeye muzaf olan 
        nekra da marife olur" kuralı gereği, AST üzerindeki İzafet zincirleri (Mudaf_MudafIlayh) 
        özyineli (recursive) olarak taranır. Bu, teolojik metinlerdeki ardışık tamlamalarda 
        oluşabilecek Exists/Constant Z3 uyuşmazlığını (Misquantification) çözer.
        
        [FAZ 4 ENTEGRASYONU]: İzafet zincirinin derinlik sınırı kaldırılarak tam DAG taraması 
        haline getirilmiştir.
        """
        if visited is None: 
            visited = set()
        if token in visited: 
            return False
        visited.add(token)

        morph = lexicon.get(token)
        
        # 1. Saf (Lafzî) Belirlilik
        if morph and getattr(morph.hpsg, 'is_definite', False):
            return True
        if morph and getattr(morph, 'pattern', '') == "Ism_Isaret":
            return True
        if morph and getattr(morph, 'pattern', '') == "Ism_Mevsul":
            return True
        if token.lower() in ["huve", "hiye", "huma", "hum", "hunne", "ente", "enti", "entuma", "entum", "entunne", "ene", "nahnu", "ellezi", "elleti", "ellezine", "men", "ma"]:
            return True

        # 2. İzafet (Bağlamsal) Zincirlemesi (Recursive DAG Traversal)
        for amil, mamul, rel, _ in dependencies:
            if amil == token and rel == 'Mudaf_MudafIlayh':
                # Eğer Muzafun İleyh marife ise, Muzaf da marife statüsü kazanır.
                if self._is_definite(mamul, lexicon, dependencies, visited):
                    return True
                    
        return False

    def _identify_primary_governors(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis]) -> Tuple[Optional[str], int, Optional[str], int]:
        """
        .. felsefe_notu:: Amil-i Kıyâsî ve Amil-i Semâî'nin Tespiti (Avamil-i Mi'e)
        Kripke uzayının sınırlarını çizen temel yöneticileri (Governors) arar. 
        'Fiil', yapısal bir amildir (Amil-i Kıyâsî) ve cümleye ontolojik hareket/oluş katar. 
        'İnne' ise duyuma/nakle dayalı bir amildir (Amil-i Semâî) ve cümlenin epistemolojik 
        kesinliğini Modal Mantıktaki Zorunluluk Operatörü ($\square P$) ile mühürler. 
        Tüm SMT AST yapısı bu iki ana kolon üzerine bina edilir.
        """
        amil_token = None
        amil_index = -1
        inne_token = None
        inne_index = -1
        
        for idx, token in enumerate(tokens):
            morph = lexicon.get(token)
            if morph:
                o_type = getattr(morph, 'ontologic_type', '')
                if morph.hpsg and morph.hpsg.ontologic_type:
                    o_type = morph.hpsg.ontologic_type.value if isinstance(morph.hpsg.ontologic_type, Enum) else str(morph.hpsg.ontologic_type)
                
                if o_type == "Fiil":
                    amil_token = token
                    amil_index = idx
                elif o_type == "Harf_Inne":
                    inne_token = token
                    inne_index = idx
        return amil_token, amil_index, inne_token, inne_index

    def _apply_pragmatic_modifiers(self, t1: str, t2: str, m1: Optional[MorphologicalAnalysis], amil_index: int, idx: int, dependencies: List[Tuple[str, str, str, str]]) -> bool:
        """
        .. pedagojik_anlati:: Muktazâ el-Hâl, Tevkîd ve Kasr (İlm-i Ma'ânî)
            Sa'deddin et-Taftazânî'nin 'Mutavvel'inde detaylandırdığı üzere; 'Tevkîd' (Pekiştirme), 
            muhatabın (Sâil'in) şüphesini gidermek için önermeyi Modal Mantık'ta 
            'Zorunlu' (Necessity: $\square P$) statüsüne yükseltir.
            
            'Kasr' ise niteliği bir varlığa hapsetme işlemidir; 
            $$\forall x (\text{Sifat}(x) \iff \text{Mevsuf}(x))$$ 
            şeklindeki mantıksal çift yönlü gerektirmeyi (Biconditional) Z3'e mühürler.
        """
        if not m1: return False
        
        o_type = getattr(m1, 'ontologic_type', '')
        if m1.hpsg and m1.hpsg.ontologic_type:
            o_type = m1.hpsg.ontologic_type.value if isinstance(m1.hpsg.ontologic_type, Enum) else str(m1.hpsg.ontologic_type)

        if o_type == "Harf_Tevkid":
            dependencies.append((t2, t1, 'Tevkid_Modifier', 'None'))
            return True
            
        if o_type == "Harf_Kasr":
            kasr_direction = 'Mevsuf_to_Sifat'
            if t1.lower() == "innema":
                if amil_index != -1 and idx < amil_index:
                    kasr_direction = 'Sifat_to_Mevsuf'
                else:
                    kasr_direction = 'Mevsuf_to_Sifat'
            elif t1.lower() == "illa":
                    kasr_direction = 'Sifat_to_Mevsuf'

            dependencies.append((t2, t1, 'Kasr_Modifier', kasr_direction))
            return True
            
        return False

    def _apply_dynamic_transitions(self, t1: str, t2: str, tokens: List[str], idx: int, dependencies: List[Tuple[str, str, str, str]]) -> bool:
        """
        .. pedagojik_anlati:: Fâ-i Füzâiyye ve Dinamik Mantık (Dynamic Logic)
            Klasik statik mantıkta (FOL) 'Fâ-i Füzâiyye' ve 'Sebebiyye'nin (nedensellik fâ'sı) 
            karşılığı yoktur, zira bunlar zaman/durum sıçramalarını (State Transition) ifade eder. 
            Bir eylemin (A) aniden diğerini (B) var etmesi, SMT'de ardışık Kripke dünyalarının 
            ($W_t \implies W_{t+1}$) yaratılmasını zorunlu kılar.
        """
        if t1.lower() in self.atif_particles:
            if idx > 0:
                t_prev = tokens[idx-1]
                if t1.lower() == "fa":
                    shart_exists = any(t.lower() in self.shart_luzumi for t in tokens[:idx])
                    if shart_exists:
                        # Modus Ponens zinciri (A -> B)
                        dependencies.append((t_prev, t2, 'Rel_Fa_Sebebiyye', 'Luzumi_Muttasila'))
                    else:
                        # Beklenmedik Ontolojik Sıçrama
                        dependencies.append((t_prev, t2, 'Rel_Fa_Fuzaiyye', 'Dynamic_Transition'))
                else:
                    dependencies.append((t_prev, t2, 'Rel_Atif', t1.lower()))
            return True
        return False

    def _apply_spatial_mutaallak(self, t1: str, t2: str, tokens: List[str], idx: int, lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]]) -> bool:
        """
        .. pedagojik_anlati:: Müteallak Prensibi ve Kripke Uzay Sabitlemesi
            Harf-i Cerler ontolojik olarak askıda var olamazlar. SMT evreninde, eylemin (Amil) 
            veya zımnî bir mevcudiyetin (Kainun_Virtual) üzerine bir uzaysal boyut (SpaceSort) 
            olarak bağlanmak (Müteallak) zorundadırlar. 
            
            Matematiksel karşılığı:
            $$\forall w, t, x, l: (\text{Entity}(x) \land \text{Location}(l) \land \text{Rel\_Fi}(x, l)) \implies \text{LocatedIn}(x, l, w, t)$$
        """
        if t1.lower() in self.harf_i_cerler:
            sem_type = self.harf_i_cerler[t1.lower()]
            rel_name = 'Muteallak_Mekan' if sem_type in ["Zarfiyye", "Isti_la"] else 'Muteallak_Harf'

            m2 = lexicon.get(t2)
            # Gayri Munsarif (Diptotes) bükün kuralı: Cer durumunda fetha alması (Semantic Shift koruması)
            if m2 and getattr(m2.hpsg, 'is_diptote', False):
                dependencies.append((t1, t2, 'Mecrur_Diptote_Override', 'Majrur'))
            else:
                dependencies.append((t1, t2, 'Harf_Mecrur', 'Majrur'))
            
            potential_amils = []
            for prev_idx in range(idx - 1, -1, -1):
                prev_token = tokens[prev_idx]
                prev_morph = lexicon.get(prev_token)
                if prev_morph:
                    o_type = getattr(prev_morph, 'ontologic_type', '')
                    if prev_morph.hpsg and prev_morph.hpsg.ontologic_type:
                        o_type = prev_morph.hpsg.ontologic_type.value if isinstance(prev_morph.hpsg.ontologic_type, Enum) else str(prev_morph.hpsg.ontologic_type)

                    if o_type == "Fiil":
                        potential_amils.append(prev_token)
                        break
                    elif o_type == "Ism" and getattr(prev_morph, 'thematic_role', '') in ["Agent", "Patient", "Action"]:
                        potential_amils.append(prev_token)
                        break

            closest_amil = potential_amils[0] if potential_amils else None

            if closest_amil:
                # Eylem açıkça varsa (Zarf-ı Lağv)
                dependencies.append((closest_amil, t1, rel_name, 'Zarf_Lagv'))
            else:
                # Eylem yoksa ontolojik uzaya zımni varlık (Kainun) enjekte edilir (Zarf-ı Müstakar)
                dependencies.append(('Kainun_Virtual', t1, rel_name, 'Zarf_Mustakar'))
            return True
        return False

    def _apply_nominal_adjuncts(self, t1: str, t2: str, m1: Optional[MorphologicalAnalysis], m2: Optional[MorphologicalAnalysis], tokens: List[str], idx: int, lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]]) -> bool:
        """
        .. mantik_kurali:: İzafet (Tamlamalar) ve Kesişim (Intersection) Uzayı
            İsim tamlamaları (İzafet) ve Sıfat uyumları, Z3 uzayında varlıkların 
            alt-kümelerini (Subset: $x \in Y$) veya özellik kesişimlerini 
            (Intersection: $x \in A \cap B$) matematiksel olarak tanımlar.
            
        [FAZ 1 ENTEGRASYONU]: İzafet, Hâl, Temyiz ve Sıfat tamlamaları; saf ontolojik 
        matrisler olan Irab, Number, Gender ve Definiteness bayrakları eşleştirilerek 
        denetlenir (Feature Unification). Bu, Gayri Munsarif veya Cemi Mükesser kalıplarındaki görsel/dizgisel 
        uyumsuzlukları matematiksel olarak aşar.
        
        [FAZ 4 ENTEGRASYONU]: Hâl ve Temyiz ontolojik ayrımı katı HPSG matrisinden okunarak
        Z3 kısıt uzayı (TimeSortVasfi vs TimeSortZati) için güvence altına alınmıştır.
        """
        if m1 and m2 and getattr(m1, 'ontologic_type', '') == "Ism" and getattr(m2, 'ontologic_type', '') == "Ism":
            irab_m2 = self._get_irab_val(m2)
            irab_m1 = self._get_irab_val(m1)
            
            def_t1 = self._is_definite(t1, lexicon, dependencies)
            def_t2 = self._is_definite(t2, lexicon, dependencies)

            # 1. İzafet Kuralı (Muzaf nekra, Muzafun İleyh ma'rife/mecrur)
            if not def_t1 and (def_t2 or irab_m2 == "Majrur"):
                dependencies.append((t1, t2, 'Mudaf_MudafIlayh', 'Majrur'))
            
            # 2. Hâl ve Temyiz Ayrımı (Ontolojik Nitelik Ayrımı - Faz 4 Yaması)
            elif (irab_m2 == "Mansub" or irab_m2 == "Mansub_or_Majrur") and getattr(m1, 'thematic_role', '') in ["Agent", "Patient", "Action"]:
                
                # Câmid (Türememiş) ve Müştak (Türemiş) kontrolü HPSG veya Ontolojik Tip üzerinden yapılır
                m2_o_type = getattr(m2, 'ontologic_type', '')
                if m2.hpsg and m2.hpsg.ontologic_type:
                    m2_o_type = m2.hpsg.ontologic_type.value if isinstance(m2.hpsg.ontologic_type, Enum) else str(m2.hpsg.ontologic_type)
                    
                is_mustak = m2_o_type == "Ism_Mustak" or ("Camid" not in getattr(m2, 'pattern', '') and "Gayri_Munsarif" not in getattr(m2, 'pattern', ''))
                
                if is_mustak:
                    # Hâl: Geçici durum arazıdır (TimeSortVasfi'ye kilitlenir)
                    dependencies.append((t1, t2, "Rel_Hal", "Mansub"))
                else:
                    # Temyiz: Zâtî ve evrensel bir açıklamadır (TimeSortZati'ye kilitlenir)
                    dependencies.append((t1, t2, "Rel_Temyiz", "Mansub"))

            # 3. Sıfat-Mevsuf Uyum Kuralı (Tam Unification)
            is_sifat_uyumu = False
            if def_t1 == def_t2:
                if irab_m1 == irab_m2 and self._get_gender_val(m1) == self._get_gender_val(m2) and self._get_number_val(m1) == self._get_number_val(m2):
                    is_sifat_uyumu = True
                
                # Gayri Munsarif İstisnası için tolerans (Mansub_or_Majrur HPSG matrisinde örtüşürse)
                elif getattr(m2.hpsg, 'is_diptote', False) and irab_m1 == "Majrur" and irab_m2 == "Mansub_or_Majrur":
                    if self._get_gender_val(m1) == self._get_gender_val(m2) and self._get_number_val(m1) == self._get_number_val(m2):
                        is_sifat_uyumu = True
            
            if is_sifat_uyumu:
                dependencies.append((t1, t2, 'Sifat_Mevsuf', 'Tabi'))
            return True
        return False

    def _apply_bedel_apposition(self, t1: str, t2: str, m1: Optional[MorphologicalAnalysis], m2: Optional[MorphologicalAnalysis], lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]]) -> bool:
        """
        .. pedagojik_anlati:: Bedel ve Mantıksal Kimlik Çözümlemesi (Pointer Aliasing)
            Bedel, kendisinden önce geçen ismin (Mübdelun Minh) ontolojik kimliğine 
            doğrudan işaret eden (Pointer Aliasing) bir amil-mamul yapısıdır.
            Z3 motorunda bu yapı, iki farklı EntitySort değişkeninin hafızada 
            aynı pointer'a eşitlenmesi (Identity: $Zeyd = Kardes$) demektir.
        """
        if m1 and m2 and getattr(m1, 'ontologic_type', '') == "Ism" and getattr(m2, 'ontologic_type', '') == "Ism":
            if self._is_definite(t1, lexicon, dependencies) and self._is_definite(t2, lexicon, dependencies):
                irab_match = self._get_irab_val(m1) == self._get_irab_val(m2)
                gen_match = self._get_gender_val(m1) == self._get_gender_val(m2)
                num_match = self._get_number_val(m1) == self._get_number_val(m2)
                
                if irab_match and gen_match and num_match:
                    if getattr(m1, 'thematic_role', '') == "Entity" and getattr(m2, 'thematic_role', '') == "Entity":
                        is_already_sifat = any((rel == 'Sifat_Mevsuf' and u == t1 and v == t2) for u, v, rel, _ in dependencies)
                        if not is_already_sifat:
                            dependencies.append((t1, t2, 'Bedel_Identity', 'Tabi_Identity'))
                            return True
        return False

    def _apply_conditional_and_disjunctive_logic(self, t1: str, t2: str, dependencies: List[Tuple[str, str, str, str]]) -> bool:
        """
        .. mantik_kurali:: Kadiyye-i Şartiyye ve Munfasıla (Hipotetik ve Ayrık Önermeler)
            [FAZ 2 ENTEGRASYONU]: İbn Sînâcı 'İn', 'Lev' (Katı Zorunluluk/Modus Ponens) ve 
            'İmmâ', 'Ev' (Katı Ayrıklık/XOR) yapılarının Z3 AST köprüsünü kurar. Sıradan 
            bir z3.Implies veya z3.Or değil, erişilebilir tüm Kripke dünyalarını kapsayan 
            Modal kısıtlara dönüştürülür.
        """
        if t1.lower() in self.shart_luzumi:
            # Lüzumî Şartiyye (Strict Implication: W_1'deki öncül, W_2'deki neticeyi zorunlu kılar)
            dependencies.append((t1, t2, "Rel_Shart_Luzumi", "Majzum"))
            return True
            
        if t1.lower() in self.munfasila_inadi:
            # İnadî Hakikiyye (Strict XOR: Mâniatü'l-Cem' ve'l-Hulüvv)
            dependencies.append((t1, t2, "Rel_Munfasila_Inadi", "Tabi"))
            return True
            
        return False

    def _apply_shamsiyye_modalities(self, t1: str, t2: str, dependencies: List[Tuple[str, str, str, str]]) -> bool:
        """
        .. felsefe_notu:: Kâtibî'nin 13 Kipli Yüzey Zarfları (Surface Modalities)
            [FAZ 2 ENTEGRASYONU]: 'Dâimâ', 'Kat'an', 'Muhâlan' gibi zarflar, cümlenin 
            yüklemini (Amil) Zâtî ve Vasfî zaman kiplerine (TimeSortZati/TimeSortVasfi) 
            sokan ontolojik mühürlerdir. AST tarafında doğrudan Z3 Modal Operator 
            düğümlerine çevrilir.
        """
        # Hata 1 (Cyclic Dependency) Düzeltmesi: Kiplik zarfı hem t1 hem de t2 pozisyonunda
        # olabilir. Kayan pencere kontrolünde cümlenin sonundaysa ('qat'an' gibi) 
        # t2 pozisyonunda da yakalanıp t1'e eklemlenmelidir.
        if t1.lower() in self.modal_adverbs:
            modality = self.modal_adverbs[t1.lower()]
            dependencies.append((t1, t2, f'Modal_{modality}', 'Mansub'))
            return True
        elif t2.lower() in self.modal_adverbs:
            modality = self.modal_adverbs[t2.lower()]
            dependencies.append((t2, t1, f'Modal_{modality}', 'Mansub'))
            return True
            
        return False

    def _resolve_adjacent_pairs(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]], amil_index: int) -> None:
        """
        .. pedagojik_anlati:: Yanal Bağlam (Adjacent Context) İşleyicisi
        Kayan pencere (Sliding Window) algoritmasıyla, doğrusal bağlamda yan yana gelen 
        lafızların ontolojik kilitlerini (İzafet, Sıfat, Bedel) sırayla oluşturur.
        """
        for i in range(len(tokens) - 1):
            t1 = tokens[i]
            t2 = tokens[i+1]
            
            m1 = lexicon.get(t1)
            m2 = lexicon.get(t2)
            
            # Sorumluluk zinciri (Chain of Responsibility)
            if self._apply_pragmatic_modifiers(t1, t2, m1, amil_index, i, dependencies): continue
            if self._apply_dynamic_transitions(t1, t2, tokens, i, dependencies): continue
            if self._apply_spatial_mutaallak(t1, t2, tokens, i, lexicon, dependencies): continue
            if self._apply_nominal_adjuncts(t1, t2, m1, m2, tokens, i, lexicon, dependencies): continue
            if self._apply_bedel_apposition(t1, t2, m1, m2, lexicon, dependencies): continue
            if self._apply_conditional_and_disjunctive_logic(t1, t2, dependencies): continue
            if self._apply_shamsiyye_modalities(t1, t2, dependencies): continue

    def _resolve_ism_mevsul_and_sila(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]]) -> None:
        """
        .. mantik_kurali:: İsm-i Mevsûl ve Sıla Cümlesi (Relative Clauses)
            [FAZ 3 ENTEGRASYONU]: Arapçada 'Ellezî' (Mevsûl), Z3 Kripke uzayında 
            Lambda Soyutlaması ($\lambda x. \Phi(x)$) işlevi görür. Mevsûl'den sonra gelen 
            eylem (Fiil) veya yargı Sıla Cümlesidir. AST'de bu bir alt-graf (Sub-graph) 
            olarak bağlanır ve Âid zamiri (Pointer Alias) ile Mevsûl'e eşitlenir.
        """
        for idx, token in enumerate(tokens):
            morph = lexicon.get(token)
            if not morph:
                continue
                
            o_type = getattr(morph, 'ontologic_type', '')
            if morph.hpsg and morph.hpsg.ontologic_type:
                o_type = morph.hpsg.ontologic_type.value if isinstance(morph.hpsg.ontologic_type, Enum) else str(morph.hpsg.ontologic_type)
            
            pattern = getattr(morph, 'pattern', '')
            is_mevsul = o_type == "Ism_Mevsul" or pattern == "Ism_Mevsul" or token.lower() in ["ellezi", "elleti", "ellezine", "men", "ma"]
            
            if is_mevsul:
                sila_root = None
                for sub_idx in range(idx + 1, len(tokens)):
                    sub_token = tokens[sub_idx]
                    sub_morph = lexicon.get(sub_token)
                    if sub_morph:
                        sub_o_type = getattr(sub_morph, 'ontologic_type', '')
                        if sub_morph.hpsg and sub_morph.hpsg.ontologic_type:
                            sub_o_type = sub_morph.hpsg.ontologic_type.value if isinstance(sub_morph.hpsg.ontologic_type, Enum) else str(sub_morph.hpsg.ontologic_type)
                        
                        if sub_o_type == "Fiil":
                            sila_root = sub_token
                            break
                        
                if sila_root:
                    dependencies.append((token, sila_root, 'Rel_Sila', 'Sila_Clause'))
                    dependencies.append((token, f"{sila_root}_Aid_Virtual", 'Rel_Aid', 'PointerAlias'))


    def _resolve_inne_scope(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]], inne_token: Optional[str], inne_index: int, amil_token: Optional[str], amil_index: int) -> None:
        """
        .. pedagojik_anlati:: İnne'nin Ameli ve Epistemik Zorunluluk (Epistemic Necessity)
            İnne'nin ismini nasb, haberini ref' yapması basit bir sentaktik kural değildir.
            Kripke uzayında bu işlem, önermeyi Modal Mantıktaki zorunluluk operatörüne ($\square$) 
            bağlayarak 'Zorunlu Hakikat' (Necessity) statüsüne kilitler. SMT'de bu, evrensel 
            niceleyici `z3.ForAll` ile temsil edilecektir.
        """
        if not inne_token:
            return
            
        ism_tokens_after = [t for idx, t in enumerate(tokens) if idx > inne_index and lexicon.get(t) and getattr(lexicon.get(t), 'ontologic_type', '') == "Ism"]
        
        if ism_tokens_after:
            ism_inne = ism_tokens_after[0]
            dependencies.append((inne_token, ism_inne, 'Amel_Inne_Ism', 'Mansub'))
            
            if amil_token and amil_index > inne_index:
                dependencies.append((inne_token, amil_token, 'Amel_Inne_Haber', 'Marfu_Mahallen'))
            elif len(ism_tokens_after) >= 2:
                haber_inne = None
                for ism in ism_tokens_after[1:]:
                    is_mudaf_ilayh = any(rel == 'Mudaf_MudafIlayh' and t_sub == ism for _, t_sub, rel, _ in dependencies)
                    if not is_mudaf_ilayh:
                        haber_inne = ism
                        break
                if not haber_inne:
                    haber_inne = ism_tokens_after[-1]
                
                dependencies.append((inne_token, haber_inne, 'Amel_Inne_Haber', 'Marfu'))

    def _resolve_nominal_copula(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]]) -> List[Tuple[str, str, str, str]]:
        """
        .. pedagojik_anlati:: Kadiyye-i Hamliyye ve Rabıta (Zero-Copula) Düğümü
            [FAZ 3 ENTEGRASYONU]: İbn Hişâm'ın 'Muğni'l-Lebîb' kuralı gereği Haber 
            müfred (tekil isim), Şibh-i Cümle (Zarf/Harf-i Cer) veya Cümle-i Fiiliye olabilir.
            Mübteda ile Haber arasına Rabıta düğümü atılarak zımnî (Copula) bağ kurulur.
            Hata Ayıklama Yaması: Copula yalnızca İsim Cümlelerinde devreye girer.
        """
        valid_mubteda_candidates = []
        for t in tokens:
            m = lexicon.get(t)
            if m and getattr(m, 'ontologic_type', '') == "Ism":
                is_invalid = any(rel in ['Mudaf_MudafIlayh', 'Harf_Mecrur', 'Mecrur_Diptote_Override', 'Amel_Inne_Ism', 'Amel_Inne_Haber', 'Fail', 'Naib_Fail', 'Meful', 'Rel_Sila', 'Rel_Ihtisas', 'Rel_Hal', 'Rel_Temyiz'] and v == t for u, v, rel, ir in dependencies)
                # Kayan pencerede "qat'an" veya "daima" modalite olarak sağdan bağlanmışsa (t2->t1)
                # Döngü Hatası (Cyclic Dependency) engellemesi:
                is_modal = any(str(rel).startswith('Modal_') and u == t for u, v, rel, ir in dependencies)
                if not is_invalid and not is_modal:
                    valid_mubteda_candidates.append(t)

        if not valid_mubteda_candidates:
            return dependencies

        mubteda = valid_mubteda_candidates[0]
        mubteda_idx = tokens.index(mubteda)
        haber = None
        
        # [Cümle-i Fiiliye vs İsmiye Denetimi]: Eğer ilk geçerli mübteda adayı bir 
        # Fiil'den SONRA geliyorsa, bu cümle zaten bir Fiil Cümlesidir. Copula iptal edilir.
        amil_index = next((idx for idx, t in enumerate(tokens) if lexicon.get(t) and getattr(lexicon.get(t), 'ontologic_type', '') == "Fiil"), -1)
        if amil_index != -1 and amil_index < mubteda_idx:
            return dependencies

        has_zarf_mustakar = any(rel in ['Muteallak_Mekan', 'Muteallak_Harf'] and am == 'Kainun_Virtual' for am, ma, rel, ir in dependencies)

        for sub_idx in range(mubteda_idx + 1, len(tokens)):
            t_sub = tokens[sub_idx]
            m_sub = lexicon.get(t_sub)
            if m_sub:
                o_type = getattr(m_sub, 'ontologic_type', '')
                if m_sub.hpsg and m_sub.hpsg.ontologic_type:
                    o_type = m_sub.hpsg.ontologic_type.value if isinstance(m_sub.hpsg.ontologic_type, Enum) else str(m_sub.hpsg.ontologic_type)
                
                if o_type == "Ism":
                    is_mudaf_ilayh = any(rel == 'Mudaf_MudafIlayh' and v == t_sub for u, v, rel, ir in dependencies)
                    is_sifat = any(rel == 'Sifat_Mevsuf' and v == t_sub for u, v, rel, ir in dependencies)
                    is_badal = any(rel == 'Bedel_Identity' and v == t_sub for u, v, rel, ir in dependencies)
                    is_modal_sub = any(str(rel).startswith('Modal_') and u == t_sub for u, v, rel, ir in dependencies)
                    if not is_mudaf_ilayh and not is_sifat and not is_badal and not is_modal_sub:
                        haber = t_sub
                        break
                elif o_type == "Fiil":
                    haber = t_sub
                    break
        
        if not haber and has_zarf_mustakar:
            haber = 'Kainun_Virtual'
            
        if not haber and len(valid_mubteda_candidates) > 1:
            haber = valid_mubteda_candidates[-1]
            
        if not haber:
            # [Anti-Cyclic Kural]: Eğer geriye kalan adaylar birer Mudaf Ilayh veya tabi ise
            # onları zorla Haber yapmak ontolojik döngüye (Semantic Shift & Cycle) sebep olur.
            # Bunun yerine sanal varoluş düğümünü (Kainun_Virtual) yüklem tayin ediyoruz.
            haber = 'Kainun_Virtual'

        if mubteda != haber:
            # [DAG Güvenlik Duvarı]: Mübteda'dan Haber'e halihazırda çekilmiş bir 
            # Sifat_Mevsuf gibi yanal bağ varsa, bunu kopararak Haber statüsüne terfi ettiriyoruz.
            edges_to_remove = [d for d in dependencies if d[0] == mubteda and d[1] == haber]
            for d in edges_to_remove:
                dependencies.remove(d)

            is_mubteda_marife = self._is_definite(mubteda, lexicon, dependencies)
            is_haber_marife = False
            if haber != 'Kainun_Virtual' and lexicon.get(haber) and getattr(lexicon.get(haber), 'ontologic_type', '') == "Ism":
                is_haber_marife = self._is_definite(haber, lexicon, dependencies)
            
            dependencies.append(('Rabita_Virtual', mubteda, 'Rabita_Subject', 'Marfu'))
            dependencies.append(('Rabita_Virtual', haber, 'Rabita_Predicate', 'Marfu'))
            
            if is_mubteda_marife and is_haber_marife:
                dependencies.append((haber, mubteda, 'Rabita_Identity', 'Marfu'))
            elif is_mubteda_marife and lexicon.get(haber) and getattr(lexicon.get(haber), 'ontologic_type', '') == "Fiil":
                dependencies.append((haber, mubteda, 'Rabita_Cümle_Fiiliye', 'Marfu'))
            else:
                dependencies.append((haber, mubteda, 'Rabita_Predication', 'Marfu'))

        return dependencies

    def _resolve_verbal_arguments(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]], amil_token: str, amil_index: int) -> None:
        """
        .. pedagojik_anlati:: Amil-Mamul Ataması ve Müstatir (Gizli) Zamirler (DRT)
            Eğer cümlede eylemi yapan açık Fail (Agent) yoksa, kelâm felsefesindeki 
            "Her eylemin bir faili vardır" aksiyomu gereği sistem çökmeye zorlanamaz. 
            Bunun yerine Discourse Representation Theory (DRT) kuralları işletilerek 
            Müstatir Zamir (Hidden Pronoun) cümlenin mantıksal matrisine soyut 
            `z3.Exists` varoluşsal değişkenleri olarak zerk edilir.

            [FAZ 2 ENTEGRASYONU]: Mebnî lil-Meçhul (Edilgen/Passive) Fiil Çözümlemesi.
            Eğer amilin (fiilin) çatısı (voice) 'Passive' ise:
            1. Merfu öge (Örn: Zeydun) 'Fail' değil, 'Naib_Fail' olarak işaretlenir.
            2. 'Fail' (Agent) ontolojik olarak gizlendiği için, nedensellik aksiyomu 
               gereği AST'ye 'Unknown_Agent_Virtual' (z3.Exists) düğümü Fail olarak raptedilir.
        """
        has_explicit_fail = False
        has_explicit_naib_fail = False
        
        amil_morph = lexicon.get(amil_token)
        voice = getattr(amil_morph, 'voice', 'Active') if amil_morph else 'Active'
        
        for idx, token in enumerate(tokens):
            if token == amil_token: 
                continue
                
            morph = lexicon.get(token)
            if not morph or getattr(morph, 'ontologic_type', '') != "Ism":
                continue

            irab_val = self._get_irab_val(morph)

            if irab_val == "Marfu":
                is_inne_haber = any(rel == 'Amel_Inne_Haber' and mamul == token for _, mamul, rel, _ in dependencies)
                if not is_inne_haber:
                    if voice == "Passive":
                        dependencies.append((amil_token, token, 'Naib_Fail', 'Marfu'))
                        has_explicit_naib_fail = True
                    else:
                        dependencies.append((amil_token, token, 'Fail', 'Marfu'))
                        has_explicit_fail = True
            
            elif irab_val == "Mansub" or irab_val == "Mansub_or_Majrur":
                is_hal_temyiz = any(rel in ['Rel_Hal', 'Rel_Temyiz'] and mamul == token for _, mamul, rel, _ in dependencies)
                is_majrur = any(mamul == token and (irab == 'Majrur' or rel == 'Mecrur_Diptote_Override') for _, mamul, rel, irab in dependencies)
                is_inne_ism = any(rel == 'Amel_Inne_Ism' and mamul == token for _, mamul, rel, _ in dependencies)
                
                if not is_hal_temyiz and not is_majrur and not is_inne_ism:
                    if idx < amil_index:
                        dependencies.append((amil_token, token, 'Rel_Ihtisas', 'Mansub'))
                    else:
                        dependencies.append((amil_token, token, 'Meful', 'Mansub'))
            
            elif irab_val == "Majrur":
                is_sub_tree_child = any((rel == 'Mudaf_MudafIlayh' or rel == 'Rel_Atif' or rel == 'Harf_Mecrur') and t2 == token for _, t2, rel, _ in dependencies)
                if not is_sub_tree_child:
                    dependencies.append((amil_token, token, 'Majrur', 'Majrur'))

        # DRT Müstatir Zamir Zerk Etme (Hidden Pronoun Injection)
        if amil_token:
            if voice == "Passive":
                # Aksiyom: Failsiz eylem olamaz. Edilgen yapıda fail varoluşsal bir bilinmeze eşittir.
                dependencies.append((amil_token, 'Unknown_Agent_Virtual', 'Fail', 'Marfu_Virtual'))
                
                # Eğer dışsal bir naib fail (Örn: "Zeyd") yoksa, gizli zamir (Örn: "Huve") naib fail olur.
                if not has_explicit_naib_fail and amil_morph:
                    hidden_pronoun = getattr(amil_morph, 'hidden_pronoun', None)
                    if hidden_pronoun:
                        dependencies.append((amil_token, hidden_pronoun, 'Naib_Fail', 'Marfu_Virtual'))
            else:
                if not has_explicit_fail and amil_morph:
                    hidden_pronoun = getattr(amil_morph, 'hidden_pronoun', None)
                    if hidden_pronoun:
                        dependencies.append((amil_token, hidden_pronoun, 'Fail', 'Marfu_Virtual'))

    def suggest_dependencies(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis]) -> List[Tuple[str, str, str, str]]:
        """
        .. pedagojik_anlati:: Ontolojik Orkestrasyon Akışı (AST Pipeline)
        Cümlenin başından sonuna kadar, mantıksal önceliğe (Precedence) göre amillerin 
        mamullere etkisini sıraya koyar. Önce Kıyâsî ve Semâî kökler tespit edilir, sonra 
        bağlamsal (Adjacent) operatörler işlenir.
        """
        dependencies = []
        
        amil_token, amil_index, inne_token, inne_index = self._identify_primary_governors(tokens, lexicon)
        
        self._resolve_adjacent_pairs(tokens, lexicon, dependencies, amil_index)
        self._resolve_ism_mevsul_and_sila(tokens, lexicon, dependencies)
        self._resolve_inne_scope(tokens, lexicon, dependencies, inne_token, inne_index, amil_token, amil_index)

        dependencies = self._resolve_nominal_copula(tokens, lexicon, dependencies)

        if amil_token:
            self._resolve_verbal_arguments(tokens, lexicon, dependencies, amil_token, amil_index)
                    
        return dependencies

    def build_ast(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]], lexicon: Optional[Dict[str, MorphologicalAnalysis]] = None) -> nx.DiGraph:
        """
        .. felsefe_notu:: Yönlü Grafik (Directed Graph) ve Z3 Determinizmi
        Listeler halinde çıkarılan tüm mantıksal bağları NetworkX üzerinden Yönlü Bir Grafiğe 
        (DiGraph) döker. 
        [FAZ 2 MİMARİSİ]: Kâtibî modaliteleri (Zaruriyye/Daime) ve Lüzumî/İnadî şartlar, 
        `z3_mapping` etiketiyle SMT'ye Z3 Expression Builder üzerinden katı operatör 
        olarak iletilir.
        [FAZ 3 MİMARİSİ]: İsm-i Mevsûl (Rel_Sila), Âid Zamiri (Rel_Aid) ve Cümle-i 
        Fiiliye Haber (Rabita_Cümle_Fiiliye) için SMT karşılıkları kısıt haritasına eklenmiştir.
        """
        # Hata 1 (Graph State Leak) Düzeltmesi: Graf objesini doğrudan .clear() ile silmek 
        # yerine temiz ve izole yeni bir graf tahsis ediliyor (Thread-Safe).
        self.dependency_graph = nx.DiGraph()
         
        for token in tokens:
            node_attrs = {"virtual": False, "ast_node_class": "StandardEntity"}
            if lexicon and token in lexicon:
                m = lexicon[token]
                o_type = getattr(m, 'ontologic_type', '')
                
                if o_type == "Harf_Inne" or token.lower() in self.shart_luzumi or token.lower() in self.munfasila_inadi:
                    node_attrs["ast_node_class"] = "EpistemicOperatorNode"
                    node_attrs["operator_type"] = "Necessity_or_Condition"
                elif token.lower() in self.modal_adverbs:
                    node_attrs["ast_node_class"] = "ModalOperatorNode"
                elif o_type == "Fiil":
                    node_attrs["ast_node_class"] = "ActionNode"
                elif getattr(m, 'pattern', '') == "Ism_Mevsul":
                    node_attrs["ast_node_class"] = "LambdaAbstractionNode"
            self.dependency_graph.add_node(token, **node_attrs)
            
        for amil, mamul, rel, irab in dependencies:
            if mamul not in self.dependency_graph:
                ast_class = "DRT_ExistentialNode" if 'Virtual' in irab else "StandardEntity"
                self.dependency_graph.add_node(mamul, virtual=True, ast_node_class=ast_class)
            
            if amil not in self.dependency_graph:
                if amil in ['Rabita_Virtual', 'Kainun_Virtual']:
                    self.dependency_graph.add_node(amil, virtual=True, ast_node_class="ZeroCopulaNode")
                else:
                    self.dependency_graph.add_node(amil, virtual=True, ast_node_class="StandardEntity")
                
            # Z3 Kripke Uzayı ve Şemsiyye Mantığı (ModalLogic) Eşleştirmeleri
            edge_attrs = {"relation": rel, "irab": irab, "z3_mapping": "Standard"}
            
            if rel in ['Muteallak_Mekan', 'Zarf_Mustakar', 'Zarf_Lagv']:
                edge_attrs["z3_mapping"] = "SpaceSortConstraint"
            elif rel in ['Bedel_Identity', 'Rabita_Identity', 'Rel_Aid']:
                edge_attrs["z3_mapping"] = "PointerAlias"
            elif rel == 'Rabita_Predication':
                edge_attrs["z3_mapping"] = "SetInclusion"
            elif rel in ['Rel_Sila', 'Rabita_Cümle_Fiiliye']:
                edge_attrs["z3_mapping"] = "SubClausePredicate"
            elif rel in ['Amel_Inne_Ism', 'Amel_Inne_Haber', 'Tevkid_Modifier', 'Kasr_Modifier']:
                edge_attrs["z3_mapping"] = "ModalNecessity"
            elif rel in ['Rel_Fa_Fuzaiyye', 'Rel_Fa_Sebebiyye']:
                edge_attrs["z3_mapping"] = "DynamicStateTransition"
            # [FAZ 2]: Kâtibî Modalite Köprüleri
            elif rel == 'Rel_Shart_Luzumi':
                edge_attrs["z3_mapping"] = "StrictImplication_Luzumi"
            elif rel == 'Rel_Munfasila_Inadi':
                edge_attrs["z3_mapping"] = "StrictDisjunction_Inadi"
            elif str(rel).startswith('Modal_'):
                edge_attrs["z3_mapping"] = rel # Örn: Modal_Zaruriyye_i_Mutlaka
                
            self.dependency_graph.add_edge(amil, mamul, **edge_attrs)
            
        return self.dependency_graph

    def extract_temporal_conditions(self, ast: nx.DiGraph) -> Dict[str, str]:
        """
        .. mantik_kurali:: Şemsiyye Kiplikleri ve Zaman Bağlamı
        Zaman/Durum zarflarını ve şart koşullarını AST'den filtreleyerek, Kripke 
        semantiğindeki TimeSort/WorldSort sıçrama noktalarını (Transition Nodes) ayıklar.
        """
        conditions = {}
        for u, v, data in ast.edges(data=True):
            if data.get('relation') in self.temporal_triggers:
                conditions[u] = v
        return conditions

    # -------------------------------------------------------------------------
    # FAZ 14 - KISIT İZOLASYONU VE TOPOLOJİK SAĞLIK (E2E SMT HEALTH PROTECTION)
    # -------------------------------------------------------------------------

    def _isolate_smt_constraints(self, ast: nx.DiGraph) -> Dict[str, List[Tuple[str, str, Dict[str, Any]]]]:
        """
        .. pedagojik_anlati:: Kısıt İzolasyon Bariyeri (Constraint Isolation)
        Z3 motoruna tek tiple aktarılan ilişkiler; İnne (Zorunluluk), Bedel (Kimlik) 
        ve Fâ (Dinamik Geçiş) gibi birbiriyle çelişen ontolojik düzlemlerde Combinatorial 
        Explosion yaratır. Bu metod, bağımlılıkları SMT derlenme fazlarına (Phases) ayırır.
        Faz 2 kapsamında "PHASE_6_MODAL_LOGIC" bariyeri eklenmiştir.
        [FAZ 3 ENTEGRASYONU]: İsm-i Mevsûl için eklenen 'Rel_Aid' eşitleme bağı 
        (Pointer Alias), döngü yaratmaması için 'PHASE_2_IDENTITY_ALIAS' katmanında izole edilmiştir.
        """
        isolated_phases = {
            "PHASE_1_STATIC_ONTOLOGY": [],   # Sabit kimlikler (Entity, Fail, Meful)
            "PHASE_2_IDENTITY_ALIAS": [],    # İşaretçi eşitleme (Bedel, Rabita, Aid)
            "PHASE_3_NECESSITY_SCOPE": [],   # Epistemik zorunluluk (İnne, Tevkid)
            "PHASE_4_SPATIAL_TEMPORAL": [],  # Müteallak (Mekân) ve Şartlar
            "PHASE_5_DYNAMIC_TRANSITION": [],# Fâ-i Füzâiyye ve Dinamik Geçişler
            "PHASE_6_MODAL_LOGIC": []        # Şemsiyye (Lüzumî, İnadî, Zarûriyye vb.)
        }
        
        for u, v, data in ast.edges(data=True):
            rel = data.get('relation', '')
            z3_map = data.get('z3_mapping', '')
            
            if rel in ['Bedel_Identity', 'Rabita_Identity', 'Rabita_Predication', 'Rel_Aid']:
                isolated_phases["PHASE_2_IDENTITY_ALIAS"].append((u, v, data))
            elif rel in ['Amel_Inne_Ism', 'Amel_Inne_Haber', 'Tevkid_Modifier', 'Kasr_Modifier']:
                isolated_phases["PHASE_3_NECESSITY_SCOPE"].append((u, v, data))
            elif rel in ['Muteallak_Mekan', 'Muteallak_Harf', 'Rel_Zarf_Zaman', 'Rel_Shart']:
                isolated_phases["PHASE_4_SPATIAL_TEMPORAL"].append((u, v, data))
            elif rel in ['Rel_Fa_Fuzaiyye', 'Rel_Fa_Sebebiyye']:
                isolated_phases["PHASE_5_DYNAMIC_TRANSITION"].append((u, v, data))
            elif "Strict" in z3_map or "Modal_" in z3_map:
                isolated_phases["PHASE_6_MODAL_LOGIC"].append((u, v, data))
            else:
                isolated_phases["PHASE_1_STATIC_ONTOLOGY"].append((u, v, data))
                
        return isolated_phases

    def _enforce_topological_order(self, ast: nx.DiGraph) -> List[str]:
        """
        .. mantik_kurali:: Asiklik Bağımlılık Zorlayıcı (DAG Enforcement)
        Z3 First-Order Logic (FOL) motorunun 'Ex Falso Quodlibet' (Çelişkiden her şey çıkar) 
        tuzağına düşmemesi için, gramer ağacı kesinlikle Yönlü Asiklik Graf (DAG) olmalıdır. 
        Döngü (Cycle) tespit edilirse, sistem felsefi çelişkiyi raporlar ve hiyerarşik 
        derleme sırasını çıkarır.
        """
        if not nx.is_directed_acyclic_graph(ast):
            cycles = list(nx.simple_cycles(ast))
            raise ValueError(f"[LOGIC_FAILURE_PROBABILITY: HIGH] AST içerisinde ontolojik "
                             f"döngü (Cyclic Dependency) tespit edildi. Z3 sonsuz kısıt yayılımına "
                             f"girecektir. Döngü oluşturan düğümler: {cycles}")
        
        # Z3'te tanımlamalar yaprak (leaf) düğümlerden kök (root) düğümlere doğru 
        # (Dependency-first) derlenmelidir. Bu yüzden Topological Sort listesi ters çevrilir.
        compilation_order = list(reversed(list(nx.topological_sort(ast))))
        return compilation_order

    def run_e2e_health_check(self, ast: nx.DiGraph) -> Dict[str, Any]:
        """
        .. pedagojik_anlati:: Faz 14 Gramer Sağlık Taraması (Health Check Orchestrator)
        Kripke uzayı kombinatoryal patlamalarını engellemek üzere AST'yi denetler. 
        Topolojik sırayı (Topological Order) ve faz izoleli kısıtları (Isolated Phases) 
        döndürerek Z3 motorunun güvenle çalışacağı bir "SAT-Safe" yürütme planı sunar.
        """
        compilation_order = self._enforce_topological_order(ast)
        isolated_phases = self._isolate_smt_constraints(ast)
        
        return {
            "is_dag": True,
            "compilation_order": compilation_order,
            "isolated_phases": isolated_phases
        }