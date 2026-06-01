from typing import List, Dict, Tuple
from linguistics.sarf_parser import MorphologicalAnalysis

class NahivDependencyCompiler:
    """
    Arapça Sentaktik Bağımlılık Ağacını (Nahiv AST) üreten parser.
    Faz 10.2: Alt-ağaç (Sub-Tree) çözümleyicileri entegre edildi.
    İzafet (İsim Tamlaması) ve Sıfat-Mevsuf ilişkilerini saptayarak,
    ontolojik mesafe motoruna (L1) deterministik 'Edge'ler sağlar.
    """
    def __init__(self):
        self.definite_article = ("al_", "el_") # Harf-i Ta'rif

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
            
            if m1 and m2 and m1.ontologic_type == "Ism" and m2.ontologic_type == "Ism":
                # İzafet (Mudaf - Mudaf İleyh) Matrisi
                # Kural: 1. İsim Nekra (Belirsiz), 2. İsim Marife veya Mecrur (Kasrateyn '-in' veya Kasra '-i')
                if not self._is_definite(t1) and (self._is_definite(t2) or t2.lower().endswith(('in', 'i'))):
                    dependencies.append((t1, t2, 'Mudaf_MudafIlayh', 'Majrur'))
                
                # Sıfat-Mevsuf (Na't - Man'ut) Matrisi
                elif self._is_definite(t1) == self._is_definite(t2):
                    dependencies.append((t1, t2, 'Sifat_Mevsuf', 'Tabi'))

        # 2. ANA CÜMLE (SENTENCE) ÇÖZÜMLEMESİ: FİİL KONTROLÜ
        amil_token = None
        for token in tokens:
            morph = lexicon.get(token)
            if morph and morph.ontologic_type == "Fiil":
                amil_token = token
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
        for token in tokens:
            if token == amil_token: 
                continue
                
            morph = lexicon.get(token)
            if not morph or morph.ontologic_type != "Ism":
                continue

            if token.lower().endswith('un'):
                dependencies.append((amil_token, token, 'Fail', 'Marfu'))
            elif token.lower().endswith('an'):
                dependencies.append((amil_token, token, 'Meful', 'Mansub'))
            elif token.lower().endswith(('in', 'i')):
                is_sub_tree_child = any(rel == 'Mudaf_MudafIlayh' and t2 == token for _, t2, rel, _ in dependencies)
                if not is_sub_tree_child:
                    dependencies.append((amil_token, token, 'Majrur', 'Majrur'))
                    
        return dependencies