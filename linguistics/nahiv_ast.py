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
    [FAZ 3 ENTEGRASYONU]: İnne ve Kardeşleri (Amel Statüleri) cümlenin ana amili olarak AST'ye eklendi.
    [FAZ 4 ENTEGRASYONU]: Mekân Bildiren Harf-i Cerlerin Müteallak (Bağlantı) Prensibi, Zarf-ı Mustakar 
    ve Zarf-ı Lağv matrisleri ile Zero-Copula (Kainun_Virtual) AST'ye entegre edildi.
    """
    def __init__(self):
        self.definite_article = ("al_", "el_") # Harf-i Ta'rif
        self.dependency_graph = nx.DiGraph()
        # Kâtibî'nin Şemsiyye kipliklerini tetikleyecek sentaktik bağlar (Hal ve Şart)
        self.temporal_triggers = ["Rel_Hal", "Rel_Zarf_Zaman", "Rel_Shart"]
        # Kadiyye-i Şartiyye (Fasıl/Vasıl) tetikleyicileri
        self.atif_particles = ["wa", "fa", "aw", "summe", "am", "bal", "la", "lakin"]
        # [FAZ 4 ENTEGRASYONU] Mekân/Zaman Harf-i Cer ve Zarfları
        self.mekan_zarflari = ["fi", "ala", "min", "ila", "bi", "li", "inde", "tahta", "fawqa", "beyne", "khalf", "amam"]

    def _is_definite(self, token: str) -> bool:
        return token.lower().startswith(self.definite_article)

    def suggest_dependencies(self, tokens: List[str], lexicon: Dict[str, MorphologicalAnalysis]) -> List[Tuple[str, str, str, str]]:
        dependencies = []
        
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
                
        for i in range(len(tokens) - 1):
            t1 = tokens[i]
            t2 = tokens[i+1]
            
            m1 = lexicon.get(t1)
            m2 = lexicon.get(t2)
            
            if m1 and m1.ontologic_type == "Harf_Tevkid":
                dependencies.append((t2, t1, 'Tevkid_Modifier', 'None'))
                continue
            
            if m1 and m1.ontologic_type == "Harf_Kasr":
                kasr_direction = 'Mevsuf_to_Sifat'
                if t1.lower() == "innema":
                    if amil_index != -1 and i < amil_index:
                        kasr_direction = 'Sifat_to_Mevsuf'
                    else:
                        kasr_direction = 'Mevsuf_to_Sifat'
                elif t1.lower() == "illa":
                        kasr_direction = 'Sifat_to_Mevsuf'

                dependencies.append((t2, t1, 'Kasr_Modifier', kasr_direction))
                continue
                
            if t1.lower() in self.atif_particles:
                if i > 0:
                    t_prev = tokens[i-1]
                    dependencies.append((t_prev, t2, 'Rel_Atif', t1.lower()))
                continue
                
            # [FAZ 4 ENTEGRASYONU] Harf-i Cer, Mecrur ve Müteallak Bağıntısı
            if t1.lower() in self.mekan_zarflari:
                dependencies.append((t1, t2, 'Harf_Mecrur', 'Majrur'))
                
                if amil_token:
                    # Zarf-ı Lağv: Cümlede açıkça zikredilmiş bir eyleme (amile) mekânsal kısıt ekler.
                    dependencies.append((amil_token, t1, 'Muteallak_Mekan', 'Zarf_Lagv'))
                else:
                    # Zarf-ı Mustakar: Amil zikredilmemiştir. Zımnî 'Kainun' (Mevcut/Karar Kılmış) amili takdir edilir.
                    dependencies.append(('Kainun_Virtual', t1, 'Muteallak_Mekan', 'Zarf_Mustakar'))
                continue

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
                    
            elif t1.lower() in ["in", "iza", "law", "amma"]:
                dependencies.append((t1, t2, "Rel_Shart", "Majzum"))
        
        if inne_token:
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

        if not amil_token and not inne_token:
            # [FAZ 4 ENTEGRASYONU] Zarf-ı Mustakar'ın Kadiyye-i Hamliyye üzerindeki otoritesi
            has_zarf_mustakar = any(rel == 'Muteallak_Mekan' and am == 'Kainun_Virtual' for am, ma, rel, ir in dependencies)
            ism_tokens = [t for t in tokens if lexicon.get(t) and lexicon.get(t).ontologic_type == "Ism"]
            
            if has_zarf_mustakar and len(ism_tokens) >= 1:
                mubteda = ism_tokens[0]
                # Kainun_Virtual, varoluşsal bir yüklem (Haber) olarak Mübteda'ya bağlanır
                dependencies.append(('Kainun_Virtual', mubteda, 'Mubteda_Haber', 'Marfu_Virtual'))
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
                    dependencies.append((haber, mubteda, 'Mubteda_Haber', 'Marfu'))
            
            return dependencies
            
        if not amil_token and inne_token:
            return dependencies 

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
                is_majrur = any(mamul == token and irab == 'Majrur' for _, mamul, rel, irab in dependencies)
                is_inne_ism = any(rel == 'Amel_Inne_Ism' and mamul == token for _, mamul, rel, _ in dependencies)
                
                if not is_hal and not is_majrur and not is_inne_ism:
                    if idx < amil_index:
                        dependencies.append((amil_token, token, 'Rel_Ihtisas', 'Mansub'))
                    else:
                        dependencies.append((amil_token, token, 'Meful', 'Mansub'))
            elif token.lower().endswith(('in', 'i')):
                # [FAZ 4 YAMASI] Harf_Mecrur bağına girenler ana fiile Majrur olarak doğrudan bağlanamaz. Onlar Harf üzerinden Müteallak olurlar.
                is_sub_tree_child = any((rel == 'Mudaf_MudafIlayh' or rel == 'Rel_Atif' or rel == 'Harf_Mecrur') and t2 == token for _, t2, rel, _ in dependencies)
                if not is_sub_tree_child:
                    dependencies.append((amil_token, token, 'Majrur', 'Majrur'))

        if amil_token and not has_explicit_fail:
            amil_morph = lexicon.get(amil_token)
            hidden_pronoun = getattr(amil_morph, 'hidden_pronoun', None)
            if hidden_pronoun:
                dependencies.append((amil_token, hidden_pronoun, 'Fail', 'Marfu_Virtual'))
                    
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