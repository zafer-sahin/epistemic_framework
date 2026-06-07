from typing import List, Optional, Literal, Dict
from pydantic import BaseModel
from enum import IntEnum
from core.exceptions import ContextPoisoningError

class DenialLevel(IntEnum):
    KHALI_AL_ZIHN = 0  # Zihin boş, nötr durum. Tevkîd (pekiştirme) yasaktır.
    MUTAREDDIT = 1     # Şüphe durumu (Men' saldırısı). Tevkîd kullanımı caiz/önerilendir (Hasan).
    MUNKIR = 2         # Kesin inkar durumu (Nakz saldırısı). Tevkîd zorunludur (Vâcib).

class EntityMention(BaseModel):
    word: str
    ontologic_id: str
    timestamp: int
    agent: Literal["Mujib", "Sail"]
    sealed_namespace: str  # [FAZ 4] Yalıtım Zırhı: Hangi usûl uzayında (Namespace) üretildiğini mühürler.
    # [FAZ 2 ENTEGRASYONU]: HPSG (Cinsiyet ve Sayı) Kısıt Yapıları
    gender: Optional[str] = None
    number: Optional[str] = None

class DiscourseRegister:
    """
    Çok-Aktörlü (Multi-Agent) Kapsamlı Söylem Belleği (Discourse Register).
    Faz 4 - Adım 1: Sâil ve Mucîb için mutlak Semantik Yalıtım (Context Sealing) zırhı.
    Faz 2 - Adım 1: Epistemik Durum (Muktazâ el-Hâl) matrisi.
    [FAZ 2 ENTEGRASYONU]: HPSG Kısıtları ile Discourse Representation Theory (DRT) Anaphora çözümlemesi.
    """
    def __init__(self):
        # Stack mimarisi: index 0 her zaman Global (Kök) bağlamı temsil eder.
        self.mujib_frames: List[List[EntityMention]] = [[]]  
        self.sail_frames: List[List[EntityMention]] = [[]]  
        self.clock: int = 0
        
        # [FAZ 2 ENTEGRASYONU]: Munfasıl/Muttasıl Zamirlerin HPSG Cinsiyet ve Sayı Matrisi
        self.pronouns = {
            "huve": {"gender": "Muzekker", "number": "Mufred"},
            "hiye": {"gender": "Muennes", "number": "Mufred"},
            "huma": {"gender": None, "number": "Tesniye"},  # Tesniye (İkil) her iki cinsiyeti de kapsayabilir.
            "hum": {"gender": "Muzekker", "number": "Cemi"},
            "hunne": {"gender": "Muennes", "number": "Cemi"}
        }
        
        self.active_agent: Literal["Mujib", "Sail"] = "Mujib" # Varsayılan aktör iddia sahibidir (Mucîb)
        
        # [FAZ 2.1] Epistemik Durum Matrisi (Muktazâ el-Hâl)
        self.epistemic_state: Dict[Literal["Mujib", "Sail"], DenialLevel] = {
            "Mujib": DenialLevel.KHALI_AL_ZIHN,
            "Sail": DenialLevel.KHALI_AL_ZIHN
        }

    def set_agent(self, agent: Literal["Mujib", "Sail"]) -> None:
        """Diyalektik sırasına göre aktif aktörü (Sâil veya Mucîb) değiştirir."""
        self.active_agent = agent

    def update_epistemic_state(self, agent: Literal["Mujib", "Sail"], level: DenialLevel) -> None:
        """İlm-i Ma'ânî gereği muhatabın inkâr derecesini günceller."""
        if level < self.epistemic_state[agent]:
            # Diyalektikte inkar derecesi (şüphe giderilmedikçe) geriye düşemez.
            return
        self.epistemic_state[agent] = level

    def get_opponent_epistemic_state(self) -> DenialLevel:
        """Aktif aktörün muhatabının epistemik durumunu döndürür (Muktazâ el-Hâl denetimi için)."""
        opponent = "Sail" if self.active_agent == "Mujib" else "Mujib"
        return self.epistemic_state[opponent]

    def push_scope(self) -> None:
        """Z3.push() veya yeni bir diyalektik iddia açıldığında, sadece aktif aktörün alt bağlamını yaratır."""
        if self.active_agent == "Mujib":
            self.mujib_frames.append([])
        else:
            self.sail_frames.append([])

    def pop_scope(self) -> None:
        """Z3.pop() tetiklendiğinde veya iddia çürütüldüğünde aktif aktörün varsayımsal bağlamını imha eder."""
        frames = self.mujib_frames if self.active_agent == "Mujib" else self.sail_frames
        
        if len(frames) > 1:
            frames.pop()
        else:
            raise RuntimeError(f"[BELLEK HATASI] {self.active_agent} global söylem çerçevesi (Frame 0) imha edilemez. Stack underflow.")

    def add_mention(self, word: str, ontologic_id: str, active_namespace: str, gender: Optional[str] = None, number: Optional[str] = None) -> None:
        """Aktif aktörün kapsamına, aktif uzayın mührüyle (namespace) yeni bir ontolojik varlık ataması yapar."""
        mention = EntityMention(
            word=word, 
            ontologic_id=ontologic_id, 
            timestamp=self.clock,
            agent=self.active_agent,
            sealed_namespace=active_namespace,
            gender=gender,
            number=number
        )
        frames = self.mujib_frames if self.active_agent == "Mujib" else self.sail_frames
        frames[-1].append(mention)
        self.clock += 1

    def resolve_pronoun(self, pronoun: str, enforcement_namespace: Optional[str] = None) -> Optional[str]:
        """
        [FAZ 4] Aktör-Spesifik ve Uzay-Korumalı Zamir (Anafora) tespiti.
        [FAZ 2 ENTEGRASYONU] HPSG Feature Structures (Cinsiyet ve Sayı) üzerinden DRT Geriye Dönük Çözümlemesi.
        Sadece konuşan aktörün kendi yığıtındaki (LIFO) geçmiş kabulleri (Müsellemat) taranır.
        Eğer çapraz sorguda (Mu'aradah) bağlam zehirlenmesi saptanırsa motor durdurulur.
        """
        pronoun_lower = pronoun.lower()
        if pronoun_lower not in self.pronouns:
            return None

        target_gender = self.pronouns[pronoun_lower]["gender"]
        target_number = self.pronouns[pronoun_lower]["number"]

        frames = self.mujib_frames if self.active_agent == "Mujib" else self.sail_frames

        # Yığıt içerisinde sondan başa (LIFO) doğru ilerleyerek en yakın mantıksal uyumu (Unification) arar.
        for frame in reversed(frames):
            # [LOGIC FIX]: Yalnızca frame'in son elemanı değil, frame içindeki tüm aktörler sondan başa taranmalıdır.
            for resolved_mention in reversed(frame):
                
                # Context Sealing (Bağlam Zehirlenmesi Koruması)
                if enforcement_namespace and resolved_mention.sealed_namespace != enforcement_namespace:
                    raise ContextPoisoningError(
                        f"LOGIC_FAILURE_PROBABILITY: HIGH - Context Poisoning (Bağlam Zehirlenmesi) Tespit Edildi! "
                        f"'{pronoun}' zamiri '{resolved_mention.sealed_namespace}' uzayında üretildi, "
                        f"ancak şu an '{enforcement_namespace}' uzayına sızmaya/bağlanmaya çalışıyor. Mu'aradah çapraz izolasyonu ihlal edildi."
                    )

                # [FAZ 2] HPSG Kısıt Doğrulaması (Cinsiyet ve Sayı Uyumu)
                if target_gender and resolved_mention.gender and target_gender != resolved_mention.gender:
                    continue  # Cinsiyet uyuşmazlığı, önceki adaylara bak.
                
                if target_number and resolved_mention.number and target_number != resolved_mention.number:
                    continue  # Sayı uyuşmazlığı, önceki adaylara bak.
               
                return resolved_mention.ontologic_id
                
        raise ValueError(f"LOGIC_FAILURE_PROBABILITY: HIGH - '{pronoun}' zamiri için {self.active_agent} geçmiş söylem belleği boş veya ontolojik kısıtlar (HPSG) uyumsuz. Referans (Antecedent) tanımsız.")
        
    def clear_memory(self) -> None:
        """Mezhep (Usûl) profili değiştiğinde veya diyalektik oturum sıfırlandığında belleği donanımsal olarak temizler."""
        self.mujib_frames = [[]]
        self.sail_frames = [[]]
        self.clock = 0
        self.active_agent = "Mujib"
        self.epistemic_state = {"Mujib": DenialLevel.KHALI_AL_ZIHN, "Sail": DenialLevel.KHALI_AL_ZIHN}