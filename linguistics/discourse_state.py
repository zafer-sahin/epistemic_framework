from typing import List, Optional
from pydantic import BaseModel

class EntityMention(BaseModel):
    word: str
    ontologic_id: str
    timestamp: int

class DiscourseRegister:
    """
    Kapsamlı (Scoped) Söylem Belleği (Discourse Register).
    Z3 push/pop state mimarisiyle tam senkronize çalışır.
    İptal edilebilir (Defeasible) önermeler çürütüldüğünde, ilgili
    bağlam çerçevesi (Frame) yok edilerek bellek zehirlenmesi engellenir.
    """
    def __init__(self):
        # Stack mimarisi: index 0 her zaman Global (Kök) bağlamı temsil eder.
        self.frames: List[List[EntityMention]] = [[]]  
        self.clock: int = 0
        self.pronouns = {"huve", "hiye", "huma", "hum", "hunne"}

    def push_scope(self) -> None:
        """Z3.push() veya yeni bir diyalektik iddia açıldığında alt bağlam (Scope) yaratır."""
        self.frames.append([])

    def pop_scope(self) -> None:
        """Z3.pop() tetiklendiğinde veya iddia çürütüldüğünde varsayımsal bağlamı imha eder."""
        if len(self.frames) > 1:
            self.frames.pop()
        else:
            raise RuntimeError("[BELLEK HATASI] Global söylem çerçevesi (Frame 0) imha edilemez. Stack underflow.")

    def add_mention(self, word: str, ontologic_id: str) -> None:
        """Mevcut (Aktif) kapsama yeni bir ontolojik varlık ekler."""
        self.frames[-1].append(EntityMention(
            word=word, 
            ontologic_id=ontologic_id, 
            timestamp=self.clock
        ))
        self.clock += 1

    def resolve_pronoun(self, pronoun: str) -> Optional[str]:
        """
        Zamir (Anafora) tespiti. 
        Aktif çerçeveden başlayarak (LIFO) geçmişe doğru tarar ve ilk uyumlu varlığı döndürür.
        """
        pronoun_lower = pronoun.lower()
        if pronoun_lower not in self.pronouns:
            return None

        for frame in reversed(self.frames):
            if frame:
                return frame[-1].ontologic_id
                
        raise ValueError(f"LOGIC_FAILURE_PROBABILITY: HIGH - '{pronoun}' zamiri için geçmiş söylem belleği boş. Referans (Antecedent) tanımsız.")
        
    def clear_memory(self) -> None:
        """Mezhep (Usûl) profili değiştiğinde veya oturum sıfırlandığında belleği donanımsal olarak temizler."""
        self.frames = [[]]
        self.clock = 0