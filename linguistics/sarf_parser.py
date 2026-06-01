from typing import Dict, List, Any
from pydantic import BaseModel

class MorphologicalAnalysis(BaseModel):
    original_word: str
    root: str           
    pattern: str        
    ontologic_type: str 

class SarfEngine:
    """
    Üretken Morfoloji Motoru ('İlm-i Sarf).
    Faz 10.4: Mudaf (Tamlanan) kelimelerin tenvin düşmesi (İ'rab)
    durumu için deterministik Fallback yaması eklendi.
    """
    def __init__(self):
        self.vowels = {'a', 'e', 'i', 'ı', 'o', 'ö', 'u', 'ü'}
        self.harf_set = {"fi", "min", "ila", "ala", "bi", "li", "wa", "au", "summe", "la", "in"}
        
        self.wazan_matrix = {
            "CaCaCa": ("Fa'ala", "Fiil", [0, 2, 4]),       
            "yaCCiCu": ("Yaf'ilu", "Fiil", [2, 3, 5]),     
            "yaCCaCu": ("Yaf'alu", "Fiil", [2, 3, 5]),     
            "yaCCuCu": ("Yaf'ulu", "Fiil", [2, 3, 5]),     
            
            "CaaCa": ("Fa'ala_Ecvef", "Fiil", [0, 'W_Y', 3]),   
            "yaCooCu": ("Yaf'ulu_Ecvef", "Fiil", [2, 'W', 4]),   
            "yaCeeCu": ("Yaf'ilu_Ecvef", "Fiil", [2, 'Y', 4]),   
            "CaCaa": ("Fa'ala_Nakis", "Fiil", [0, 2, 'W_Y']),    
            
            "iCCaCaCa": ("Ifta'ala_Ibdal", "Fiil", ['IBDAL', 4, 6]), 
            
            "CaCiCun": ("Fâ'ilun", "Ism", [0, 2, 4]),      
            "maCCuCun": ("Maf'ûlun", "Ism", [2, 3, 5]),    
        }

    def _generate_structural_signature(self, word: str) -> str:
        sig = ""
        word_lower = word.lower()
        length = len(word_lower)
        
        for i, char in enumerate(word_lower):
            if char in self.vowels:
                sig += char
            elif char in ['m', 'y', 'a', 't'] and i == 0:
                sig += char
            elif char == 'n' and i == length - 1 and word_lower[i-1] in ['u', 'a', 'i']:
                sig += char
            else:
                sig += 'C'
        return sig

    def _extract_root(self, word: str, root_commands: List[Any]) -> str:
        word_lower = word.lower()
        resolved_root = ""
        
        try:
            for cmd in root_commands:
                if isinstance(cmd, int):
                    resolved_root += word_lower[cmd]
                elif cmd == 'W_Y':
                    resolved_root += "w" 
                elif cmd == 'W':
                    resolved_root += "w"
                elif cmd == 'Y':
                    resolved_root += "y"
                elif cmd == 'IBDAL':
                    if word_lower[1] == 't' and word_lower[2] == 't':
                        resolved_root += "w"
                    elif word_lower[1] == 'd' and word_lower[2] == 'd':
                        resolved_root += "d"
                    else:
                        resolved_root += word_lower[1] 
                else:
                    raise ValueError(f"Geçersiz fonolojik komut: {cmd}")
                    
            return resolved_root
        except IndexError:
            raise ValueError(f"[İ'LÂL HATASI] '{word}' kelimesinin yapısal indeksi taştı.")

    def _derive_morphology(self, word: str) -> MorphologicalAnalysis:
        word_lower = word.lower()
        
        if word_lower in self.harf_set:
            return MorphologicalAnalysis(original_word=word_lower, root=word_lower, pattern="Harf", ontologic_type="Harf")

        signature = self._generate_structural_signature(word_lower)
        
        if signature in self.wazan_matrix:
            vezin, ont_type, root_commands = self.wazan_matrix[signature]
            extracted_root = self._extract_root(word_lower, root_commands)
            return MorphologicalAnalysis(
                original_word=word_lower,
                root=extracted_root,
                pattern=vezin,
                ontologic_type=ont_type
            )
            
        # 3. İ'rab Fallback (Câmid İsimler ve Mudaf Formları)
        # Tenvinli (Marife/Nekra İsim)
        if word_lower.endswith(("un", "an", "in")):
            camid_root = word_lower[:-2] 
            return MorphologicalAnalysis(
                original_word=word_lower, root=camid_root, pattern="Alem/Camid_Munevven", ontologic_type="Ism"
            )
        # Tenvinsiz (Mudaf veya Gayr-ı Munsarif)
        elif word_lower.endswith(("u", "a", "i")):
            camid_root = word_lower[:-1]
            return MorphologicalAnalysis(
                original_word=word_lower, root=camid_root, pattern="Alem/Camid_Mudaf", ontologic_type="Ism"
            )

        raise ValueError(f"[SARF ÇÖKÜŞÜ] '{word}' (İmza: {signature}) kelimesi ontolojik evrende tanımlanamadı.")

    def derive_lexicon(self, words: List[str]) -> Dict[str, MorphologicalAnalysis]:
        derived_lexicon = {}
        for word in words:
            derived_lexicon[word] = self._derive_morphology(word)
        return derived_lexicon