import ast
import z3
import re
from typing import Dict

class Z3ExpressionBuilder:
    """
    Sadece belirlenmiş ontolojik ID'ler ve FOL kuralları dahilinde
    Z3 ifadelerine (z3.ExprRef) dönüşüm yapan güvenlik duvarlı ve derinlik limitli AST derleyicisi.
    Faz 2 - Adım 1: Kripke Semantiği (Olası Dünyalar) ve WorldSort eklentisi.
    """
    def __init__(self, max_depth: int = 15):
        self.EntitySort = z3.DeclareSort('Entity')
        self.WorldSort = z3.DeclareSort('World') # Kripke Olası Dünyalar Uzayı
        self.predicates: Dict[str, z3.FuncDeclRef] = {}
        
        # Modal Erişim Bağıntısı (Accessibility Relation: R(w1, w2))
        self.Access = z3.Function('Access', self.WorldSort, self.WorldSort, z3.BoolSort())
        
        self.valid_identifier_pattern = re.compile(r'^[A-Za-z0-9_]+$')
        self.max_depth = max_depth

    def get_or_create_predicate(self, name: str, arity: int = 1) -> z3.FuncDeclRef:
        if not self.valid_identifier_pattern.match(name):
            raise ValueError(f"[SENTAKS İHLALİ] Geçersiz ontolojik sembol: '{name}'. Sadece ASCII/Transliterasyon desteklenir.")

        if name not in self.predicates:
            # Muvaccehât: Her yüklem artık N ariteye ek olarak bir "Dünya" (w) parametresi alır.
            domains = [self.WorldSort] + [self.EntitySort] * arity
            self.predicates[name] = z3.Function(name, *domains, z3.BoolSort())
        else:
            # Mevcut arite, WorldSort eklendiği için +1 olarak kontrol edilir
            existing_arity = self.predicates[name].arity()
            if existing_arity != arity + 1:
                raise ValueError(f"[SENTAKS İHLALİ] '{name}' predikat arite çakışması.")
                
        return self.predicates[name]

    def parse(self, expr_str: str, current_world: z3.ExprRef = None) -> z3.ExprRef:
        try:
            if current_world is None:
                current_world = z3.Const('w_base', self.WorldSort)
            tree = ast.parse(expr_str, mode='eval').body
            # Kök ayrıştırmada World (w) parametresi bound_vars içerisine gömülür
            return self._eval_node(tree, {'__world__': current_world}, current_depth=0)
        except SyntaxError as e:
            raise ValueError(f"[SENTAKS İHLALİ] Geçersiz FOL/Modal ifadesi derlenemez: {e}")

    def _eval_node(self, node: ast.AST, bound_vars: Dict[str, z3.ExprRef], current_depth: int) -> z3.ExprRef:
        if current_depth > self.max_depth:
            raise RecursionError(f"[ÇÖKÜŞ] AST Derinlik Limiti ({self.max_depth}) aşıldı.\nCombinatorial Explosion engellendi.")

        current_w = bound_vars.get('__world__')

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise SyntaxError("Yüksek dereceli fonksiyon çağrıları reddedildi.")
            
            func_name = node.func.id
            
            if func_name == 'Implies':
                return z3.Implies(self._eval_node(node.args[0], bound_vars, current_depth + 1), 
                                  self._eval_node(node.args[1], bound_vars, current_depth + 1))
            elif func_name == 'And':
                return z3.And(*[self._eval_node(arg, bound_vars, current_depth + 1) for arg in node.args])
            elif func_name == 'Or':
                return z3.Or(*[self._eval_node(arg, bound_vars, current_depth + 1) for arg in node.args])
            elif func_name == 'Not':
                return z3.Not(self._eval_node(node.args[0], bound_vars, current_depth + 1))
            
            elif func_name == 'Luzumi':
                arg_a = self._eval_node(node.args[0], bound_vars, current_depth + 1)
                arg_b = self._eval_node(node.args[1], bound_vars, current_depth + 1)
                existential_vars = [v for k, v in bound_vars.items() if k != '__world__']
                if existential_vars:
                    return z3.And(z3.Implies(arg_a, arg_b), z3.Exists([existential_vars[0]], arg_a))
                return z3.Implies(arg_a, arg_b)

            elif func_name == 'Inadi':
                arg_a = self._eval_node(node.args[0], bound_vars, current_depth + 1)
                arg_b = self._eval_node(node.args[1], bound_vars, current_depth + 1)
                return z3.And(z3.Or(arg_a, arg_b), z3.Not(z3.And(arg_a, arg_b)))
            
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
            
            else:
                # N-Ary Yüklem Çağrılarına otomatik olarak World (w) parametresi enjekte edilir
                args = [current_w] + [self._eval_node(arg, bound_vars, current_depth + 1) for arg in node.args]
                # Arite hesabı, World (w) eklendiği için node.args üzerinden hesaplanır
                arity = len(node.args)
                predicate = self.get_or_create_predicate(func_name, arity)
                return predicate(*args)

        elif isinstance(node, ast.Name):
            if node.id in bound_vars:
                return bound_vars[node.id]
            else:
                raise NameError(f"Bağlı olmayan değişken (Unbound Variable): '{node.id}' tespit edildi.")
        
        raise TypeError(f"Desteklenmeyen AST Düğümü: {type(node).__name__}.")