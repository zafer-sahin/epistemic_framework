import networkx as nx
from typing import List, Dict, Tuple
from linguistics.sarf_parser import MorphologicalAnalysis

class NahivDependencyCompiler:
    """
    Arapça Sentaktik Bağımlılık Ağacını (Nahiv AST) üreten parser.
    Faz 10.2: Alt-ağaç (Sub-Tree) çözümleyicileri entegre edildi.
    Faz 2 - Adım 2.2: İlm-i Ma'ânî Tevkîd (Pekiştirme) edatlarının AST düğümüne bağlanması.
    Faz 2 - Adım 2.5: Takdim (Pre-positioning) ve İhtisas (Kasr) tespiti.
    İzafet (İsim Tamlaması), Sıfat-Mevsuf ve Hal ilişkilerini saptayarak,
    ontolojik mesafe motoruna (L1) deterministik 'Edge'ler sağlar.
    """
    def __init__(self):
        self.definite_article = ("al_", "el_") # Harf-i Ta'rif
        self.dependency_graph = nx.DiGraph()
        # Kâtibî'nin Şemsiyye kipliklerini tetikleyecek sentaktik bağlar (Hal ve Şart)
        self.temporal_triggers = ["Rel_Hal", "Rel_Zarf_Zaman", "Rel_Shart"]

    def _is_definite(self, token: str) -> bool:
        return token.lower().startswith(self.definite_article)

    def suggest_dependencies(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis]) -> List[Tuple[str, str, str, str]]:
        dependencies = []
        
        # 1. ALT-AĞAÇ (PHRASE/TERKİB) ÇÖZÜMLEMESİ (Sliding Window)
        for i in range(len(tokens) - 1):
            t1 = tokens[i]
            t2 = tokens[i+1]
            
            m1 = lexicon.get(t1)
            m2 = lexicon.get(t2)
            
            # [FAZ 2.2] Tevkîd Edatlarının Ana Yükleme/İsme Bağlanması
            if m1 and m1.ontologic_type == "Harf_Tevkid":
                dependencies.append((t2, t1, 'Tevkid_Modifier', 'None'))
                continue
            
            # [FAZ 2.5] Kasr Edatlarının (İnnemâ, İllâ) Bağlanması
            if m1 and m1.ontologic_type == "Harf_Kasr":
                dependencies.append((t2, t1, 'Kasr_Modifier', 'None'))
                continue
            
            if m1 and m2 and m1.ontologic_type == "Ism" and m2.ontologic_type == "Ism":
                # İzafet (Mudaf - Mudaf İleyh) Matrisi
                if not self._is_definite(t1) and (self._is_definite(t2) or t2.lower().endswith(('in', 'i'))):
                    dependencies.append((t1, t2, 'Mudaf_MudafIlayh', 'Majrur'))
                
                # [FAZ 4 ENTEGRASYONU] Hal ve Zarf-ı Zaman (Vasfî Zaman Tetiği) - [ÖNCELİKLİ]
                # Hal, marife veya nekra bir fail/mefulün mansub (-an) niteliğidir. İ'rab uyumu aramaz.
                elif t2.lower().endswith('an') and m1.thematic_role in ["Agent", "Patient", "Action"]:
                    dependencies.append((t1, t2, "Rel_Hal", "Mansub"))

                # Sıfat-Mevsuf (Na't - Man'ut) Matrisi
                # [LOGIC FIX]: Sadece marife/nekra uyumu yetmez, kesin İ'rab (son iki harf: un/an/in) uyumu şarttır.
                elif self._is_definite(t1) == self._is_definite(t2) and t1[-2:] == t2[-2:]:
                    dependencies.append((t1, t2, 'Sifat_Mevsuf', 'Tabi'))
                    
            # Şart Edatları (İn, İza, Lev, Amma)
            elif t1.lower() in ["in", "iza", "law", "amma"]:
                dependencies.append((t1, t2, "Rel_Shart", "Majzum"))

        # 2. ANA CÜMLE (SENTENCE) ÇÖZÜMLEMESİ: FİİL KONTROLÜ
        amil_token = None
        amil_index = -1
        for idx, token in enumerate(tokens):
            morph = lexicon.get(token)
            if morph and morph.ontologic_type == "Fiil":
                amil_token = token
                amil_index = idx
                break
        
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
        for idx, token in enumerate(tokens):
            if token == amil_token: 
                continue
                
            morph = lexicon.get(token)
            if not morph or morph.ontologic_type != "Ism":
                continue

            if token.lower().endswith('un'):
                dependencies.append((amil_token, token, 'Fail', 'Marfu'))
            elif token.lower().endswith('an'):
                # Hal olarak bağlanmış bir kelime tekrar Meful olarak bağlanmamalıdır.
                is_hal = any(rel == 'Rel_Hal' and mamul == token for _, mamul, rel, _ in dependencies)
                if not is_hal:
                    # [FAZ 2.5] İlm-i Ma'ânî İhtisas (Takdim) Kontrolü
                    # Eğer meful, fiilden (amil) önce gelmişse bu bir İhtisas/Kasr durumudur.
                    if idx < amil_index:
                        dependencies.append((amil_token, token, 'Rel_Ihtisas', 'Mansub'))
                    else:
                        dependencies.append((amil_token, token, 'Meful', 'Mansub'))
            elif token.lower().endswith(('in', 'i')):
                is_sub_tree_child = any(rel == 'Mudaf_MudafIlayh' and t2 == token for _, t2, rel, _ in dependencies)
                if not is_sub_tree_child:
                    dependencies.append((amil_token, token, 'Majrur', 'Majrur'))
                    
        return dependencies

    def build_ast(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]]) -> nx.DiGraph:
        self.dependency_graph.clear()
        for token in tokens:
            self.dependency_graph.add_node(token)
            
        for amil, mamul, rel, irab in dependencies:
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