import z3
import re
from typing import List, Dict, Any, Optional, Literal, Tuple
from core.logic_engine import AristotelianSolver
from linguistics.discourse_state import DiscourseRegister

class AdabAlBahthEngine:
    """
    .. pedagojik_anlati:: Cürcânî Diyalektiği ve Z3 Otomatı
    Taftâzânî, Cürcânî ve Gelenbevî temelli Münazara Sonlu Durum Makinesi (FSM).
    Faz 4 ve Faz 5 entegrasyonuyla: Rekürsif Men' (İç içe İspat Yükümlülüğü), Mülâzama 
    Counter-Model Çözümlemesi, Tahrîr-i Mahall-i Niza' (Kavramsal İzolasyon) ve 
    z3.Optimize tabanlı Mu'aradah (Çapraz-Ekol Kilitlenmesi / Tevcîh) mekanizmalarını barındırır.
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

        # [HATA DÜZELTMESİ - P0-4]: Bu motorun çözücüde açtığı delil kapsamı (push) açık mı?
        # Kapsamı yalnızca açan kapatır; paylaşılan çözücüdeki yabancı scope'lara dokunulmaz.
        self._evidence_scope_open = False

    def _open_evidence_scope(self) -> None:
        """Mucîb'in delil kapsamını (Z3 push + DRT frame) açar."""
        self.discourse.set_agent("Mujib")
        self.solver.solver.push()
        self.discourse.push_scope()
        self._evidence_scope_open = True

    def _close_evidence_scope(self) -> None:
        """Yalnızca bu motorun açtığı delil kapsamını kapatır; açık kapsam yoksa hiçbir şey yapmaz."""
        if not self._evidence_scope_open:
            return
        self._evidence_scope_open = False
        self.solver.solver.pop()
        self.discourse.set_agent("Mujib")
        self.discourse.pop_scope()

    def _assert_evidence(self, musellemat: List[str], premises: List[str]) -> None:
        """Müsellemât ve öncülleri açık delil kapsamına mühürler."""
        w_env = z3.Const('w_env', self.solver.builder.WorldSort)
        tz_env = z3.Const('tz_env', self.solver.builder.TimeSortZati)
        tv_env = z3.Const('tv_env', self.solver.builder.TimeSortVasfi)
        s_env = z3.Const('s_env', self.solver.builder.SpaceSort) # [FAZ 4.1] Kripke Uzayı - Mekân Boyutu
        x_env = z3.Const('x_env', self.solver.builder.EntitySort)

        for m_term in musellemat:
            if "(" in m_term and ")" in m_term:
                self._auto_register_predicates(m_term)
                self.solver.solver.add(self.solver.builder.parse(m_term))
            else:
                pred = self.solver.builder.get_or_create_predicate(m_term, arity=1)
                # Çok-boyutlu uzay kısıtı mühürlenir
                self.solver.solver.add(z3.Exists([w_env, tz_env, tv_env, s_env, x_env], pred(w_env, tz_env, tv_env, s_env, x_env)))

        for p in premises:
            self._auto_register_predicates(p)
            self.solver.solver.add(self.solver.builder.parse(p))

    def resolve_debate(self) -> None:
        """Münazarayı dışarıdan (ör. çapraz-ekol mu'âraza) sonuçlandırır ve açık delil kapsamını kapatır."""
        self._close_evidence_scope()
        self.current_state = "RESOLVED"

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
        """
        .. felsefe_notu:: Tahrîr-i Mahall-i Niza' (Kavramsal Senkronizasyon)
        Sâil ve Mucîb argümantasyona başlamadan önce, itilafın tam olarak nerede olduğunu 
        izole etmek zorundadır. Bu aşama, varlıkların DiscourseRepresentation (DRT) üzerinde 
        'Müsellem' (Base/Ortak) veya 'Niza' (Mujib/Çatışmalı) olarak mühürlenmesini sağlar.
        Bağlam zehirlenmesinin (Context Poisoning) önüne geçilen ilk duvardır.
        """
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
        
        # [FAZ 4.2 GÜNCELLEMESİ] DRT Context Sealing Enjeksiyonu
        for term in musellemat:
            self.discourse.add_mention(word=term, ontologic_id=term, active_namespace="Base")
            
        for term in niza_terms:
            self.discourse.add_mention(word=term, ontologic_id=term, active_namespace="Mujib")
        
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

        self._open_evidence_scope()

        try:
            self._assert_evidence(self.musellemat, premises)
            is_consistent = (self.solver.solver.check() == z3.sat)
        except Exception as e:
            self._close_evidence_scope()
            return {"status": "ERROR", "message": f"Delil Derleme Hatası (Sentaks/Arite/Müsellemât): {e}"}

        if not is_consistent:
            self._close_evidence_scope()
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

            self._close_evidence_scope()

            # Rekürsif İspat Yükümlülüğü: Hedef öncül yeni Da'vâ olur.
            self.claim_stack.append((self.active_claim, self.active_premises, self.musellemat, self.niza_terms))
            self.active_claim = target_premise
            self.active_premises = []
            self.current_state = "ISOLATING_CONTENTION"
            
            # [HATA DÜZELTMESİ]: Yeni Da'vâ eklendiğinde Tahrîr-i Niza' için FSM nöbeti zorunlu olarak Sâil'e geçer.
            self.discourse.set_agent("Sail")
            
            return {
                "status": "MEN_ON_PREMISE", 
                "message": f"Sâil '{target_premise}' öncülünü kanıtsız bularak reddetti (Men'). Lüzum zinciri askıya alındı. Mucîb, reddedilen bu öncülü yeni bir Da'vâ olarak ispatlamak zorundadır. Tahrîr-i Niza' bekleniyor."
            }
            
        elif attack_type == "Nakz":
            """
            .. mantik_kurali:: Nakz ve Mülâzama (Lüzum Bağı Testi)
            Nakz saldırısı, öncüllerin doğru kabul edildiği bir modelde neticenin (iddianın) yanlış 
            olabileceğini ispatlama sürecidir. Hadd-i Evsat (orta terim) neticeyi ontolojik bir zorunlulukla 
            bağlamıyorsa (Mülâzama yoksa), SMT çözücü bir Counter-Model bulacak ve Mucîb'in istidlâli Fâsid sayılacaktır.
            """
            from linguistics.discourse_state import DenialLevel
            self.discourse.update_epistemic_state("Sail", DenialLevel.MUNKIR)

            self.solver.solver.push()
            try:
                for p in self.active_premises:
                    self._auto_register_predicates(p)
                    self.solver.solver.add(self.solver.builder.parse(p))
                
                self._auto_register_predicates(self.active_claim)
                # İddianın değili eklenerek karşı-model (Counter-Model) aranır.
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

            self._close_evidence_scope()

            if self.claim_stack and response["status"] == "ILZAM":
                return self._resolve_sub_claim()
            elif self.claim_stack and response["status"] == "NAKZ_SUCCESS":
                return self._revert_sub_claim_failure("Alt-iddianın delili Nakz edildi. Üst iddia kanıtsız kaldı.")
            else:
                self.current_state = "RESOLVED"
                return response
                
        elif attack_type == "Muaradah":
            """
            .. felsefe_notu:: Mu'aradah ve Z3 Optimize (Tevcîh Kilitlenmesi)
            Çapraz ekol çarpışmalarında (Örn: Eş'arî vs. Selefî), Z3'ün deterministik Push/Pop yalıtımı 
            tek başına yeterli değildir. Rakibin ontolojik ağacı "ödünç alınıp" kendi silahıyla vurulmak 
            istendiğinde (Tevcîh), 'z3.Optimize()' ve 'Soft Constraints' kullanılarak deterministik kilitlenme 
            (Stalemate) üretilir. Bu, iki zıt doğrunun aynı anda geçerli olduğu diyalektik bir düğümdür.
            """
            if not target_premise:
                return {"status": "INVALID_ATTACK", "message": "Mu'aradah için bir karşı-iddia (Counter-Claim) sunulmalıdır."}
                
            opt = z3.Optimize()
            
            w_env = z3.Const('w_env', self.solver.builder.WorldSort)
            tz_env = z3.Const('tz_env', self.solver.builder.TimeSortZati)
            tv_env = z3.Const('tv_env', self.solver.builder.TimeSortVasfi)
            s_env = z3.Const('s_env', self.solver.builder.SpaceSort)
            x_env = z3.Const('x_env', self.solver.builder.EntitySort)
            
            # Müsellemâtı (Ortak Kabulleri) mutlak (Hard Constraint) olarak ekle
            for m_term in self.musellemat:
                if "(" in m_term and ")" in m_term:
                    self._auto_register_predicates(m_term)
                    opt.add(self.solver.builder.parse(m_term))
                else:
                    pred = self.solver.builder.get_or_create_predicate(m_term, arity=1)
                    opt.add(z3.Exists([w_env, tz_env, tv_env, s_env, x_env], pred(w_env, tz_env, tv_env, s_env, x_env)))
                    
            # Mucîb'in asıl argüman öncüllerini mutlak (Hard Constraint) olarak ekle
            for p in self.active_premises:
                self._auto_register_predicates(p)
                opt.add(self.solver.builder.parse(p))
                
            # Sâil'in Mu'aradah hedefini (karşı önermesini) Esnek Kısıt (Soft Constraint) olarak ekle
            self._auto_register_predicates(target_premise)
            opt.add_soft(self.solver.builder.parse(target_premise), weight=10)
            
            # Kilitlenmeyi (Stalemate) simüle etmek için Mucîb'in iddiasının zıttını da Esnek Kısıt olarak ekle
            opt.add_soft(z3.Not(self.solver.builder.parse(self.active_claim)), weight=10)
            
            check_opt = opt.check()

            self._close_evidence_scope()
            self.current_state = "RESOLVED"
            
            if check_opt == z3.sat:
                return {
                    "status": "STALEMATE",
                    "message": "Mu'aradah başarılı. Z3 Optimize motoru her iki ekolün de haklı olabileceği esnek bir kilitlenme (Stalemate / Tevcîh) buldu. Argüman askıya alındı."
                }
            else:
                return {
                    "status": "MUARADAH_FAILED",
                    "message": "Sâil'in Mu'aradah girişimi ontolojik çelişki yarattı. Çapraz-ekol saldırısı başarısız. Mucîb haklıdır."
                }
        else:
            return {"status": "ERROR", "message": "Geçersiz Âdâb-ı Bahs saldırı tipi."}

    def _resolve_sub_claim(self) -> Dict[str, Any]:
        """Alt-iddia başarıyla ispatlandığında yığıttan ana iddiaya geri dönüş yapar."""
        prev_claim, prev_premises, prev_musellemat, prev_niza = self.claim_stack.pop()
        self.active_claim = prev_claim
        self.active_premises = prev_premises
        self.musellemat = prev_musellemat
        self.niza_terms = prev_niza

        # Ana iddianın delil kapsamı Men' anında kapatılmıştı; nöbet ana iddiaya dönerken yeniden kurulur.
        self._open_evidence_scope()
        self._assert_evidence(self.musellemat, self.active_premises)
        self.current_state = "AWAITING_ATTACK"
        self.discourse.set_agent("Sail")

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
        try:
            self._close_evidence_scope()
        except (z3.Z3Exception, RuntimeError):
            # Kapsam dışarıdan kapatılmışsa oturum yine de sıfırlanır.
            pass

        self.current_state = "AWAITING_CLAIM"
        self.active_claim = None
        self.active_premises = []
        self.claim_stack.clear()
        self.musellemat = []
        self.niza_terms = []
        self.discourse.set_agent("Mujib")
        self.discourse.clear_memory()