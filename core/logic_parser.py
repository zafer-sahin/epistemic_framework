import ast
import z3
from typing import Dict, Any

class Z3ExpressionBuilder:
    """
    Aristotelesçi sembolik kısıtları (string), eval() kullanmadan
    güvenli bir şekilde yerel Z3 ifadelerine (z3.ExprRef) dönüştüren AST derleyicisi.
    """
    def __init__(self):
        # Z3 Evrensel Varlık Sortu (Entity Domain)
        self.EntitySort = z3.DeclareSort('Entity')
        
        # ÖNEMLİ: Predikat Önbelleği (Cache) İlklendirmesi
        # Bu satır eksik olduğu için 'AttributeError' tetiklenmektedir.
        self.predicates: Dict[str, z3.FuncDeclRef] = {}

    def get_or_create_predicate(self, name: str, arity: int = 1) -> z3.FuncDeclRef:
        """
        Gelen sembolü (Örn: 'S', 'M', 'Nâtık') Z3 Evreninde bir Fonksiyon (Predicate) olarak tanımlar.
        P(x) -> True/False (Boolean) dönecek şekilde haritalanır.
        Z3 evreninde verilen isimde ve boyutta (arity) bir yüklem yaratır.
        Eğer yüklem daha önce yaratılmışsa ve boyutu eşleşiyorsa onu döndürür.
        """
        if name not in self.predicates:
            # Arite sayısı kadar EntitySort (girdi) domaini oluştur.
            domains = [self.EntitySort] * arity
            self.predicates[name] = z3.Function(name, *domains, z3.BoolSort())
        else:
            # Fail-Fast: Önceden tanımlı yüklemin parametre sayısıyla mevcut çağrı uyuşmuyorsa çökert.
            existing_arity = self.predicates[name].arity()
            if existing_arity != arity:
                raise ValueError(f"[SENTAKS İHLALİ] '{name}' predikatı {existing_arity} parametreli tanımlı, ancak {arity} parametre ile çağrıldı.")
                
        return self.predicates[name]

    def parse(self, expr_str: str) -> z3.ExprRef:
        """
        String ifadeyi güvenli Python AST düğümlerine ayrıştırır ve Z3 motoruna besler.
        """
        tree = ast.parse(expr_str, mode='eval').body
        return self._eval_node(tree, {})

    def _eval_node(self, node: ast.AST, bound_vars: Dict[str, z3.ExprRef]) -> z3.ExprRef:
        """
        Öz-yinelemeli (recursive) AST düğüm gezgini (Node Visitor).
        """
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise SyntaxError("Yüksek dereceli fonksiyon çağrıları (Higher-order functions) desteklenmiyor.")
            
            func_name = node.func.id
            
            # Z3 Temel Mantıksal Operatörleri
            if func_name == 'Implies':
                return z3.Implies(self._eval_node(node.args[0], bound_vars), 
                                  self._eval_node(node.args[1], bound_vars))
            elif func_name == 'And':
                return z3.And(*[self._eval_node(arg, bound_vars) for arg in node.args])
            elif func_name == 'Or':
                return z3.Or(*[self._eval_node(arg, bound_vars) for arg in node.args])
            elif func_name == 'Not':
                return z3.Not(self._eval_node(node.args[0], bound_vars))
            
            # Niceleyiciler (Quantifiers): Forall([x], body) / Exists([x], body)
            elif func_name in ('Forall', 'Exists'):
                if not isinstance(node.args[0], ast.List):
                    raise SyntaxError("Niceleyici değişkenleri liste formatında olmalıdır. Örn: [x]")
                
                var_nodes = node.args[0].elts
                new_bound_vars = bound_vars.copy() # Scope izolasyonu
                z3_vars = []
                
                for v in var_nodes:
                    if isinstance(v, ast.Name):
                        # Değişkeni Z3 Const olarak tanımla ve Scope'a ekle
                        z3_var = z3.Const(v.id, self.EntitySort)
                        new_bound_vars[v.id] = z3_var
                        z3_vars.append(z3_var)
                    else:
                        raise ValueError(f"Geçersiz niceleyici değişkeni tipi: {type(v)}")
                
                # Gövdeyi (body) yeni scope değişkenleriyle değerlendir
                body_expr = self._eval_node(node.args[1], new_bound_vars)
                
                if func_name == 'Forall':
                    return z3.ForAll(z3_vars, body_expr)
                else:
                    return z3.Exists(z3_vars, body_expr)
            
            # Yüklem Çağrıları (Predicate Calls): S(x), M(x), Amil(x, y) vb. N-Ary
            else:
                args = [self._eval_node(arg, bound_vars) for arg in node.args]
                arity = len(args) # Parametre sayısını dinamik olarak hesapla
                predicate = self.get_or_create_predicate(func_name, arity)
                return predicate(*args)

        elif isinstance(node, ast.Name):
            # Karşılaşılan değişken (Örn: 'x') mutlaka bir niceleyici scope'unda bağlanmış (bound) olmalıdır.
            if node.id in bound_vars:
                return bound_vars[node.id]
            else:
                raise NameError(f"Bağlı olmayan değişken (Unbound Variable): '{node.id}' tespit edildi. Kısıtlar kapalı formüllerde (Closed Formulas) yazılmalıdır.")
        
        raise TypeError(f"Desteklenmeyen AST Düğümü: {type(node).__name__}")