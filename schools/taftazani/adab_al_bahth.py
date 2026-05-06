import z3
from typing import List, Dict, Any
from core.logic_engine import AristotelianSolver

class AdabAlBahthEngine:
    """
    Taftâzânî ve Cürcânî temelli Münazara Durum Makinesi.
    I/O bağımsızdır. Sadece mantıksal durum (State) ve veri (Payload) döndürür.
    """
    def __init__(self, solver: AristotelianSolver):
        self.solver = solver

    def evaluate_claim(self, claim: str) -> Dict[str, Any]:
        """İddianın (Da'vâ) ontolojik zorunluluğunu test eder."""
        try:
            is_already_valid = self.solver.verify_syllogism([], claim)
            if is_already_valid:
                return {"status": "TAHSIL_I_HASIL", "message": "İddia zaten ontolojik bir zorunluluktur."}
            return {"status": "MEN", "message": "İddia zorunlu değil. Delil talep ediliyor."}
        except Exception as e:
            return {"status": "ERROR", "message": f"İddia Derleme Hatası: {e}"}

    def evaluate_evidence(self, claim: str, premises: List[str]) -> Dict[str, Any]:
        """Delillerin (Öncüller) tutarlılığını ve iddiaya olan lüzum bağını test eder."""
        self.solver.solver.push()
        is_consistent = True
        try:
            for p in premises:
                self.solver.solver.add(self.solver.builder.parse(p))
            is_consistent = (self.solver.solver.check() == z3.sat)
        except Exception as e:
            self.solver.solver.pop()
            return {"status": "ERROR", "message": f"Delil Derleme Hatası (Sentaks/Arite): {e}"}
        
        self.solver.solver.pop()

        if not is_consistent:
            return {"status": "MUKABERE", "message": "İmkansız veya birbiriyle çelişen öncüller (Ex Falso Quodlibet ihlali)."}

        is_valid = self.solver.verify_syllogism(premises, claim)
        if is_valid:
            return {"status": "ILZAM", "message": "Deliller iddiayı ontolojik olarak zorunlu kılmaktadır."}
        else:
            return {"status": "NAKZ", "message": "Fasid İstidlal. Öncüller tutarlı ancak lüzum bağı (Hadd-i Evsat) eksik."}