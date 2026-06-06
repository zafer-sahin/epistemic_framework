import z3
import re
from typing import List, Dict, Any, Optional, Literal, Tuple
from core.logic_engine import AristotelianSolver
from linguistics.discourse_state import DiscourseRegister

class AdabAlBahthEngine:
    """
    Taftâzânî, Cürcânî ve Gelenbevî temelli Münazara Sonlu Durum Makinesi (FSM).
    Faz 5: Rekürsif Men' (İç içe İspat Yükümlülüğü), Mülâzama Counter-Model Çözümlemesi 
    ve Tahrîr-i Mahall-i Niza' Z3 Aksiyom Enjeksiyonu.
    """
    def __init__(self, solver: AristotelianSolver, discourse: DiscourseRegister):
        self.solver = solver
        self.discourse = discourse
        
        self.current_state: Literal["AWAITING_CLAIM", "ISOLATING_CONTENTION", "AWAITING_EVIDENCE", "AWAITING_ATTACK", "RESOLVED"] = "AWAITING_CLAIM"
        self.active_claim: Optional[str] = None
        self.active_premises: List[str] = []
        
        # Rekürsif diyalektik için yığıt (Stack) mimarisi
        self.claim_stack: List[Tuple[str, List[str], List[str], List[str]]] = [] 
        
        self.musellemat: List[str] = [] 
        self.niza_terms: List[str] = [] 

    def _auto_register_predicates(self, fol_str: str) -> None:
        """
        Z3 Parser'ın tanımsız yüklem (Unknown Predicate) hatası vermesini engellemek için, 
        kompleks FOL stringleri içindeki tüm felsefi kavramları parse edilmeden önce SMT Builder'a kaydeder.
        """
        matches = re.findall(r'([A-Z][a-zA-Z0-9_]*)\s*\(', fol_str)
        z3_keywords = {"Forall", "Exists", "And", "Or", "Not", "Implies"}
        for match in matches:
            if match not in z3_keywords:
                self.solver.builder.get_or_create_predicate(match, arity=1)

    def submit_claim(self, claim: str) -> Dict[str, Any]:
        if self.current_state not in ["AWAITING_CLAIM", "AWAITING_EVIDENCE"]:
            raise ValueError(f"[DİYALEKTİK İHLAL] Mevcut durum '{self.current_state}'. Yeni iddia sunulamaz.")
            
        self.discourse.set_agent("Mujib")
        
        self._auto_register_predicates(claim)
        is_already_valid = self.solver.verify_syllogism([], claim)
        
        if is_already_valid:
            if self.claim_stack:
                return self._resolve_sub_claim()
            else:
                self.current_state = "RESOLVED"
                return {"status": "TAHSIL_I_HASIL", "message": "İddia ontolojik bir aksiyomdur (Tahsîl-i Hâsıl), ispat gerektirmez."}
        
        self.active_claim = claim
        
        self.current_state = "ISOLATING_CONTENTION"
        self.discourse.set_agent("Sail") 
        
        return {
            "status": "AWAITING_TAHRIR", 
            "message": "İddia alındı. Delil sunulmadan önce Tahrîr-i Mahall-i Niza' (Kavramsal Senkronizasyon) aşamasına geçiliyor."
        }

    def tahrir_i_niza(self, musellemat: List[str], niza_terms: List[str]) -> Dict[str, Any]:
        if self.current_state != "ISOLATING_CONTENTION":
            raise ValueError(f"[DİYALEKTİK İHLAL] Tahrîr-i Niza' yalnızca 'ISOLATING_CONTENTION' aşamasında yapılabilir.")
            
        if not niza_terms:
            if self.claim_stack:
                return self._resolve_sub_claim()
            else:
                self.current_state = "RESOLVED"
                return {"status": "NO_CONTENTION", "message": "Tartışılacak (Niza') hiçbir kavram bildirilmedi, uyuşmazlık yoktur."}

        self.musellemat = musellemat
        self.niza_terms = niza_terms
        
        self.current_state = "AWAITING_EVIDENCE"
        self.discourse.set_agent("Mujib") 
        
        return {
            "status": "CONTENTION_ISOLATED", 
            "message": f"Müsellemât (Kabul): {musellemat} | Niza' (İhtilaf): {niza_terms}. Sâil iddiayı sınırlandırdı, Mucîb delil getirmelidir."
        }

    def submit_evidence(self, premises: List[str]) -> Dict[str, Any]:
        if self.current_state != "AWAITING_EVIDENCE":
            raise ValueError("[DİYALEKTİK İHLAL] Şu an delil sunma aşamasında değilsiniz. (Tahrîr-i Niza' yapılmamış olabilir)")
        
        self.discourse.set_agent("Mujib")
        
        self.solver.solver.push()
        self.discourse.push_scope()
        
        try:
            w_env = z3.Const('w_env', self.solver.builder.WorldSort)
            tz_env = z3.Const('tz_env', self.solver.builder.TimeSortZati)
            tv_env = z3.Const('tv_env', self.solver.builder.TimeSortVasfi)
            x_env = z3.Const('x_env', self.solver.builder.EntitySort)
            
            for m_term in self.musellemat:
                if "(" in m_term and ")" in m_term:
                    self._auto_register_predicates(m_term)
                    self.solver.solver.add(self.solver.builder.parse(m_term))
                else:
                    pred = self.solver.builder.get_or_create_predicate(m_term, arity=1)
                    self.solver.solver.add(z3.Exists([w_env, tz_env, tv_env, x_env], pred(w_env, tz_env, tv_env, x_env)))

            for p in premises:
                self._auto_register_predicates(p)
                self.solver.solver.add(self.solver.builder.parse(p))
                
            is_consistent = (self.solver.solver.check() == z3.sat)
        except Exception as e:
            self.solver.solver.pop()
            self.discourse.pop_scope()
            return {"status": "ERROR", "message": f"Delil Derleme Hatası (Sentaks/Arite/Müsellemât): {e}"}
        
        if not is_consistent:
            self.solver.solver.pop()
            self.discourse.pop_scope()
            if self.claim_stack:
                return self._revert_sub_claim_failure("Mucîb'in delilleri tutarsız (Mukabere). Alt-iddia çöktü.")
            else:
                self.current_state = "RESOLVED"
                return {"status": "MUKABERE", "message": "Mucîb'in kendi öncülleri (veya Müsellemât) birbiriyle çelişiyor. İddia baştan çöktü."}
            
        self.active_premises = premises
        self.current_state = "AWAITING_ATTACK"
        self.discourse.set_agent("Sail")
        
        return {"status": "EVIDENCE_LOGGED", "message": "Delil kendi içinde tutarlı. Sâil'in diyalektik saldırısı bekleniyor."}

    def attack_evidence(self, attack_type: Literal["Men", "Nakz", "Muaradah"], target_premise: Optional[str] = None) -> Dict[str, Any]:
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
            
            # Rekürsif İspat Yükümlülüğü: Hedef öncül yeni Da'vâ olur.
            self.claim_stack.append((self.active_claim, self.active_premises, self.musellemat, self.niza_terms))
            self.active_claim = target_premise
            self.active_premises = []
            self.current_state = "ISOLATING_CONTENTION"
            
            return {
                "status": "MEN_ON_PREMISE", 
                "message": f"Sâil '{target_premise}' öncülünü kanıtsız bularak reddetti (Men'). Lüzum zinciri askıya alındı. Mucîb, reddedilen bu öncülü yeni bir Da'vâ olarak ispatlamak zorundadır. Tahrîr-i Niza' bekleniyor."
            }
            
        elif attack_type == "Nakz":
            from linguistics.discourse_state import DenialLevel
            self.discourse.update_epistemic_state("Sail", DenialLevel.MUNKIR)

            self.solver.solver.push()
            try:
                for p in self.active_premises:
                    self._auto_register_predicates(p)
                    self.solver.solver.add(self.solver.builder.parse(p))
                
                self._auto_register_predicates(self.active_claim)
                # İddianın değili eklenerek karşı-model (Counter-Model) aranır
                self.solver.solver.add(z3.Not(self.solver.builder.parse(self.active_claim)))
                
                check_result = self.solver.solver.check()
                
                if check_result == z3.unsat:
                    response = {
                        "status": "ILZAM", 
                        "message": "Sâil'in Nakz girişimi başarısız. Mülâzama (Lüzum bağı) ontolojik olarak geçerli. Öncüller zorunlu olarak neticeyi veriyor. Mucîb kazandı (İlzam)."
                    }
                else:
                    counter_model = self.solver.solver.model()
                    response = {
                        "status": "NAKZ_SUCCESS", 
                        "message": "Fâsid İstidlâl kanıtlandı. Öncüller doğru olduğu halde neticenin yanlış olabildiği bir model (Counter-Model) bulundu. Mülâzama koptu.",
                        "counter_model_extract": str(counter_model)
                    }
            finally:
                self.solver.solver.pop()

            self.solver.solver.pop()
            self.discourse.set_agent("Mujib")
            self.discourse.pop_scope()
            
            if self.claim_stack and response["status"] == "ILZAM":
                return self._resolve_sub_claim()
            elif self.claim_stack and response["status"] == "NAKZ_SUCCESS":
                return self._revert_sub_claim_failure("Alt-iddianın delili Nakz edildi. Üst iddia kanıtsız kaldı.")
            else:
                self.current_state = "RESOLVED"
                return response
                
        elif attack_type == "Muaradah":
            return {"status": "PENDING_CROSS_SCHOOL", "message": "Mu'aradah saldırısı için Orkestratör üzerinden çapraz-ekol (z3.Optimize) izolasyon motoru tetiklenmelidir."}
        else:
            return {"status": "ERROR", "message": "Geçersiz Âdâb-ı Bahs saldırı tipi."}

    def _resolve_sub_claim(self) -> Dict[str, Any]:
        """Alt-iddia başarıyla ispatlandığında yığıttan ana iddiaya geri dönüş yapar."""
        prev_claim, prev_premises, prev_musellemat, prev_niza = self.claim_stack.pop()
        self.active_claim = prev_claim
        self.active_premises = prev_premises
        self.musellemat = prev_musellemat
        self.niza_terms = prev_niza
        self.current_state = "AWAITING_ATTACK"
        
        return {
            "status": "SUB_CLAIM_PROVEN",
            "message": "Mucîb, Men' edilen öncülü başarıyla ispatladı. Ana iddiaya geri dönüldü. Sâil'in diğer öncüllere saldırısı (Men'/Nakz/Muaradah) bekleniyor."
        }

    def _revert_sub_claim_failure(self, reason: str) -> Dict[str, Any]:
        """Alt-iddia çürütüldüğünde zincirleme reaksiyonla ana iddiayı da iptal eder."""
        self.claim_stack.clear()
        self.current_state = "RESOLVED"
        return {
            "status": "CHAIN_FAILURE",
            "message": f"Diyalektik zincir koptu: {reason} Ana iddia da geçersiz sayıldı."
        }

    def reset_session(self) -> None:
        if self.current_state == "AWAITING_ATTACK" or self.current_state == "AWAITING_EVIDENCE":
            try:
                self.solver.solver.pop()
                self.discourse.pop_scope()
            except z3.Z3Exception:
                pass
            
        self.current_state = "AWAITING_CLAIM"
        self.active_claim = None
        self.active_premises = []
        self.claim_stack.clear()
        self.musellemat = []
        self.niza_terms = []
        self.discourse.set_agent("Mujib")
        self.discourse.clear_memory()