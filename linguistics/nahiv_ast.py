import networkx as nx
from typing import List, Dict, Tuple, Optional
from linguistics.sarf_parser import MorphologicalAnalysis

"""
.. felsefe_notu::
    Klasik İslâm gramerinde kelimeler bağımsız değildir. Her cümle, bir "Amil" 
    (yöneten) ve "Mamul" (yönetilen) ağıdır. Bu, Aristotelesçi "Muharrik" ve 
    "Müteharrik" felsefesinin dilbilimsel izdüşümüdür.
    Bu modül, doğal dili Z3 SMT çözücüsünün Kripke uzayında işleyebileceği 
    Hiyerarşik Bağımlılık Ağaçlarına (Directed Graph - AST) çevirir.
"""

class NahivDependencyCompiler:
    """
    Arapça Sentaktik Bağımlılık Ağacını (Nahiv AST) üreten parser.
    Faz 10.2: Alt-ağaç (Sub-Tree) çözümleyicileri entegre edildi.
    Faz 2 - Adım 2.2: İlm-i Ma'ânî Tevkîd (Pekiştirme) edatlarının AST düğümüne bağlanması.
    Faz 2 - Adım 2.5: Takdim (Pre-positioning) ve İhtisas (Kasr) tespiti.
    Faz 2 - Adım 2.6: Kasr (Hasr) Operatörlerinde Yön Tespiti (Sıfat/Mevsuf) ve Harf-i Atıf (Fasıl/Vasıl) Entegrasyonu.
    [FAZ 1 ENTEGRASYONU]: Gayri Munsarif (Diptotes) kelimelerin cer durumundaki (fetha) i'rab istisnaları AST mantığına işlendi.
    [FAZ 2 ENTEGRASYONU]: Müstatir Zamir (Hidden Pronoun) otonom düğüm enjeksiyonu eklendi (Zero-Node Agent).
    [FAZ 3 ENTEGRASYONU]: İnne ve Kardeşleri (Amel Statüleri) cümlenin ana amili olarak AST'ye eklendi.
    [FAZ 4 ENTEGRASYONU]: Mekân Bildiren Harf-i Cerlerin Müteallak (Bağlantı) Prensibi ve Zero-Copula (Kainun_Virtual).
    [FAZ 5 ENTEGRASYONU]: Geriye Dönük Amil Tarayıcısı (Backward-Scan). Şibh-i Fiil (Fiilimsi) ve İlsak/Gaye bildiren Harf-i Cerlerin Zarf-ı Lağv/Mustakar olarak alt-ağaçlara bağlanması.
    [FAZ 7 ENTEGRASYONU]: Rabıta (Copula) Dinamikleri ve Fâ-i Füzâiyye/Sebebiyye (Dynamic Logic) Sentaksı.
    [FAZ 10 ENTEGRASYONU]: Dışsal OntoLex veri kaynağına dayalı Gayri Munsarif (Diptote) Mecrur Override kuralı.
    
    [FAZ 9 LITERATE CHUNKING]: Bilişsel Yükü (Cognitive Load) 4 birimin altında tutmak
    için monolitik parse algoritması hiyerarşik private fonksiyonlara ayrılmıştır.
    Her sentaktik düğümün Z3 SMT motorundaki ontolojik kısıt karşılığı (Muktazâ el-Hâl)
    pedagojik anlatılarla (LaTeX destekli) kod bloklarına dokunmuştur (Weaving).
    """
    def __init__(self):
        self.definite_article = ("al_", "el_") 
        self.dependency_graph = nx.DiGraph()
        
        # Kâtibî'nin Şemsiyye kipliklerini tetikleyecek sentaktik bağlar (Hal ve Şart)
        self.temporal_triggers = ["Rel_Hal", "Rel_Zarf_Zaman", "Rel_Shart"]
        # Kadiyye-i Şartiyye (Fasıl/Vasıl) tetikleyicileri
        self.atif_particles = ["wa", "fa", "aw", "summe", "am", "bal", "la", "lakin"]
        
        # [FAZ 5 ENTEGRASYONU] Kapsamlı Harf-i Cer ve Müteallak Ontolojisi
        self.harf_i_cerler = {
            "fi": "Zarfiyye",
            "ala": "Isti_la",
            "min": "Ibtida_i_Gaye",
            "ila": "Intiha_i_Gaye",
            "bi": "Ilsak_Alet",
            "li": "Ihtisas_Mulk",
            "inde": "Zarfiyye",
            "tahta": "Zarfiyye",
            "fawqa": "Zarfiyye",
            "beyne": "Zarfiyye",
            "khalf": "Zarfiyye",
            "amam": "Zarfiyye",
            "an": "Mucaveze"
        }

    def _is_definite(self, token: str) -> bool:
        return token.lower().startswith(self.definite_article)

    def _identify_primary_governors(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis]) -> Tuple[Optional[str], int, Optional[str], int]:
        """
        Kripke uzayının ontolojik sınırlarını çizen Ana Amilleri (Governors) tespit eder.
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
        .. pedagojik_anlati::
            İlm-i Ma'ânî'de 'Tevkîd' muhatabın şüphesini gidermek için önermeyi Modal Mantık'ta 
            'Zorunlu' (Necessity: $\\square P$) statüsüne yükseltir (Muktazâ el-Hâl).
            'Kasr' ise evrensel nicelik kısıtıdır; $\\forall x (Sifat(x) \\iff Mevsuf(x))$ mantıksal 
            çift yönlü gerektirmesini SMT motoruna mühürler.
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
        .. pedagojik_anlati::
            'Fâ-i Füzâiyye' ve 'Sebebiyye', klasik statik mantıkta (FOL) bir karşılığı olmayan 
            zaman/durum sıçramalarını (State Transition) ifade eder.
            Dinamik Mantıkta (Dynamic Logic) bir eylemin aniden diğerini var etmesi, SMT'de 
            ardışık Kripke dünyalarının ($W_0 \\implies W_1$) yaratılmasını zorunlu kılar.
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
        .. pedagojik_anlati::
            Harf-i Cerler ontolojik olarak tek başlarına var olamazlar. SMT evreninde, 
            Mekânsal Boyut (SpaceSort), eylemin (Amil) veya zımnî bir mevcudiyetin (Kainun_Virtual) 
            üzerine $\\exists e. \\text{LocatedIn}(e, \\text{Space}, \\text{World})$ 
            fonksiyonuyla bağlanmak (Müteallak) zorundadır.
            [FAZ 10] Gayri Munsarif kelimelerin harf-i cer sonrası aldığı fetha (-a) 
            harekesi, zımnî olarak majrur (Mecrur_Diptote_Override) kabul edilir.
        """
        if t1.lower() in self.harf_i_cerler:
            sem_type = self.harf_i_cerler[t1.lower()]
            rel_name = 'Muteallak_Mekan' if sem_type in ["Zarfiyye", "Isti_la"] else 'Muteallak_Harf'

            m2 = lexicon.get(t2)
            # Gayri Munsarif Override Kontrolü
            if m2 and getattr(m2, 'is_diptote', False):
                dependencies.append((t1, t2, 'Mecrur_Diptote_Override', 'Majrur'))
            else:
                dependencies.append((t1, t2, 'Harf_Mecrur', 'Majrur'))
            
            # Müteallak Amili Taraması: Sadece ana fiil değil, en yakın Şibh-i Fiil de amil olabilir.
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
                # Zarf-ı Lağv: Açıkça zikredilmiş bir amile (fiil veya şibh-i fiil) ontolojik kısıt ekler.
                dependencies.append((closest_amil, t1, rel_name, 'Zarf_Lagv'))
            else:
                # Zarf-ı Mustakar: Amil zikredilmemiştir. Zımnî 'Kainun' (Mevcut) sanal amili takdir edilir.
                dependencies.append(('Kainun_Virtual', t1, rel_name, 'Zarf_Mustakar'))
            return True
        return False

    def _apply_nominal_adjuncts(self, t1: str, t2: str, m1: Optional[MorphologicalAnalysis], m2: Optional[MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]]) -> bool:
        """
        .. pedagojik_anlati::
            İsim tamlamaları (İzafet) ve Sıfat uyumları, Z3 uzayında varlıkların 
            alt-kümelerini (Subset: $x \\in Y$) veya kesişimlerini (Intersection: $x \\in A \\cap B$) tanımlar.
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

    def _apply_conditional_logic(self, t1: str, t2: str, dependencies: List[Tuple[str, str, str, str]]) -> bool:
        """
        .. pedagojik_anlati::
            Şart edatları, mantıksal gerektirmeyi (Implication: $P \\implies Q$) AST yapısına mühürler.
        """
        if t1.lower() in ["in", "iza", "law", "amma"]:
            dependencies.append((t1, t2, "Rel_Shart", "Majzum"))
            return True
        return False

    def _resolve_adjacent_pairs(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]], amil_index: int) -> None:
        """
        [FAZ 9 CHUNKING MİMARİSİ]
        Doğrusal bağlamda yan yana gelen lafızların ontolojik kilitlerini oluşturur.
        Okunabilirliği artırmak ve çalışma belleğini korumak adına tüm kurallar
        kendi felsefi/matematiksel yalıtım alanlarına (Private Methods) aktarılmıştır.
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
            if self._apply_conditional_logic(t1, t2, dependencies): continue

    def _resolve_inne_scope(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis], dependencies: List[Tuple[str, str, str, str]], inne_token: Optional[str], inne_index: int, amil_token: Optional[str], amil_index: int) -> None:
        """
        .. pedagojik_anlati::
            'İnne'nin amel etmesi (Government), basit bir i'rab ataması değil; Kripke uzayında 
            önermeyi 'Zorunlu Hakikat' statüsüne mühürlemesidir. Nasb ve Ref' durumları, 
            SMT'de fail-meful karışıklığını önleyerek Ex Falso Quodlibet hatasını engeller.
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
        .. pedagojik_anlati::
            Rabıta (Gizli Copula) Üretimi. Deterministik SMT çözücüsü, isim cümlelerindeki
            boşluğu okuyamaz. Bu metod, görünmez bir sıfır-noktası (Zero-Copula Node) üreterek
            mübteda ile haber arasına mantıksal eşdeğerlik ($x = y$) veya aidiyet ($x \\in Y$) bağını kurar.
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
        .. pedagojik_anlati::
            Fiil amiline bağlı Fail, Meful ve Müstatir (gizli) zamir argümanlarını çözümler.
            Eğer cümlede açık bir fail yoksa, "Her eylemin bir faili vardır" nedensellik 
            aksiyomu gereği, fiilin morfolojisindeki gizli zamiri Z3'e varoluşsal değişken 
            ($\\exists x$) olarak zerk eder.
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

    def build_ast(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]]) -> nx.DiGraph:
        self.dependency_graph.clear()
         
        for token in tokens:
            self.dependency_graph.add_node(token)
            
        for amil, mamul, rel, irab in dependencies:
            if mamul not in self.dependency_graph:
                self.dependency_graph.add_node(mamul, virtual=True)
            if amil not in self.dependency_graph:
                self.dependency_graph.add_node(amil, virtual=True)
                
            self.dependency_graph.add_edge(amil, mamul, relation=rel, irab=irab)
            
        return self.dependency_graph
    
    def extract_temporal_conditions(self, ast: nx.DiGraph) -> Dict[str, str]:
        conditions = {}
        for u, v, data in ast.edges(data=True):
            if data.get('relation') in self.temporal_triggers:
                conditions[u] = v
        return conditions