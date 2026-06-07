import networkx as nx
from typing import List, Dict, Tuple
from linguistics.sarf_parser import MorphologicalAnalysis

class NahivDependencyCompiler:
    """
    Arapça Sentaktik Bağımlılık Ağacını (Nahiv AST) üreten parser.
    Faz 10.2: Alt-ağaç (Sub-Tree) çözümleyicileri entegre edildi.
    Faz 2 - Adım 2.2: İlm-i Ma'ânî Tevkîd (Pekiştirme) edatlarının AST düğümüne bağlanması.
    Faz 2 - Adım 2.5: Takdim (Pre-positioning) ve İhtisas (Kasr) tespiti.
    Faz 2 - Adım 2.6: Kasr (Hasr) Operatörlerinde Yön Tespiti (Sıfat/Mevsuf) ve Harf-i Atıf (Fasıl/Vasıl) Entegrasyonu.
    [FAZ 1 ENTEGRASYONU]: Gayri Munsarif (Diptotes) kelimelerin cer durumundaki (fetha) i'rab istisnaları AST mantığına işlendi.
    [FAZ 2 ENTEGRASYONU]: Müstatir Zamir (Hidden Pronoun) otonom düğüm enjeksiyonu eklendi (Zero-Node Agent).
    İzafet (İsim Tamlaması), Sıfat-Mevsuf, Hal ve Atıf ilişkilerini saptayarak,
    ontolojik mesafe motoruna (L1) deterministik 'Edge'ler sağlar.
    """
    def __init__(self):
        self.definite_article = ("al_", "el_") # Harf-i Ta'rif
        self.dependency_graph = nx.DiGraph()
        # Kâtibî'nin Şemsiyye kipliklerini tetikleyecek sentaktik bağlar (Hal ve Şart)
        self.temporal_triggers = ["Rel_Hal", "Rel_Zarf_Zaman", "Rel_Shart"]
        # Kadiyye-i Şartiyye (Fasıl/Vasıl) tetikleyicileri
        self.atif_particles = ["wa", "fa", "aw", "summe", "am", "bal", "la", "lakin"]

    def _is_definite(self, token: str) -> bool:
        return token.lower().startswith(self.definite_article)

    def suggest_dependencies(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis]) -> List[Tuple[str, str, str, str]]:
        dependencies = []
        
        # 1. ANA CÜMLE (SENTENCE) ÇÖZÜMLEMESİ: FİİL KONTROLÜ (Erken Tespit)
        amil_token = None
        amil_index = -1
        for idx, token in enumerate(tokens):
            morph = lexicon.get(token)
            if morph and morph.ontologic_type == "Fiil":
                amil_token = token
                amil_index = idx
                break
                
        # 2. ALT-AĞAÇ (PHRASE/TERKİB) ÇÖZÜMLEMESİ (Sliding Window)
        for i in range(len(tokens) - 1):
            t1 = tokens[i]
            t2 = tokens[i+1]
            
            m1 = lexicon.get(t1)
            m2 = lexicon.get(t2)
            
            # [FAZ 2.2] Tevkîd Edatlarının Ana Yükleme/İsme Bağlanması
            if m1 and m1.ontologic_type == "Harf_Tevkid":
                dependencies.append((t2, t1, 'Tevkid_Modifier', 'None'))
                continue
            
            # [FAZ 2.6] Kasr Edatlarının (İnnemâ, İllâ) Yönlü Bağlanması
            if m1 and m1.ontologic_type == "Harf_Kasr":
                kasr_direction = 'Mevsuf_to_Sifat' # Varsayılan yön
                
                # İnnemâ genellikle cümlede son gelen öğeye (Te'hir) kısıtlama yapar.
                if t1.lower() == "innema":
                    if amil_index != -1 and i < amil_index:
                        # Fiilden önce gelirse, faili fiile veya mefulü fiile hasreder.
                        kasr_direction = 'Sifat_to_Mevsuf'
                    else:
                        kasr_direction = 'Mevsuf_to_Sifat'
                # İllâ (Nefy ile birlikte), kendisinden sonra gelene hasreder.
                elif t1.lower() == "illa":
                        kasr_direction = 'Sifat_to_Mevsuf'

                # Tuple aritesini korumak adına irab parametresi (4. indis) kasr yönünü taşımak için aşırı yüklenir (overloaded).
                dependencies.append((t2, t1, 'Kasr_Modifier', kasr_direction))
                continue
                
            # [FAZ 2.6] Kadiyye-i Şartiyye: Harf-i Atıf (Fasıl ve Vasıl) Matrisi
            if t1.lower() in self.atif_particles:
                if i > 0:
                    t_prev = tokens[i-1]
                    # Atıf bağlacı, bir önceki token ile bir sonraki token (Ma'tûf ve Ma'tûf aleyh) arasında Lüzum/İnad bağı kurar.
                    dependencies.append((t_prev, t2, 'Rel_Atif', t1.lower()))
                continue

            if m1 and m2 and m1.ontologic_type == "Ism" and m2.ontologic_type == "Ism":
                # İzafet (Mudaf - Mudaf İleyh) Matrisi
                # [FAZ 1 - GAYRİ MUNSARİF YAMASI]: Mudaf_Ilayh olan diptote kelime fetha (-a) ile bitebilir.
                is_diptote_majrur = getattr(m2, 'is_diptote', False) and t2.lower().endswith('a')
                if not self._is_definite(t1) and (self._is_definite(t2) or t2.lower().endswith(('in', 'i')) or is_diptote_majrur):
                    dependencies.append((t1, t2, 'Mudaf_MudafIlayh', 'Majrur'))
                
                # [FAZ 4 ENTEGRASYONU] Hal ve Zarf-ı Zaman (Vasfî Zaman Tetiği) - [ÖNCELİKLİ]
                # Hal, marife veya nekra bir fail/mefulün mansub (-an) niteliğidir. İ'rab uyumu aramaz.
                elif t2.lower().endswith('an') and m1.thematic_role in ["Agent", "Patient", "Action"]:
                    dependencies.append((t1, t2, "Rel_Hal", "Mansub"))

                # Sıfat-Mevsuf (Na't - Man'ut) Matrisi
                # [LOGIC FIX]: Sadece marife/nekra uyumu yetmez, kesin İ'rab uyumu şarttır.
                is_sifat_uyumu = False
                if self._is_definite(t1) == self._is_definite(t2):
                    if t1[-2:] == t2[-2:]:
                        is_sifat_uyumu = True
                    # [FAZ 1 - GAYRİ MUNSARİF YAMASI]: Triptote mevsuf (mecrur) + Diptote sıfat (mecrur '-a' ile)
                    elif getattr(m2, 'is_diptote', False) and t1.lower().endswith(('in', 'i')) and t2.lower().endswith('a'):
                        is_sifat_uyumu = True
                
                if is_sifat_uyumu:
                    dependencies.append((t1, t2, 'Sifat_Mevsuf', 'Tabi'))
                    
            # Şart Edatları (İn, İza, Lev, Amma)
            elif t1.lower() in ["in", "iza", "law", "amma"]:
                dependencies.append((t1, t2, "Rel_Shart", "Majzum"))
        
        # 3. İSİM CÜMLESİ (Kadiyye-i Hamliyye) ZİNCİRİ
        if not amil_token:
            ism_tokens = [t for t in tokens if lexicon.get(t) and lexicon.get(t).ontologic_type == "Ism"]
            
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
                    dependencies.append((haber, mubteda, 'Mubteda_Haber', 'Marfu'))
            
            return dependencies

        # 4. FİİL CÜMLESİ (Verbal Sentence) ZİNCİRİ
        has_explicit_fail = False
        for idx, token in enumerate(tokens):
            if token == amil_token: 
                continue
                
            morph = lexicon.get(token)
            if not morph or morph.ontologic_type != "Ism":
                continue

            is_diptote = getattr(morph, 'is_diptote', False)

            if token.lower().endswith('un') or (is_diptote and token.lower().endswith('u')):
                dependencies.append((amil_token, token, 'Fail', 'Marfu'))
                has_explicit_fail = True
            elif token.lower().endswith('an') or (is_diptote and token.lower().endswith('a')):
                # Hal olarak bağlanmış bir kelime tekrar Meful olarak bağlanmamalıdır.
                # [FAZ 1 - GAYRİ MUNSARİF KORUMASI]: Eğer kelime diptote ise ve zaten Majrur (Mudaf_Ilayh) olarak bağlandıysa Meful OLAMAZ.
                is_hal = any(rel == 'Rel_Hal' and mamul == token for _, mamul, rel, _ in dependencies)
                is_majrur = any(mamul == token and irab == 'Majrur' for _, mamul, rel, irab in dependencies)
                
                if not is_hal and not is_majrur:
                    # [FAZ 2.5] İlm-i Ma'ânî İhtisas (Takdim) Kontrolü
                    # Eğer meful, fiilden (amil) önce gelmişse bu bir İhtisas/Kasr durumudur.
                    if idx < amil_index:
                        dependencies.append((amil_token, token, 'Rel_Ihtisas', 'Mansub'))
                    else:
                        dependencies.append((amil_token, token, 'Meful', 'Mansub'))
            elif token.lower().endswith(('in', 'i')):
                # Mudaf İleyh veya Atıf (Ma'tûf) ile alt ağaca bağlananlar ana amile majrur olarak bağlanmamalıdır.
                is_sub_tree_child = any((rel == 'Mudaf_MudafIlayh' or rel == 'Rel_Atif') and t2 == token for _, t2, rel, _ in dependencies)
                if not is_sub_tree_child:
                    dependencies.append((amil_token, token, 'Majrur', 'Majrur'))

        # [FAZ 2 ENTEGRASYONU] Müstatir (Gizli) Zamir Tespiti ve AST'ye Zero-Node Enjeksiyonu
        if amil_token and not has_explicit_fail:
            amil_morph = lexicon.get(amil_token)
            hidden_pronoun = getattr(amil_morph, 'hidden_pronoun', None)
            if hidden_pronoun:
                # Gerçek metinde olmayan sanal bir fail (Agent) düğümü yaratılır ve fiile bağlanır.
                # IlmWadAdapter bu zamiri gördüğünde DiscourseRegister üzerinden HPSG eşleşmesiyle çözecektir.
                dependencies.append((amil_token, hidden_pronoun, 'Fail', 'Marfu_Virtual'))
                    
        return dependencies

    def build_ast(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]]) -> nx.DiGraph:
        self.dependency_graph.clear()
        
        # Orijinal tokenları grafiğe ekle
        for token in tokens:
            self.dependency_graph.add_node(token)
            
        for amil, mamul, rel, irab in dependencies:
            # [FAZ 2 YAMASI] Sanal (Zero-Node) zamirler (Örn: 'huve') tokens listesinde olmadığı için hata vermemesi adına açıkça eklenir.
            if mamul not in self.dependency_graph:
                self.dependency_graph.add_node(mamul, virtual=True)
            if amil not in self.dependency_graph:
                self.dependency_graph.add_node(amil, virtual=True)
                
            self.dependency_graph.add_edge(amil, mamul, relation=rel, irab=irab)
            
        return self.dependency_graph
    
    def extract_temporal_conditions(self, ast: nx.DiGraph) -> Dict[str, str]:
        """
        AST üzerinden Vasfî Zamanı (t_vasfi) tetikleyen düğümleri çeker.
        Eğer bir varlığa Rel_Hal veya Rel_Shart bağlanmışsa, o varlık SMT katmanında
        'Meşrûta-i Âmme' veya 'Örfiyye-i Âmme' matrisine sokulmalıdır.
        """
        conditions = {}
        for u, v, data in ast.edges(data=True):
            if data.get('relation') in self.temporal_triggers:
                conditions[u] = v  # u: Zât (Özne), v: Vasıf (Şart/Hal)
        return conditions