import z3
from typing import List, Dict, Any
from core.logic_engine import AristotelianSolver
from linguistics.discourse_state import DiscourseRegister

class AdabAlBahthEngine:
    """
    Taftâzânî ve Cürcânî temelli Münazara Durum Makinesi.
    Z3 (Mantıksal Uzay) ile DiscourseRegister (Dilbilimsel Uzay) arasında
    donanımsal Push/Pop senkronizasyonunu sağlar.
    """
    def __init__(self, solver: AristotelianSolver, discourse: DiscourseRegister):
        self.solver = solver
        self.discourse = discourse

    def evaluate_claim(self, claim: str) -> Dict[str, Any]:
        """İddianın (Da'vâ) ontolojik zorunluluğunu (Tahsîl-i Hâsıl / Men') test eder."""
        try:
            # İddia testi statik bir kontroldür, söylem belleğini zehirlemez.
            is_already_valid = self.solver.verify_syllogism([], claim)
            if is_already_valid:
                return {"status": "TAHSIL_I_HASIL", "message": "İddia zaten ontolojik bir zorunluluktur."}
            return {"status": "MEN", "message": "İddia zorunlu değil. Delil talep ediliyor."}
        except Exception as e:
            return {"status": "ERROR", "message": f"İddia Derleme Hatası: {e}"}

    def evaluate_evidence(self, claim: str, premises: List[str]) -> Dict[str, Any]:
        """Delillerin tutarlılığını ve iddiaya olan lüzum bağını test eder."""
        
        # Mantıksal ve Dilbilimsel uzayda eşzamanlı Frame (Kapsam) açılışı
        self.solver.solver.push()
        self.discourse.push_scope()
        
        is_consistent = True
        try:
            for p in premises:
                self.solver.solver.add(self.solver.builder.parse(p))
            is_consistent = (self.solver.solver.check() == z3.sat)
        except Exception as e:
            # Çöküş durumunda her iki uzayı da temizle
            self.solver.solver.pop()
            self.discourse.pop_scope()
            return {"status": "ERROR", "message": f"Delil Derleme Hatası (Sentaks/Arite): {e}"}
        
        # Eğer öncüller birbiriyle çelişiyorsa
        if not is_consistent:
            self.solver.solver.pop()
            self.discourse.pop_scope()
            return {"status": "MUKABERE", "message": "İmkansız veya birbiriyle çelişen öncüller (Ex Falso Quodlibet ihlali)."}

        # Öncüller tutarlıysa, iddiayı (Da'vâ) doğrulayıp doğrulamadığını kontrol et
        is_valid = self.solver.verify_syllogism(premises, claim)
        
        # Test bittiği için varsayımsal kapsamları bellekten düşür
        self.solver.solver.pop()
        self.discourse.pop_scope()

        if is_valid:
            return {"status": "ILZAM", "message": "Deliller iddiayı ontolojik olarak zorunlu kılmaktadır."}
        else:
            return {"status": "NAKZ", "message": "Fasid İstidlal. Öncüller tutarlı ancak lüzum bağı (Hadd-i Evsat) eksik."}