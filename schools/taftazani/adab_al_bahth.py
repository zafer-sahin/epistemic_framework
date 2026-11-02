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
    Counter-Model Çözümlemesi, Tahrîr-i Mahall-i Niza' (Kavramsal İzolasyon) ve ortak ontolojide
    sınanan Mu'aradah (karşı-iddia) mekanizmalarını barındırır.
    [HATA DÜZELTMESİ - P0-8]: Müsâdere (iddiayı öncül olarak almak) ve devr delil sunulurken reddedilir.
    Düşen bir nakız ya da mu'âraza münazarayı bitirmez; münazara teslîmle biter (`concede`): Sâil
    teslim ederse ilzâm, Mucîb teslim ederse ifhâm.
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

    @staticmethod
    def _conjuncts(expr: z3.ExprRef) -> List[z3.ExprRef]:
        """İfadenin kendisi ve iç içe And'lerdeki bütün cüz'leri."""
        parts = [expr]
        if z3.is_and(expr):
            for child in expr.children():
                parts.extend(AdabAlBahthEngine._conjuncts(child))
        return parts

    @staticmethod
    def _entails(premise: z3.ExprRef, conclusion: z3.ExprRef) -> bool:
        """Salt mantık bakımından (ontoloji ve müsellemât olmadan) öncülün neticeyi gerektirip gerektirmediği."""
        solver = z3.Solver()
        solver.set("timeout", 2000)
        solver.add(premise, z3.Not(conclusion))
        return solver.check() == z3.unsat

    def _find_musadere(self, premises: List[str]) -> Optional[Tuple[str, str]]:
        """
        .. mantik_kurali:: Müsâdere ale'l-Matlûb ve Devr
            Delil, ispat edeceği şeyi öncül olarak alamaz. Bir öncül ya da öncülün bir cüz'ü, salt mantık
            bakımından iddiaya eşdeğerse (iddianın ta kendisi ya da başka sözle ifadesiyse) delil müsâderedir;
            men' edilmiş bir öncülün ispatında ana iddialardan birine eşdeğerse devirdir. Eşdeğerlik ontoloji
            ve müsellemât olmadan sınanır: arka plan bilgisiyle birbirinden çıkan iki önermeden birini
            ötekiyle ispatlamak müsâdere değildir ("cansız bir şey var" öncülü, Cemad ⊂ Cism sayesinde "cisim
            var" iddiasını gerektirir ama onun aynısı değildir).
        """
        claims = [self.active_claim] + [entry[0] for entry in reversed(self.claim_stack)]
        for premise in premises:
            self._auto_register_predicates(premise)
            for part in self._conjuncts(self.solver.builder.parse(premise)):
                for claim in claims:
                    claim_expr = self.solver.builder.parse(claim)
                    if self._entails(part, claim_expr) and self._entails(claim_expr, part):
                        return premise, claim
        return None

    def submit_evidence(self, premises: List[str]) -> Dict[str, Any]:
        if self.current_state != "AWAITING_EVIDENCE":
            raise ValueError("[DİYALEKTİK İHLAL] Şu an delil sunma aşamasında değilsiniz. (Tahrîr-i Niza' yapılmamış olabilir)")
        
        self.discourse.set_agent("Mujib")

        # [HATA DÜZELTMESİ - P0-8] İddiayı varsayan delil, kapsam açılmadan reddedilir; Mucîb başka delil getirebilir.
        try:
            musadere = self._find_musadere(premises)
        except Exception as e:
            return {"status": "ERROR", "message": f"Delil Derleme Hatası (Sentaks/Arite/Müsellemât): {e}"}

        if musadere is not None:
            premise, claim = musadere
            kind = "müsâdere ale'l-matlûb" if claim == self.active_claim else "devr: men' edilen öncül ana iddiayla ispatlanıyor"
            return {
                "status": "MUSADERE",
                "message": f"Delil, ispat edeceği şeyi varsayıyor ({kind}): '{premise}' öncülü '{claim}' iddiasının aynısı. Mucîb, iddiayı varsaymayan bir delil getirmelidir."
            }

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
            [HATA DÜZELTMESİ - P0-8]: Karşı-model yoksa yalnızca bu itiraz düşer (NAKZ_FAILED). İlzâm,
            Sâil'in itirazlarının tükenmesidir; men' ve mu'âraza hakkı sürer, münazara açık kalır.
            """
            from linguistics.discourse_state import DenialLevel
            self.discourse.update_epistemic_state("Sail", DenialLevel.MUNKIR)

            counter_model = None
            self.solver.solver.push()
            try:
                for p in self.active_premises:
                    self._auto_register_predicates(p)
                    self.solver.solver.add(self.solver.builder.parse(p))
                
                self._auto_register_predicates(self.active_claim)
                # İddianın değili eklenerek karşı-model (Counter-Model) aranır.
                self.solver.solver.add(z3.Not(self.solver.builder.parse(self.active_claim)))
                
                check_result = self.solver.solver.check()
                if check_result == z3.sat:
                    counter_model = self.solver.solver.model()
            finally:
                self.solver.solver.pop()

            if check_result == z3.unsat:
                return {
                    "status": "NAKZ_FAILED",
                    "message": "Sâil'in Nakz girişimi düştü: Mülâzama (Lüzum bağı) geçerli, öncüller zorunlu olarak neticeyi veriyor. Münazara sürüyor; Sâil men' ya da mu'âraza edebilir veya delili teslim edebilir."
                }
            if check_result == z3.unknown:
                # Çözücünün karar verememesi bir hüküm değildir; münazara açık kalır.
                return {
                    "status": "NAKZ_UNDECIDED",
                    "message": "Nakz karara bağlanamadı: öncüllerin neticeyi gerektirip gerektirmediği belirlenemedi. Sâil'in saldırısı bekleniyor."
                }

            self._close_evidence_scope()
            if self.claim_stack:
                return self._revert_sub_claim_failure("Alt-iddianın delili Nakz edildi. Üst iddia kanıtsız kaldı.")
            self.current_state = "RESOLVED"
            return {
                "status": "NAKZ_SUCCESS",
                "message": "Fâsid İstidlâl kanıtlandı. Öncüller doğru olduğu halde neticenin yanlış olabildiği bir model (Counter-Model) bulundu. Mülâzama koptu.",
                "counter_model_extract": str(counter_model)
            }
                
        elif attack_type == "Muaradah":
            """
            .. felsefe_notu:: Mu'aradah ve Ortak Ontoloji
            Sâil, Mucîb'in delilini men' etmeden iddianın hilâfını ileri sürer. Karşı-iddia, açık delil
            kapsamında sınanır: ontoloji, müsellemât ve Sâil'in men' etmediği öncüller.
            - Karşı-iddia bu kapsamla çelişiyorsa mu'âraza düşer (MUARADAH_FAILED).
            - Kapsamla bağdaşıyor ama kapsam, karşı-iddiaya rağmen iddiayı gerektiriyorsa karşı-iddia
              iddianın hilâfı değildir; mu'âraza iddiaya yöneltilmemiştir (MUARADAH_FAILED).
            - Kapsamın, karşı-iddia doğruyken iddianın yanlış olduğu bir modeli varsa delil, iddiayı
              karşı-iddiaya karşı ispatlamıyor demektir; argüman askıya alınır (STALEMATE).
            Düşen mu'âraza münazarayı bitirmez (P0-8); Sâil'in men' ve teslim hakkı sürer.
            Karşı delil (Sâil'in kendi öncülleri) ve rollerin değişmesi henüz modellenmediği için,
            geçerli bir delile karşı yalın bir karşı-iddia kilitlenme üretemez.
            """
            if not target_premise:
                return {"status": "INVALID_ATTACK", "message": "Mu'aradah için bir karşı-iddia (Counter-Claim) sunulmalıdır."}

            self._auto_register_predicates(target_premise)
            counter_claim = self.solver.builder.parse(target_premise)
            claim = self.solver.builder.parse(self.active_claim)

            # [HATA DÜZELTMESİ - P0-7]: Sınama, ontolojiyi taşıyan çözücünün açık delil kapsamında yapılır;
            # karşı-iddia esnek kısıt değildir, çelişkisi sonucu belirler.
            undermines_claim = None
            self.solver.solver.push()
            try:
                self.solver.solver.add(counter_claim)
                compatible = self.solver.solver.check()
                if compatible == z3.sat:
                    self.solver.solver.add(z3.Not(claim))
                    undermines_claim = self.solver.solver.check()
            finally:
                self.solver.solver.pop()

            if compatible == z3.unknown or undermines_claim == z3.unknown:
                # Çözücünün karar verememesi bir hüküm değildir; münazara açık kalır.
                return {
                    "status": "MUARADAH_UNDECIDED",
                    "message": "Mu'aradah karara bağlanamadı: karşı-iddianın delil ve ontolojiyle ilişkisi belirlenemedi. Sâil'in saldırısı bekleniyor."
                }

            if compatible == z3.unsat:
                return {
                    "status": "MUARADAH_FAILED",
                    "message": "Sâil'in karşı-iddiası, men' etmediği delil ve ortak ontolojiyle çelişiyor. Mu'aradah düştü; münazara sürüyor (Sâil men' edebilir ya da delili teslim edebilir)."
                }
            if undermines_claim == z3.unsat:
                return {
                    "status": "MUARADAH_FAILED",
                    "message": "Sâil'in karşı-iddiası delille bağdaşıyor, ancak delil karşı-iddiaya rağmen iddiayı gerektiriyor: karşı-iddia iddianın hilâfı değil. Mu'aradah düştü; münazara sürüyor (Sâil men' edebilir ya da delili teslim edebilir)."
                }

            self._close_evidence_scope()
            self.current_state = "RESOLVED"
            return {
                "status": "STALEMATE",
                "message": "Mu'aradah başarılı. Karşı-iddia delil ve ortak ontolojiyle bağdaşıyor; delil, iddiayı karşı-iddiaya karşı ispatlamıyor. Argüman askıya alındı (Stalemate)."
            }
        else:
            return {"status": "ERROR", "message": "Geçersiz Âdâb-ı Bahs saldırı tipi."}

    def concede(self) -> Dict[str, Any]:
        """
        .. felsefe_notu:: Teslîm: İlzâm ve İfhâm
            Münazara tek bir itirazın düşmesiyle değil, nöbeti tutan tarafın cevapsız kalıp teslim etmesiyle
            biter. İtirazları tükenen Sâil delili teslim ederse ilzâm olur: iddia sabittir. Men' edilmiş bir
            öncülün ispatında Sâil'in teslimi alt-iddiayı sabit kılar ve ana iddiaya dönülür. İddiasına (ya
            da men' edilen öncüle) delil getiremeyen Mucîb teslim ederse ifhâm olur: iddia sabit olmamıştır.
        """
        if self.current_state == "AWAITING_ATTACK":
            self._close_evidence_scope()
            if self.claim_stack:
                return self._resolve_sub_claim()
            self.current_state = "RESOLVED"
            return {
                "status": "ILZAM",
                "message": "Sâil delili teslim etti; itirazları tükendi. İddia sabit oldu, Sâil ilzâm edildi (Mucîb kazandı)."
            }

        if self.current_state == "AWAITING_EVIDENCE":
            unproven = "men' edilen öncüle" if self.claim_stack else "iddiasına"
            self._close_evidence_scope()
            self.claim_stack.clear()
            self.current_state = "RESOLVED"
            return {
                "status": "IFHAM",
                "message": f"Mucîb {unproven} delil getiremeyip teslim etti; cevapsız kaldı. İddia sabit olmadı, Mucîb ifhâm edildi (Sâil kazandı)."
            }

        raise ValueError(f"[DİYALEKTİK İHLAL] Mevcut durum '{self.current_state}'. Teslim ancak delil ya da itiraz nöbetinde yapılabilir.")

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