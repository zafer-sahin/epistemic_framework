import networkx as nx
from typing import List, Dict, Tuple, Optional, Any
from linguistics.sarf_parser import MorphologicalAnalysis

"""
.. felsefe_notu:: İlm-i Nahiv ve Dilin Ontolojik Mimarisi
    Klasik İslâm gramerinde kelimeler zihinde veya metinde başıboş (bağımsız) dolaşamazlar. 
    Her cümle, bir "Amil" (etken/yöneten) ve "Mamul" (edilgen/yönetilen) ağıdır. Bu yapı, 
    Aristotelesçi "Muharrik" (Hareket Ettirici) ve "Müteharrik" (Hareket Eden) felsefesinin, 
    ve İslâm kelâmındaki nedensellik (İlliyet) ilkesinin dilbilimsel izdüşümüdür.
    Bu modül, ardışık doğal dil dizgilerini Z3 SMT çözücüsünün Kripke uzayında işleyebileceği 
    Hiyerarşik Bağımlılık Ağaçlarına (Directed Graph - AST) çevirerek, cümlenin mantıksal 
    anatomisini çıkarır.
"""

class NahivDependencyCompiler:
    """
    .. pedagojik_anlati:: Sentaktik Derleyici (Amil-Mamul Orkestrasyonu)
    Bu sınıf, kelimelerin i'rab (son hareke) durumlarına ve ontolojik tiplerine bakarak, 
    onların Kripke uzayında birbirlerine nasıl bağlanacağını (Dependency) tespit eder. 
    Geleneksel AST (Abstract Syntax Tree) mantığının aksine, buradaki her düğüm (node) bir 
    varlığı, her kenar (edge) ise ontolojik bir kısıtı (constraint) temsil eder.
    
    [FAZ 1 - LITERATE CHUNKING]: Bilişsel Yükü (Cognitive Load) asgari seviyede tutmak için, 
    karmaşık çözümleme algoritması hiyerarşik alt fonksiyonlara (Private Methods) yalıtılmıştır. 
    Her kural bloğu kendi mantıksal anlatısını taşır.
    """
    def __init__(self):
        self.definite_article = ("al_", "el_") 
        self.dependency_graph = nx.DiGraph()
        
        # .. mantik_kurali:: Şemsiyye Kiplikleri (Modalities)
        # Kâtibî'nin Şemsiyye mantığında, önermelerin zaman (Zaman) ve durum (Hal) 
        # kısıtlarına bağlanmasını sağlayan tetikleyiciler.
        self.temporal_triggers = ["Rel_Hal", "Rel_Zarf_Zaman", "Rel_Shart"]
        
        # Kadiyye-i Şartiyye (Hipotetik Önerme) için Fasıl (Ayrılma) ve Vasıl (Birleşme) operatörleri
        self.atif_particles = ["wa", "fa", "aw", "summe", "am", "bal", "la", "lakin"]
        
        # .. felsefe_notu:: Uzaysal/Bağıntısal Kısıtlar (SpaceSort Operators)
        # Harf-i cerler basit bağlaçlar değil, varlığın (Entity) Kripke dünyasında 
        # (WorldSort) hangi uzaysal düzleme yerleştiğini tayin eden ontolojik fonksiyonlardır.
        self.harf_i_cerler = {
            "fi": "Zarfiyye",           # İçindelik kısıtı
            "ala": "Isti_la",           # Üzerindelik kısıtı
            "min": "Ibtida_i_Gaye",     # Başlangıç noktası
            "ila": "Intiha_i_Gaye",     # Bitiş/Gaye noktası
            "bi": "Ilsak_Alet",         # Bitişiklik veya araçsallık
            "li": "Ihtisas_Mulk",       # Aidiyet/Mülkiyet bağıntısı
            "inde": "Zarfiyye",
            "tahta": "Zarfiyye",
            "fawqa": "Zarfiyye",
            "beyne": "Zarfiyye",
            "khalf": "Zarfiyye",
            "amam": "Zarfiyye",
            "an": "Mucaveze"            # Uzaklaşma/Aşma kısıtı
        }

    def _is_definite(self, token: str) -> bool:
        """
        .. mantik_kurali:: Ma'rife ve Nekra (Belirlilik ve Belirsizlik)
        Bir varlığın 'al-' takısı alması, onun evrensel kümeden (Universal Set) çekilip, 
        dış dünyada aktüelleşmiş spesifik bir varlığa (Instantiated Entity) dönüşmesidir.
        Bu durum Z3 SMT'de Skolemizasyon sürecini doğrudan etkiler.
        """
        return token.lower().startswith(self.definite_article)

    def _identify_primary_governors(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis]) -> Tuple[Optional[str], int, Optional[str], int]:
        """
        .. felsefe_notu:: Amil-i Kıyâsî ve Amil-i Semâî'nin Tespiti
        Kripke uzayının sınırlarını çizen temel yöneticileri (Governors) arar. 
        'Fiil', yapısal bir amildir (Kıyâsî) ve cümleye ontolojik hareket katar. 
        'İnne' ise duyuma/nakle dayalı bir amildir (Semâî) ve cümlenin epistemolojik 
        kesinliğini (Zorunluluk - $\square P$) mühürler. SMT ağacı bu kökler üzerine bina edilir.
        """
        amil_token = None
        amil_index = -1
        inne_token = None
        inne_index = -1
        
        for idx, token in enumerate(tokens):
            morph = lexicon.get(token)
            if morph:
                if morph.ontologic_type == "Fiil":
                    amil_token = token
                    amil_index = idx
                elif morph.ontologic_type == "Harf_Inne":
                    inne_token = token
                    inne_index = idx
        return amil_token, amil_index, inne_token, inne_index

    def _apply_pragmatic_modifiers(self, t1: str, t2: str, m1: Optional[MorphologicalAnalysis], amil_index: int, idx: int, dependencies: List[Tuple[str, str, str, str]]) -> bool:
        """
        .. pedagojik_anlati:: Muktazâ el-Hâl, Tevkîd ve Kasr
            İlm-i Ma'ânî'de 'Tevkîd' (Pekiştirme), muhatabın (Sâil'in) şüphesini gidermek için 
            önermeyi Modal Mantık'ta 'Zorunlu' (Necessity: $\square P$) statüsüne yükseltir.
            'Kasr' ise niteliği bir varlığa hapsetme işlemidir; $\forall x (Sifat(x) \iff Mevsuf(x))$ 
            şeklindeki mantıksal çift yönlü gerektirmeyi (Biconditional) SMT motoruna mühürler.
        """
        if m1 and m1.ontologic_type == "Harf_Tevkid":
            dependencies.append((t2, t1, 'Tevkid_Modifier', 'None'))
            return True
            
        if m1 and m1.ontologic_type == "Harf_Kasr":
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
            Klasik statik mantıkta (FOL) 'Fâ-i Füzâiyye' ve 'Sebebiyye'nin karşılığı yoktur, zira 
            bunlar zaman/durum sıçramalarını (State Transition) ifade eder. Bir eylemin (A) 
            aniden diğerini (B) var etmesi, SMT'de ardışık Kripke dünyalarının ($W_0 \implies W_1$) 
            yaratılmasını zorunlu kılar.
        """
        if t1.lower() in self.atif_particles:
            if idx > 0:
                t_prev = tokens[idx-1]
                if t1.lower() == "fa":
                    shart_exists = any(t.lower() in ["in", "iza", "law", "amma"] for t in tokens[:idx])
                    if shart_exists:
                        dependencies.append((t_prev, t2, 'Rel_Fa_Sebebiyye', 'Luzumi_Muttasila'))
                    else:
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
            olarak bağlanmak (Müteallak) zorundadırlar: 
            $\exists e. \text{LocatedIn}(e, \text{Space}, \text{World})$.
            Eğer bir eylem (Amil) açıksa bu 'Zarf-ı Lağv', açık değilse ve zihnen varlık takdir 
            ediliyorsa bu 'Zarf-ı Mustakar'dır.
        """
        if t1.lower() in self.harf_i_cerler:
            sem_type = self.harf_i_cerler[t1.lower()]
            rel_name = 'Muteallak_Mekan' if sem_type in ["Zarfiyye", "Isti_la"] else 'Muteallak_Harf'

            m2 = lexicon.get(t2)
            # Gayri Munsarif kelimeler harf-i cer sonrası fetha alsa da ontolojik olarak Mecrurdur.
            if m2 and getattr(m2, 'is_diptote', False):
                dependencies.append((t1, t2, 'Mecrur_Diptote_Override', 'Majrur'))
            else:
                dependencies.append((t1, t2, 'Harf_Mecrur', 'Majrur'))
            
            potential_amils = []
            for prev_idx in range(idx - 1, -1, -1):
                prev_token = tokens[prev_idx]
                prev_morph = lexicon.get(prev_token)
                if prev_morph:
                    if prev_morph.ontologic_type == "Fiil":
                        potential_amils.append(prev_token)
                        break
                    elif prev_morph.ontologic_type == "Ism" and prev_morph.thematic_role in ["Agent", "Patient", "Action"]:
                        potential_amils.append(prev_token)
                        break

            closest_amil = potential_amils[0] if potential_amils else None

            if closest_amil:
                dependencies.append((closest_amil, t1, rel_name, 'Zarf_Lagv'))
            else:
                dependencies.append(('Kainun_Virtual', t1, rel_name, 'Zarf_Mustakar'))
            return True
        return False

    def _apply_nominal_adjuncts(self, t1: str, t2: str, m1: Optional[MorphologicalAnalysis], m2: Optional[MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]]) -> bool:
        """
        .. mantik_kurali:: İzafet (Tamlamalar) ve Kesişim (Intersection) Uzayı
            İsim tamlamaları (İzafet) ve Sıfat uyumları, Z3 uzayında varlıkların 
            alt-kümelerini (Subset: $x \in Y$) veya özellik kesişimlerini 
            (Intersection: $x \in A \cap B$) matematiksel olarak tanımlar.
        """
        if m1 and m2 and m1.ontologic_type == "Ism" and m2.ontologic_type == "Ism":
            is_diptote_majrur = getattr(m2, 'is_diptote', False) and t2.lower().endswith('a')
            if not self._is_definite(t1) and (self._is_definite(t2) or t2.lower().endswith(('in', 'i')) or is_diptote_majrur):
                dependencies.append((t1, t2, 'Mudaf_MudafIlayh', 'Majrur'))
            
            elif t2.lower().endswith('an') and m1.thematic_role in ["Agent", "Patient", "Action"]:
                dependencies.append((t1, t2, "Rel_Hal", "Mansub"))

            is_sifat_uyumu = False
            if self._is_definite(t1) == self._is_definite(t2):
                if t1[-2:] == t2[-2:]:
                    is_sifat_uyumu = True
                elif getattr(m2, 'is_diptote', False) and t1.lower().endswith(('in', 'i')) and t2.lower().endswith('a'):
                    is_sifat_uyumu = True
            
            if is_sifat_uyumu:
                dependencies.append((t1, t2, 'Sifat_Mevsuf', 'Tabi'))
            return True
        return False

    def _apply_bedel_apposition(self, t1: str, t2: str, m1: Optional[MorphologicalAnalysis], m2: Optional[MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]]) -> bool:
        """
        .. pedagojik_anlati:: Bedel ve Mantıksal Kimlik Çözümlemesi (Pointer Aliasing)
            Bedel, kendisinden önce geçen ismin (Mübdelun Minh) ontolojik kimliğine 
            doğrudan işaret eden (Pointer Aliasing) bir amil-mamul yapısıdır.
            Z3 uzayında bu durum Entity değişkenlerinin (EntitySort) eşitlenmesi 
            (z3.And(x == y)) anlamına gelir. Çift yönlü kısıt döngülerini (Cycle) 
            önlemek için yön sabittir: Bedel -> Mübdelun Minh.
        """
        if m1 and m2 and m1.ontologic_type == "Ism" and m2.ontologic_type == "Ism":
            if self._is_definite(t1) and self._is_definite(t2) and t1[-2:] == t2[-2:]:
                if m1.thematic_role == "Entity" and m2.thematic_role == "Entity":
                    is_already_sifat = any((rel == 'Sifat_Mevsuf' and u == t1 and v == t2) for u, v, rel, _ in dependencies)
                    if not is_already_sifat:
                        dependencies.append((t1, t2, 'Bedel_Identity', 'Tabi_Identity'))
                        return True
        return False

    def _apply_conditional_logic(self, t1: str, t2: str, dependencies: List[Tuple[str, str, str, str]]) -> bool:
        """
        .. mantik_kurali:: Kadiyye-i Şartiyye (Hipotetik Önerme)
            Şart edatları (İn, İza vb.), SMT'deki mantıksal gerektirmeyi (Implication: $P \implies Q$) 
            AST yapısına mühürler.
        """
        if t1.lower() in ["in", "iza", "law", "amma"]:
            dependencies.append((t1, t2, "Rel_Shart", "Majzum"))
            return True
        return False

    def _resolve_adjacent_pairs(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]], amil_index: int) -> None:
        """
        .. pedagojik_anlati:: Yanal Bağlam (Adjacent Context) İşleyicisi
        Doğrusal bağlamda yan yana gelen lafızların ontolojik kilitlerini oluşturur. 
        Çalışma belleğini (Working Memory) aşırı yüklememek adına, Kripke uzayı kısıtlamaları 
        hiyerarşik olarak izole edilmiştir.
        """
        for i in range(len(tokens) - 1):
            t1 = tokens[i]
            t2 = tokens[i+1]
            
            m1 = lexicon.get(t1)
            m2 = lexicon.get(t2)
            
            if self._apply_pragmatic_modifiers(t1, t2, m1, amil_index, i, dependencies): continue
            if self._apply_dynamic_transitions(t1, t2, tokens, i, dependencies): continue
            if self._apply_spatial_mutaallak(t1, t2, tokens, i, lexicon, dependencies): continue
            if self._apply_nominal_adjuncts(t1, t2, m1, m2, dependencies): continue
            if self._apply_bedel_apposition(t1, t2, m1, m2, dependencies): continue
            if self._apply_conditional_logic(t1, t2, dependencies): continue

    def _resolve_inne_scope(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]], inne_token: Optional[str], inne_index: int, amil_token: Optional[str], amil_index: int) -> None:
        """
        .. pedagojik_anlati:: İnne'nin Ameli ve Epistemik Zorunluluk (Epistemic Necessity)
            İnne'nin ismini nasb, haberini ref' yapması basit bir sentaktik kural değildir.
            Kripke uzayında bu işlem, önermeyi 'Zorunlu Hakikat' (Necessity) statüsüne kilitler. 
            İ'rabın (Nasb/Ref) yanlış tespiti SMT motorunda Fail ile Meful'ü birbirine karıştırıp, 
            "Ex Falso Quodlibet" (Çelişkiden her şey çıkar) mantıksal patlamasına yol açar.
        """
        if not inne_token:
            return
            
        ism_tokens_after = [t for idx, t in enumerate(tokens) if idx > inne_index and lexicon.get(t) and lexicon.get(t).ontologic_type == "Ism"]
        
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
            Arapça isim cümlelerinde (Kadiyye-i Hamliyye) 'dır/dir' bildirme eki genellikle 
            görünmez. Zihin bu boşluğu otomatik doldursa da, deterministik SMT çözücüsü için 
            bu durum ölümcüldür. Bu algoritma, soyut AST'de görünmez bir "Rabıta Düğümü" 
            (Zero-Copula Node) üreterek; mübteda ile haber arasına mantıksal eşdeğerlik 
            (Identity: $x = y$) veya aidiyet (Predication: $x \in Y$) bağını matematiksel 
            olarak enjekte eder.
        """
        has_zarf_mustakar = any(rel in ['Muteallak_Mekan', 'Muteallak_Harf'] and am == 'Kainun_Virtual' for am, ma, rel, ir in dependencies)
        ism_tokens = [t for t in tokens if lexicon.get(t) and lexicon.get(t).ontologic_type == "Ism"]
        
        if has_zarf_mustakar and len(ism_tokens) >= 1:
             mubteda = ism_tokens[0]
             dependencies.append(('Kainun_Virtual', mubteda, 'Rabita_Predication', 'Marfu_Virtual'))
             return dependencies

        if len(ism_tokens) >= 2:
            mubteda = ism_tokens[0]
            haber = None
            for ism in ism_tokens[1:]:
                is_mudaf_ilayh = any(rel == 'Mudaf_MudafIlayh' and t_sub == ism for _, t_sub, rel, _ in dependencies)
                if not is_mudaf_ilayh:
                    haber = ism
                    break
            
            if not haber:
                haber = ism_tokens[-1]
            
            if mubteda != haber:
                is_mubteda_marife = self._is_definite(mubteda)
                is_haber_marife = self._is_definite(haber)
                
                dependencies.append(('Rabita_Virtual', mubteda, 'Rabita_Subject', 'Marfu'))
                dependencies.append(('Rabita_Virtual', haber, 'Rabita_Predicate', 'Marfu'))
                
                if is_mubteda_marife and is_haber_marife:
                    dependencies.append((haber, mubteda, 'Rabita_Identity', 'Marfu'))
                else:
                    dependencies.append((haber, mubteda, 'Rabita_Predication', 'Marfu'))
        
        return dependencies

    def _resolve_verbal_arguments(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]], amil_token: str, amil_index: int) -> None:
        """
        .. pedagojik_anlati:: Amil-Mamul Ataması ve Müstatir (Gizli) Zamirler
            Eğer cümlede eylemi yapan açık bir Fail yoksa, "Her eylemin bir faili vardır" 
            şeklindeki felsefi aksiyom gereği sistem çökmemelidir. Bu metod, İlm-i Sarf'ın 
            kökten çıkardığı gizli zamiri (Müstatir Zamir) alarak Z3 uzayına varoluşsal 
            bir değişken ($\exists x$) olarak zerk eder ve nedensellik krizini önler.
        """
        has_explicit_fail = False
        for idx, token in enumerate(tokens):
            if token == amil_token: 
                continue
                
            morph = lexicon.get(token)
            if not morph or morph.ontologic_type != "Ism":
                continue

            is_diptote = getattr(morph, 'is_diptote', False)

            if token.lower().endswith('un') or (is_diptote and token.lower().endswith('u')):
                is_inne_haber = any(rel == 'Amel_Inne_Haber' and mamul == token for _, mamul, rel, _ in dependencies)
                if not is_inne_haber:
                    dependencies.append((amil_token, token, 'Fail', 'Marfu'))
                    has_explicit_fail = True
            elif token.lower().endswith('an') or (is_diptote and token.lower().endswith('a')):
                is_hal = any(rel == 'Rel_Hal' and mamul == token for _, mamul, rel, _ in dependencies)
                is_majrur = any(mamul == token and (irab == 'Majrur' or rel == 'Mecrur_Diptote_Override') for _, mamul, rel, irab in dependencies)
                is_inne_ism = any(rel == 'Amel_Inne_Ism' and mamul == token for _, mamul, rel, _ in dependencies)
                
                if not is_hal and not is_majrur and not is_inne_ism:
                    if idx < amil_index:
                        dependencies.append((amil_token, token, 'Rel_Ihtisas', 'Mansub'))
                    else:
                        dependencies.append((amil_token, token, 'Meful', 'Mansub'))
            elif token.lower().endswith(('in', 'i')):
                is_sub_tree_child = any((rel == 'Mudaf_MudafIlayh' or rel == 'Rel_Atif' or rel == 'Harf_Mecrur') and t2 == token for _, t2, rel, _ in dependencies)
                if not is_sub_tree_child:
                    dependencies.append((amil_token, token, 'Majrur', 'Majrur'))

        if amil_token and not has_explicit_fail:
            amil_morph = lexicon.get(amil_token)
            hidden_pronoun = getattr(amil_morph, 'hidden_pronoun', None)
            if hidden_pronoun:
                dependencies.append((amil_token, hidden_pronoun, 'Fail', 'Marfu_Virtual'))

    def suggest_dependencies(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis]) -> List[Tuple[str, str, str, str]]:
        """
        .. pedagojik_anlati:: Ontolojik Orkestrasyon Akışı
        Cümlenin başından sonuna kadar, mantıksal önceliğe (Precedence) göre amillerin 
        mamullere etkisini sıraya koyar. Önce Kıyâsî ve Semâî kökler tespit edilir, sonra 
        bağlamsal operatörler işlenir.
        """
        dependencies = []
        
        amil_token, amil_index, inne_token, inne_index = self._identify_primary_governors(tokens, lexicon)
        
        self._resolve_adjacent_pairs(tokens, lexicon, dependencies, amil_index)
        self._resolve_inne_scope(tokens, lexicon, dependencies, inne_token, inne_index, amil_token, amil_index)

        if not amil_token and not inne_token:
            return self._resolve_nominal_copula(tokens, lexicon, dependencies)
            
        if not amil_token and inne_token:
            return dependencies 

        if amil_token:
            self._resolve_verbal_arguments(tokens, lexicon, dependencies, amil_token, amil_index)
                    
        return dependencies

    def build_ast(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]], lexicon: Optional[Dict[str, MorphologicalAnalysis]] = None) -> nx.DiGraph:
        """
        .. felsefe_notu:: Yönlü Grafik (Directed Graph) ve Determinizm
        Listeler halinde çıkarılan tüm mantıksal bağları NetworkX üzerinden Yönlü Bir Grafiğe 
        (DiGraph) döker. [FAZ 1.2-1.5 MİMARİSİ]: Kripke uzayında oluşacak sızıntıları önlemek 
        için her düğüme 'ast_node_class', her kenara ise SMT karşılığını bildiren 'z3_mapping' 
        etiketleri işlenir. Bu graf artık saf bir epistemolojik matristir.
        """
        self.dependency_graph.clear()
         
        for token in tokens:
            node_attrs = {"virtual": False, "ast_node_class": "StandardEntity"}
            if lexicon and token in lexicon:
                m = lexicon[token]
                if m.ontologic_type == "Harf_Inne":
                    node_attrs["ast_node_class"] = "EpistemicOperatorNode"
                    node_attrs["operator_type"] = "Necessity"
                elif m.ontologic_type == "Fiil":
                    node_attrs["ast_node_class"] = "ActionNode"
            self.dependency_graph.add_node(token, **node_attrs)
            
        for amil, mamul, rel, irab in dependencies:
            if mamul not in self.dependency_graph:
                ast_class = "DRT_ExistentialNode" if irab == 'Marfu_Virtual' else "StandardEntity"
                self.dependency_graph.add_node(mamul, virtual=True, ast_node_class=ast_class)
            
            if amil not in self.dependency_graph:
                if amil in ['Rabita_Virtual', 'Kainun_Virtual']:
                    self.dependency_graph.add_node(amil, virtual=True, ast_node_class="ZeroCopulaNode")
                else:
                    self.dependency_graph.add_node(amil, virtual=True, ast_node_class="StandardEntity")
                
            # Z3 Kripke Uzayı (SpaceSort/ModalLogic) Eşleştirmeleri
            edge_attrs = {"relation": rel, "irab": irab, "z3_mapping": "Standard"}
            
            if rel in ['Muteallak_Mekan', 'Zarf_Mustakar', 'Zarf_Lagv']:
                edge_attrs["z3_mapping"] = "SpaceSortConstraint"
            elif rel in ['Bedel_Identity', 'Rabita_Identity']:
                edge_attrs["z3_mapping"] = "PointerAlias"
            elif rel == 'Rabita_Predication':
                edge_attrs["z3_mapping"] = "SetInclusion"
            elif rel in ['Amel_Inne_Ism', 'Amel_Inne_Haber', 'Tevkid_Modifier', 'Kasr_Modifier']:
                edge_attrs["z3_mapping"] = "ModalNecessity"
            elif rel in ['Rel_Fa_Fuzaiyye', 'Rel_Fa_Sebebiyye']:
                edge_attrs["z3_mapping"] = "DynamicStateTransition"
                
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
        Z3 motoruna tek tiple aktarılan ilişkiler, İnne (Zorunluluk), Bedel (Kimlik) 
        ve Fâ (Dinamik Geçiş) gibi birbiriyle çelişen ontolojik düzlemlerde Combinatorial 
        Explosion yaratır. Bu metod, bağımlılıkları SMT derlenme fazlarına (Phases) ayırır.
        """
        isolated_phases = {
            "PHASE_1_STATIC_ONTOLOGY": [],   # Sabit kimlikler (Entity, Fail, Meful)
            "PHASE_2_IDENTITY_ALIAS": [],    # İşaretçi eşitleme (Bedel, Rabita)
            "PHASE_3_NECESSITY_SCOPE": [],   # Epistemik zorunluluk (İnne, Tevkid)
            "PHASE_4_SPATIAL_TEMPORAL": [],  # Müteallak (Mekân) ve Şartlar
            "PHASE_5_DYNAMIC_TRANSITION": [] # Fâ-i Füzâiyye ve Dinamik Geçişler
        }
        
        for u, v, data in ast.edges(data=True):
            rel = data.get('relation', '')
            if rel in ['Bedel_Identity', 'Rabita_Identity', 'Rabita_Predication']:
                isolated_phases["PHASE_2_IDENTITY_ALIAS"].append((u, v, data))
            elif rel in ['Amel_Inne_Ism', 'Amel_Inne_Haber', 'Tevkid_Modifier', 'Kasr_Modifier']:
                isolated_phases["PHASE_3_NECESSITY_SCOPE"].append((u, v, data))
            elif rel in ['Muteallak_Mekan', 'Muteallak_Harf', 'Rel_Zarf_Zaman', 'Rel_Shart']:
                isolated_phases["PHASE_4_SPATIAL_TEMPORAL"].append((u, v, data))
            elif rel in ['Rel_Fa_Fuzaiyye', 'Rel_Fa_Sebebiyye']:
                isolated_phases["PHASE_5_DYNAMIC_TRANSITION"].append((u, v, data))
            else:
                isolated_phases["PHASE_1_STATIC_ONTOLOGY"].append((u, v, data))
                
        return isolated_phases

    def _enforce_topological_order(self, ast: nx.DiGraph) -> List[str]:
        """
        .. mantik_kurali:: Asiklik Bağımlılık Zorlayıcı (DAG Enforcement)
        Z3 First-Order Logic (FOL) motorunun 'Ex Falso Quodlibet' tuzağına düşmemesi için,
        gramer ağacı kesinlikle Yönlü Asiklik Graf (DAG) olmalıdır. Döngü (Cycle) tespit
        edilirse, sistem felsefi çelişkiyi raporlar ve hiyerarşik derleme sırasını çıkarır.
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