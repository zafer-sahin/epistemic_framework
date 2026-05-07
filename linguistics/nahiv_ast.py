import z3
from typing import List, Dict, Tuple
from core.logic_engine import AristotelianSolver

class NahivDependencyCompiler:
    """
    Arapça Sentaktik Bağımlılık Ağacını (Nahiv AST), Z3 Birinci Dereceden Mantık (FOL) 
    kısıtlarına derler. Âmil-Ma'mûl (Yöneten-Yönetilen) teorisini matematikselleştirir.
    Statik ontolojiyi bozmadan çalışma zamanında geçici (ephemeral) durum analizi yapar.
    """
    def __init__(self, solver: AristotelianSolver):
        self.solver = solver
        self.builder = solver.builder

    def compile_amil_mamul(self, amil_id: str, mamul_id: str, relation_type: str, irab_state: str) -> List[z3.ExprRef]:
        """
        Sentaktik bir ilişkiyi, Z3 evreninde spesifik kelime sabitleri (Constants) 
        üzerinden ilişkisel bir FOL matrisine dönüştürür.
        Örn: (Darabe, Zeyd, 'Fail', 'Marfu') -> 
        Z3 Kısıtları: Fail(Darabe, Zeyd) AND Marfu(Zeyd)
        """
        # Kelimeleri (Token) Z3 evreninde geçici sabitler (Const) olarak tanımla
        amil_const = z3.Const(amil_id, self.builder.EntitySort)
        mamul_const = z3.Const(mamul_id, self.builder.EntitySort)
        
        constraints = []
        
        # 1. İlişki Kısıtı: N-Ary Predicate (Örn: Fail(x, y))
        rel_predicate = self.builder.get_or_create_predicate(relation_type, arity=2)
        constraints.append(rel_predicate(amil_const, mamul_const))
        
        # 2. İ'rab Kısıtı: Unary Predicate (Örn: Marfu(y))
        irab_predicate = self.builder.get_or_create_predicate(irab_state, arity=1)
        constraints.append(irab_predicate(mamul_const))
        
        return constraints


    def verify_sentence_ast(self, dependencies: List[Tuple[str, str, str, str]], lexicon: Dict[str, str] = None) -> bool:
        """
        Cümlenin sentaktik ağacının (Dependencies), ontolojik evrendeki mevcut 
        kurallarla (Örn: Sadece isimler fail olabilir) çelişip çelişmediğini test eder.
        AST'yi ontolojik Sözlük (Lexicon) ve Evrensel Gramer Kısıtlarıyla çarparak doğrular.
        """
        self.solver.solver.push()
        try:
            # 1. EVRENSEL NAHİV KISITLARI (Axioms of Syntax)
            # Fail ve Meful ilişkilerinin ontolojik doğasını Z3'e öğret.
            x, y = z3.Consts('x y', self.builder.EntitySort)
            Fail = self.builder.get_or_create_predicate('Fail', arity=2)
            Meful = self.builder.get_or_create_predicate('Meful', arity=2)
            Mubteda_Haber = self.builder.get_or_create_predicate('Mubteda_Haber', arity=2)
            Fiil = self.builder.get_or_create_predicate('Fiil', arity=1)
            Ism = self.builder.get_or_create_predicate('Ism', arity=1)

            # YENİ VEKTÖR: Mutlak Dışlama (Disjointness) Kuralı
            # Bir varlık (Kelime) aynı anda hem İsim hem Fiil olamaz.
            self.solver.solver.add(z3.ForAll([x], z3.Not(z3.And(Fiil(x), Ism(x)))))
            
            # Kural: Fail veya Meful ilişkisi varsa, amil Fiil'dir, mamul İsim'dir.
            self.solver.solver.add(z3.ForAll([x, y], z3.Implies(Fail(x, y), z3.And(Fiil(x), Ism(y)))))
            self.solver.solver.add(z3.ForAll([x, y], z3.Implies(Meful(x, y), z3.And(Fiil(x), Ism(y)))))

            # Mübteda-Haber ilişkisinde her iki argüman da İsim olmak zorundadır.
            # $ \forall x, y . \text{Mubteda\_Haber}(x, y) \rightarrow \text{Ism}(x) \land \text{Ism}(y) $
            self.solver.solver.add(z3.ForAll([x, y], z3.Implies(Mubteda_Haber(x, y), z3.And(Ism(x), Ism(y)))))

            # 2. LEKSİKOLOJİK ENJEKSİYON (Kelime Türlerinin Tanımlanması)
            if lexicon:
                for word, word_type in lexicon.items():
                    word_const = z3.Const(word, self.builder.EntitySort)
                    type_predicate = self.builder.get_or_create_predicate(word_type, arity=1)
                    # Örn: Fiil(Daraba) kısıtını Z3'e ekle
                    self.solver.solver.add(type_predicate(word_const))

            # 3. SENTAKTİK AĞACIN ENJEKSİYONU (AST)
            for amil, mamul, rel, irab in dependencies:
                z3_exprs = self.compile_amil_mamul(amil, mamul, rel, irab)
                for expr in z3_exprs:
                    self.solver.solver.add(expr)
            
            # Cümlenin sentaktik tutarlılığını Z3 çözücüsü ile doğrula
            is_valid = (self.solver.solver.check() == z3.sat)
            return is_valid
            
        except Exception as e:
            raise RuntimeError(f"[ÇÖKÜŞ] Nahiv AST Derleme Hatası: {e}")
        finally:
            # Analiz bittiğinde geçici cümle state'ini (kısıtları) bellekten sil
            # Böylece ontolojik evrenin sıfır entropi kuralı korunur.
            self.solver.solver.pop()


    def suggest_dependencies(self, tokens: List[str], lexicon: Dict[str, str]) -> List[Tuple[str, str, str, str]]:
            """
            Token dizisi ve Leksikon üzerinden otomatik Bağımlılık Ağacı (AST) önerir.
            Fiil Cümlesi ve İsim Cümlesi (Önerme) matrislerini ayırır.
            """
            dependencies = []
            amil = None
            
            # 1. FİİL CÜMLESİ (Verbal Sentence) KONTROLÜ
            for token in tokens:
                if lexicon.get(token) == "Fiil":
                    amil = token
                    break
            
            # 2. İSİM CÜMLESİ (Nominal Sentence / Kadiyye) KONTROLÜ
            if not amil:
                # Mantık ilminde önermeler (Da'vâ) genellikle iki merfu isimden oluşur.
                marfu_tokens = [t for t in tokens if t.lower().endswith('un')]
                if len(marfu_tokens) >= 2:
                    mubteda = marfu_tokens[0]
                    haber = marfu_tokens[1]
                    # Haber (Yüklem), Mübteda'ya (Özne) isnad edilir.
                    dependencies.append((haber, mubteda, 'Mubteda_Haber', 'Marfu'))
                return dependencies

            # 3. FİİL CÜMLESİ BAĞIMLILIKLARI
            for token in tokens:
                if token == amil: 
                    continue
                if token.lower().endswith('un'):
                    dependencies.append((amil, token, 'Fail', 'Marfu'))
                elif token.lower().endswith('an'):
                    dependencies.append((amil, token, 'Meful', 'Mansub'))
                elif token.lower().endswith('in'):
                    dependencies.append((amil, token, 'Majrur', 'Majrur'))
                    
            return dependencies