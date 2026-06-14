import ast
import z3
import re
from typing import Dict
from core.exceptions import DiachronicViolationError

class Z3ExpressionBuilder:
    """
    .. pedagojik_anlati:: Kripke Uzayı ve Z3 Determinizmi
    Sadece belirlenmiş ontolojik ID'ler ve FOL kuralları dahilinde Z3 ifadelerine (z3.ExprRef) 
    dönüşüm yapan güvenlik duvarlı ve derinlik limitli AST derleyicisi.
    Faz 1 - Adım 4 kapsamında: İlm-i Nahiv'deki Rabıta (Identity), İnne'nin Ameli (Necessity), 
    ve Müteallak (SpaceSort) gibi klasik Arapça ontolojilerinin Modal Mantık karşılıkları
    (Kripke Semantiği) sisteme entegre edilmiştir.
    [FAZ 3 ENTEGRASYONU]: İsm-i Mevsûl (Sıla Cümleleri) için 'SubClauseSila' 
    (Lambda Soyutlaması ve Küme Kesişimi) otonom düğümleri eklenmiştir.
    """
    def __init__(self, max_depth: int = 15):
        # 1. Ontolojik Temel Evren (Sorts)
        self.EntitySort = z3.DeclareSort('Entity')       # Mevcudat (Varlıklar)
        self.WorldSort = z3.DeclareSort('World')         # Kripke Olası Dünyalar Uzayı
        self.TimeSortZati = z3.DeclareSort('TimeZati')   # Şemsiyye Kiplikleri İçin Zâtî Zaman (De re)
        self.TimeSortVasfi = z3.DeclareSort('TimeVasfi') # Şemsiyye Kiplikleri İçin Vasfî Zaman (De dicto)
        self.SpaceSort = z3.DeclareSort('Space')         # Müteallak ve Harf-i Cerler İçin Mekânsal Uzay
        
        self.predicates: Dict[str, z3.FuncDeclRef] = {}
        
        # 2. Epistemik ve Ontolojik Sabiteler (Axiomatic Functions)
        # Modal Erişim Bağıntısı (Accessibility Relation: R(w1, w2))
        self.Access = z3.Function('Access', self.WorldSort, self.WorldSort, z3.BoolSort())
        
        # Dinamik Mantık Zaman Geçişi (Fa-i Füzâiyye için t1 -> t2 sıçraması)
        self.TimeTransition = z3.Function('TimeTransition', self.TimeSortVasfi, self.TimeSortVasfi, z3.BoolSort())

        # Mekânsal Bağlantı (Müteallak) Fonksiyonu: Entity'nin belirli bir mekânda (Space) bulunması
        self.LocatedIn = z3.Function('LocatedIn', self.WorldSort, self.TimeSortZati, self.TimeSortVasfi, self.SpaceSort, self.EntitySort, z3.BoolSort())
        
        self.valid_identifier_pattern = re.compile(r'^[A-Za-z0-9_]+$')
        self.max_depth = max_depth

    def get_or_create_predicate(self, name: str, arity: int = 1) -> z3.FuncDeclRef:
        """
        .. mantik_kurali:: Çok-Boyutlu Yüklem (N-Ary Predicate) İnşası
        Sıradan bir FOL motoru `Daraba(Zeyd, Amr)` şeklinde 2-arite kullanırken, 
        İslâm ontolojisindeki nedensellik; eylemin Dünya(w), Zâtî Zaman(t_zati), Vasfî Zaman(t_vasfi) 
        ve Mekân(s) kısıtlarından bağımsız düşünülemeyeceğini öngörür. Bu metod, ariteyi otonom 
        olarak +4 boyutla genişletir.
        """
        if not self.valid_identifier_pattern.match(name):
            raise ValueError(f"[SENTAKS İHLALİ] Geçersiz ontolojik sembol: '{name}'. Sadece ASCII/Transliterasyon desteklenir.")

        if name not in self.predicates:
            # Muvaccehât ve Mekân: Her yüklem artık N ariteye ek olarak W, T_zati, T_vasfi ve S alır.
            domains = [self.WorldSort, self.TimeSortZati, self.TimeSortVasfi, self.SpaceSort] + [self.EntitySort] * arity
            self.predicates[name] = z3.Function(name, *domains, z3.BoolSort())
        else:
            existing_arity = self.predicates[name].arity()
            if existing_arity != arity + 4:
                raise ValueError(f"[SENTAKS İHLALİ] '{name}' predikat arite çakışması. Beklenen {arity+4}, Bulunan: {existing_arity}")
                
        return self.predicates[name]

    def parse(self, expr_str: str, current_world: z3.ExprRef = None, current_time_zati: z3.ExprRef = None, current_time_vasfi: z3.ExprRef = None, current_space: z3.ExprRef = None) -> z3.ExprRef:
        try:
            if current_world is None:
                current_world = z3.Const('w_base', self.WorldSort)
            if current_time_zati is None:
                current_time_zati = z3.Const('t_zati_base', self.TimeSortZati)
            if current_time_vasfi is None:
                current_time_vasfi = z3.Const('t_vasfi_base', self.TimeSortVasfi)
            if current_space is None:
                current_space = z3.Const('s_base', self.SpaceSort)
                
            tree = ast.parse(expr_str, mode='eval').body
            
            return self._eval_node(tree, {
                '__world__': current_world, 
                '__time_zati__': current_time_zati, 
                '__time_vasfi__': current_time_vasfi,
                '__space__': current_space
            }, current_depth=0)
        except SyntaxError as e:
            raise ValueError(f"[SENTAKS İHLALİ] Geçersiz FOL/Modal ifadesi derlenemez: {e}")

    def _eval_node(self, node: ast.AST, bound_vars: Dict[str, z3.ExprRef], current_depth: int) -> z3.ExprRef:
        if current_depth > self.max_depth:
            raise RecursionError(f"[ÇÖKÜŞ] AST Derinlik Limiti ({self.max_depth}) aşıldı.\nCombinatorial Explosion engellendi.")

        current_w = bound_vars.get('__world__')
        current_t_zati = bound_vars.get('__time_zati__')
        current_t_vasfi = bound_vars.get('__time_vasfi__')
        current_s = bound_vars.get('__space__')

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise SyntaxError("Yüksek dereceli fonksiyon çağrıları reddedildi.")
            
            func_name = node.func.id
            
            # ------------------------------------------------------------------
            # 1. STANDART FOL BOOLEAN KÖPRÜLERİ
            # ------------------------------------------------------------------
            if func_name == 'Implies':
                return z3.Implies(self._eval_node(node.args[0], bound_vars, current_depth + 1), 
                                  self._eval_node(node.args[1], bound_vars, current_depth + 1))
            elif func_name == 'And':
                return z3.And(*[self._eval_node(arg, bound_vars, current_depth + 1) for arg in node.args])
            elif func_name == 'Or':
                return z3.Or(*[self._eval_node(arg, bound_vars, current_depth + 1) for arg in node.args])
            elif func_name == 'Not':
                return z3.Not(self._eval_node(node.args[0], bound_vars, current_depth + 1))
            
            # ------------------------------------------------------------------
            # 2. İLM-İ NAHİV SENTAKTİK-ONTOLOJİK MÜHÜRLERİ (FAZ 1 VE 3 EKLENTİLERİ)
            # ------------------------------------------------------------------
            elif func_name == 'Identity':
                # Bedel ve Zero-Copula: İki değişkenin Kripke uzayında aynı varlık pointer'ına (EntitySort) eşitlenmesi.
                arg_a = self._eval_node(node.args[0], bound_vars, current_depth + 1)
                arg_b = self._eval_node(node.args[1], bound_vars, current_depth + 1)
                return arg_a == arg_b

            elif func_name == 'Necessity':
                # İnne ve Kardeşleri: Önermenin mümkün tüm olası dünyalarda (Zorunlu) geçerli olması
                w_prime = z3.Const(f'w_prime_{current_depth}', self.WorldSort)
                new_vars = bound_vars.copy()
                new_vars['__world__'] = w_prime
                body_expr = self._eval_node(node.args[0], new_vars, current_depth + 1)
                return z3.ForAll([w_prime], z3.Implies(self.Access(current_w, w_prime), body_expr))

            elif func_name == 'DynamicTransition':
                # Fâ-i Füzâiyye: Zaman düzleminde ardışık bir zıplama (State Shift) operasyonu
                arg_a = self._eval_node(node.args[0], bound_vars, current_depth + 1)
                
                t_prime = z3.Const(f't_vasfi_prime_{current_depth}', self.TimeSortVasfi)
                new_vars = bound_vars.copy()
                new_vars['__time_vasfi__'] = t_prime
                arg_b = self._eval_node(node.args[1], new_vars, current_depth + 1)
                
                return z3.And(arg_a, z3.Exists([t_prime], z3.And(self.TimeTransition(current_t_vasfi, t_prime), arg_b)))
                
            elif func_name == 'SubClauseSila':
                # [FAZ 3 ENTEGRASYONU] İsm-i Mevsûl (Sıla Cümlesi): Lambda soyutlamasının 
                # Z3 FOL matrisindeki karşılığı olarak Kesişim (Intersection / z3.And).
                return z3.And(*[self._eval_node(arg, bound_vars, current_depth + 1) for arg in node.args])

            # ------------------------------------------------------------------
            # 3. ŞARTLI VE AYRIK ÖNERMELER (ŞEMSİYYE DİYALEKTİĞİ)
            # ------------------------------------------------------------------
            elif func_name == 'Luzumi':
                arg_a = self._eval_node(node.args[0], bound_vars, current_depth + 1)
                arg_b = self._eval_node(node.args[1], bound_vars, current_depth + 1)
                existential_vars = [v for k, v in bound_vars.items() if k not in ('__world__', '__time_zati__', '__time_vasfi__', '__space__')]
                if existential_vars:
                    return z3.And(z3.Implies(arg_a, arg_b), z3.Exists([existential_vars[0]], arg_a))
                return z3.Implies(arg_a, arg_b)

            elif func_name == 'Inadi_Hakikiyye':
                arg_a = self._eval_node(node.args[0], bound_vars, current_depth + 1)
                arg_b = self._eval_node(node.args[1], bound_vars, current_depth + 1)
                return z3.And(z3.Or(arg_a, arg_b), z3.Not(z3.And(arg_a, arg_b)))
                
            elif func_name == 'Inadi_Maniatul_Cem':
                arg_a = self._eval_node(node.args[0], bound_vars, current_depth + 1)
                arg_b = self._eval_node(node.args[1], bound_vars, current_depth + 1)
                return z3.Not(z3.And(arg_a, arg_b))
                
            elif func_name == 'Inadi_Maniatul_Huluv':
                arg_a = self._eval_node(node.args[0], bound_vars, current_depth + 1)
                arg_b = self._eval_node(node.args[1], bound_vars, current_depth + 1)
                return z3.Or(arg_a, arg_b)
            
            # ------------------------------------------------------------------
            # 4. NİCELEYİCİLER (QUANTIFIERS)
            # ------------------------------------------------------------------
            elif func_name in ('Forall', 'Exists'):
                if not isinstance(node.args[0], ast.List):
                    raise SyntaxError("Niceleyici değişkenleri liste formatında olmalıdır. Örn: [x]")
                
                var_nodes = node.args[0].elts
                new_bound_vars = bound_vars.copy() 
                z3_vars = []
                
                for v in var_nodes:
                    if isinstance(v, ast.Name):
                        z3_var = z3.Const(v.id, self.EntitySort)
                        new_bound_vars[v.id] = z3_var
                        z3_vars.append(z3_var)
                    else:
                        raise ValueError(f"[UNKNOWN_VARIABLE] Geçersiz niceleyici tipi: {type(v)}")
                
                body_expr = self._eval_node(node.args[1], new_bound_vars, current_depth + 1)
                
                if func_name == 'Forall':
                    return z3.ForAll(z3_vars, body_expr)
                else:
                    return z3.Exists(z3_vars, body_expr)
            
            # ------------------------------------------------------------------
            # 5. DİNAMİK YÜKLEM (N-ARY PREDICATE) ÜRETİMİ
            # ------------------------------------------------------------------
            else:
                args = [current_w, current_t_zati, current_t_vasfi, current_s] + [self._eval_node(arg, bound_vars, current_depth + 1) for arg in node.args]
                arity = len(node.args)
                predicate = self.get_or_create_predicate(func_name, arity)
                return predicate(*args)

        elif isinstance(node, ast.Name):
            if node.id in bound_vars:
                return bound_vars[node.id]
            else:
                # Otonom Serbest Değişken Tespiti ve EntitySort Ataması
                new_const = z3.Const(node.id, self.EntitySort)
                bound_vars[node.id] = new_const
                return new_const
        
        raise TypeError(f"Desteklenmeyen AST Düğümü: {type(node).__name__}.")