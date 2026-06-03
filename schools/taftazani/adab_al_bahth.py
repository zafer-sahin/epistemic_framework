import z3
from typing import List, Dict, Any, Optional, Literal
from core.logic_engine import AristotelianSolver
from linguistics.discourse_state import DiscourseRegister

class AdabAlBahthEngine:
    """
    Taftâzânî, Cürcânî ve Gelenbevî temelli Münazara Sonlu Durum Makinesi (FSM).
    Faz 5: Tahrîr-i Mahall-i Niza' (Kavramsal Senkronizasyon) ve Mülâzama testleri eklendi.
    """
    def __init__(self, solver: AristotelianSolver, discourse: DiscourseRegister):
        self.solver = solver
        self.discourse = discourse
        
        # FSM Durum Değişkenleri
        self.current_state: Literal["AWAITING_CLAIM", "ISOLATING_CONTENTION", "AWAITING_EVIDENCE", "AWAITING_ATTACK", "RESOLVED"] = "AWAITING_CLAIM"
        self.active_claim: Optional[str] = None
        self.active_premises: List[str] = []
        
        # [FAZ 5] Kavramsal Senkronizasyon Kayıtları
        self.musellemat: List[str] = [] # Ortak kabul edilen terimler (Agreed Terms)
        self.niza_terms: List[str] = [] # Üzerinde tartışılan ihtilaflı terimler (Contested Terms)

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
        
        # [FAZ 5] Doğrudan delil aşamasına atlamak yerine Tahrîr-i Niza' (Kavramsal Senkronizasyon) aşamasına geçilir
        self.current_state = "ISOLATING_CONTENTION"
        self.discourse.set_agent("Sail") # Senkronizasyon için Sâil'in onayı/reddi gerekir
        
        return {
            "status": "AWAITING_TAHRIR", 
            "message": "İddia alındı. Delil sunulmadan önce Tahrîr-i Mahall-i Niza' (Kavramsal Senkronizasyon) aşamasına geçiliyor."
        }

    def tahrir_i_niza(self, musellemat: List[str], niza_terms: List[str]) -> Dict[str, Any]:
        """[FAZ 5] Tahrîr-i Mahall-i Niza' (Kavramsal Senkronizasyon) Aşaması."""
        if self.current_state != "ISOLATING_CONTENTION":
            raise ValueError(f"[DİYALEKTİK İHLAL] Tahrîr-i Niza' yalnızca 'ISOLATING_CONTENTION' aşamasında yapılabilir.")
            
        if not niza_terms:
            self.current_state = "RESOLVED"
            return {"status": "NO_CONTENTION", "message": "Tartışılacak (Niza') hiçbir kavram bildirilmedi, uyuşmazlık yoktur."}

        self.musellemat = musellemat
        self.niza_terms = niza_terms
        
        self.current_state = "AWAITING_EVIDENCE"
        self.discourse.set_agent("Mujib") # Delil getirme yükümlülüğü Mucîb'e geri döner
        
        return {
            "status": "CONTENTION_ISOLATED", 
            "message": f"Müsellemât (Kabul): {musellemat} | Niza' (İhtilaf): {niza_terms}. Sâil iddiayı sınırlandırdı, Mucîb delil getirmelidir."
        }

    def submit_evidence(self, premises: List[str]) -> Dict[str, Any]:
        """Mucîb tarafından delil (İstidlal) sunumu."""
        if self.current_state != "AWAITING_EVIDENCE":
            raise ValueError("[DİYALEKTİK İHLAL] Şu an delil sunma aşamasında değilsiniz. (Tahrîr-i Niza' yapılmamış olabilir)")
        
        self.discourse.set_agent("Mujib")
        
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
        self.discourse.set_agent("Sail")
        
        return {"status": "EVIDENCE_LOGGED", "message": "Delil kendi içinde tutarlı. Sâil'in diyalektik saldırısı bekleniyor."}

    def attack_evidence(self, attack_type: Literal["Men", "Nakz", "Muaradah"], target_premise: Optional[str] = None) -> Dict[str, Any]:
        """Sâil'in argümana saldırı protolü."""
        if self.current_state != "AWAITING_ATTACK":
            raise ValueError("[DİYALEKTİK İHLAL] Şu an saldırı/itiraz aşamasında değilsiniz.")
            
        self.discourse.set_agent("Sail")
        
        if attack_type == "Men":
            if not target_premise or target_premise not in self.active_premises:
                return {"status": "INVALID_ATTACK", "message": "Men' saldırısı için hedef öncül belirtilmelidir."}
            
            from linguistics.discourse_state import DenialLevel
            self.discourse.update_epistemic_state("Sail", DenialLevel.MUTAREDDIT)

            self.solver.solver.pop()
            self.discourse.set_agent("Mujib")
            self.discourse.pop_scope()
            
            self.current_state = "AWAITING_EVIDENCE"
            return {"status": "MEN_ON_PREMISE", "message": f"Sâil '{target_premise}' öncülünü kanıtsız bularak reddetti (Mutareddit). Mucîb bu öncülü ara-iddia olarak ispatlamalıdır."}
            
        elif attack_type == "Nakz":
            from linguistics.discourse_state import DenialLevel
            self.discourse.update_epistemic_state("Sail", DenialLevel.MUNKIR)

            # [FAZ 5] Mülâzama (Zaruri İçerme Bağı) Denetimi. Gelenbevî'nin Nakz koşulu.
            is_valid = self.solver.verify_syllogism(self.active_premises, self.active_claim)
            
            self.solver.solver.pop()
            self.discourse.set_agent("Mujib")
            self.discourse.pop_scope()
            self.current_state = "RESOLVED"
            
            if is_valid:
                return {
                    "status": "ILZAM", 
                    "message": "Sâil'in Nakz girişimi başarısız. Mülâzama (Lüzum bağı) ontolojik olarak geçerli. Öncüller zorunlu olarak neticeyi veriyor. Mucîb kazandı (İlzam)."
                }
            else:
                return {
                    "status": "NAKZ_SUCCESS", 
                    "message": "Fasid İstidlal kanıtlandı. Mülâzama (Lüzum bağı) koptu, öncüller neticeyi doğurmuyor (Nakz). Sâil kazandı."
                }
                
        elif attack_type == "Muaradah":
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
        self.musellemat = []
        self.niza_terms = []
        self.discourse.clear_memory()