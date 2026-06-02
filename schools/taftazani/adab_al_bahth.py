import z3
from typing import List, Dict, Any, Optional, Literal
from core.logic_engine import AristotelianSolver
from linguistics.discourse_state import DiscourseRegister

class AdabAlBahthEngine:
    """
    Taftâzânî ve Cürcânî temelli Münazara Sonlu Durum Makinesi (FSM).
    Faz 4 - Adım 2: Statik otomat yapısı, karşılıklı etkileşimli ve durum izoleli (Stateful)
    bir diyalektik protokole dönüştürülmüştür.
    """
    def __init__(self, solver: AristotelianSolver, discourse: DiscourseRegister):
        self.solver = solver
        self.discourse = discourse
        
        # FSM Durum Değişkenleri
        self.current_state: Literal["AWAITING_CLAIM", "AWAITING_EVIDENCE", "AWAITING_ATTACK", "RESOLVED"] = "AWAITING_CLAIM"
        self.active_claim: Optional[str] = None
        self.active_premises: List[str] = []

    def submit_claim(self, claim: str) -> Dict[str, Any]:
        """Mucîb tarafından iddia (Da'vâ) sunumu."""
        if self.current_state != "AWAITING_CLAIM":
            raise ValueError(f"[DİYALEKTİK İHLAL] Mevcut durum '{self.current_state}'. Yeni iddia sunulamaz.")
            
        self.discourse.set_agent("Mujib")
        
        # İddia ontolojik bir aksiyom mu? (Bedîhiyyât kontrolü)
        is_already_valid = self.solver.verify_syllogism([], claim)
        
        if is_already_valid:
            self.current_state = "RESOLVED"
            return {"status": "TAHSIL_I_HASIL", "message": "İddia ontolojik bir aksiyomdur (Tahsîl-i Hâsıl), ispat gerektirmez."}
        
        self.active_claim = claim
        self.current_state = "AWAITING_EVIDENCE"
        
        # Sâil otomatik olarak varsayılan iddiayı reddeder (Men')
        self.discourse.set_agent("Sail")
        return {"status": "MEN_ACCEPTED", "message": "Sâil iddiayı kabul etmedi (Men'). Mucîb delil getirmelidir."}

    def submit_evidence(self, premises: List[str]) -> Dict[str, Any]:
        """Mucîb tarafından delil (İstidlal) sunumu."""
        if self.current_state != "AWAITING_EVIDENCE":
            raise ValueError("[DİYALEKTİK İHLAL] Şu an delil sunma aşamasında değilsiniz.")
        
        self.discourse.set_agent("Mujib")
        
        # Mantıksal ve Dilbilimsel uzayda eşzamanlı Mucîb kapsamı (Frame) açılışı
        self.solver.solver.push()
        self.discourse.push_scope()
        
        try:
            for p in premises:
                self.solver.solver.add(self.solver.builder.parse(p))
            is_consistent = (self.solver.solver.check() == z3.sat)
        except Exception as e:
            self.solver.solver.pop()
            self.discourse.pop_scope()
            return {"status": "ERROR", "message": f"Delil Derleme Hatası (Sentaks/Arite): {e}"}
        
        if not is_consistent:
            self.solver.solver.pop()
            self.discourse.pop_scope()
            self.current_state = "RESOLVED"
            return {"status": "MUKABERE", "message": "Mucîb'in kendi öncülleri birbiriyle çelişiyor. İddia baştan çöktü."}
            
        self.active_premises = premises
        self.current_state = "AWAITING_ATTACK"
        self.discourse.set_agent("Sail") # Hamle sırası Sâil'e geçti
        
        return {"status": "EVIDENCE_LOGGED", "message": "Delil kendi içinde tutarlı. Sâil'in diyalektik saldırısı bekleniyor."}

    def attack_evidence(self, attack_type: Literal["Men", "Nakz", "Muaradah"], target_premise: Optional[str] = None) -> Dict[str, Any]:
        """Sâil'in argümana saldırı protolü."""
        if self.current_state != "AWAITING_ATTACK":
            raise ValueError("[DİYALEKTİK İHLAL] Şu an saldırı/itiraz aşamasında değilsiniz.")
            
        self.discourse.set_agent("Sail")
        
        if attack_type == "Men":
            if not target_premise or target_premise not in self.active_premises:
                return {"status": "INVALID_ATTACK", "message": "Men' saldırısı için hedef öncül belirtilmelidir."}
            
            # [LOGIC FIX]: Olası Memory Leak tıkandı. FSM AWAITING_EVIDENCE'a dönmeden önce reddedilen kapsam temizlenmelidir.
            self.solver.solver.pop()
            self.discourse.set_agent("Mujib")
            self.discourse.pop_scope()
            
            # Sâil öncülü reddettiği için FSM tekrar Mucîb'in ispat durumuna döner
            self.current_state = "AWAITING_EVIDENCE"
            return {"status": "MEN_ON_PREMISE", "message": f"Sâil '{target_premise}' öncülünü kanıtsız bularak reddetti. Mucîb bu öncülü ara-iddia olarak ispatlamalıdır."}
            
        elif attack_type == "Nakz":
            # Nakz: Mucîb'in öncülleri doğru kabul edilse dahi, kıyasın neticeyi vermediğinin (Lüzum Bağı/Hadd-i Evsat hatası) ispatı
            is_valid = self.solver.verify_syllogism(self.active_premises, self.active_claim)
            
            # Test bittiği için varsayımsal kapsamları bellekten düşür
            # [LOGIC FIX]: Pop işlemi yığıtı (frame) açan Mucîb aktörü üzerinden yürütülmelidir (Stack Underflow çözümü).
            self.solver.solver.pop()
            self.discourse.set_agent("Mujib")
            self.discourse.pop_scope()
            self.current_state = "RESOLVED"
            
            if is_valid:
                return {"status": "ILZAM", "message": "Sâil'in Nakz girişimi başarısız. Lüzum bağı ontolojik olarak geçerli. Mucîb kazandı (İlzam)."}
            else:
                return {"status": "NAKZ_SUCCESS", "message": "Fasid İstidlal kanıtlandı. Öncüller sonucu doğurmuyor (Nakz). Sâil kazandı."}
                
        elif attack_type == "Muaradah":
            # Muaradah (Cross-School çatışması) Faz 4 - Adım 3'te orkestratör üzerinden yönetilecektir.
            return {"status": "PENDING_CROSS_SCHOOL", "message": "Mu'aradah saldırısı için çift usûllü izolasyon motoru tetiklenmelidir."}
        else:
            return {"status": "ERROR", "message": "Geçersiz Âdâb-ı Bahs saldırı tipi."}
            
    def reset_session(self) -> None:
        """Diyalektik oturumu (Session) sıfırlar ve bellekleri temizler."""
        if self.current_state == "AWAITING_ATTACK":
            self.solver.solver.pop()
            self.discourse.set_agent("Mujib")
            self.discourse.pop_scope()
            
        self.current_state = "AWAITING_CLAIM"
        self.active_claim = None
        self.active_premises = []
        self.discourse.clear_memory()