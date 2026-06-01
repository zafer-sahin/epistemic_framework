import ast
import z3
import re
from typing import Dict

class Z3ExpressionBuilder:
    """
    Sadece belirlenmiş ontolojik ID'ler ve FOL kuralları dahilinde
    Z3 ifadelerine (z3.ExprRef) dönüşüm yapan güvenlik duvarlı ve derinlik limitli AST derleyicisi.
    """
    def __init__(self, max_depth: int = 15):
        self.EntitySort = z3.DeclareSort('Entity')
        self.predicates: Dict[str, z3.FuncDeclRef] = {}
        
        # BRQ-01: Sadece transliterasyon ve ASCII formatına izin veren güvenlik kısıtı
        self.valid_identifier_pattern = re.compile(r'^[A-Za-z0-9_]+$')
        self.max_depth = max_depth

    def get_or_create_predicate(self, name: str, arity: int = 1) -> z3.FuncDeclRef:
        if not self.valid_identifier_pattern.match(name):
            raise ValueError(f"[SENTAKS İHLALİ] Geçersiz ontolojik sembol: '{name}'. Sadece ASCII/Transliterasyon desteklenir.")

        if name not in self.predicates:
            domains = [self.EntitySort] * arity
            self.predicates[name] = z3.Function(name, *domains, z3.BoolSort())
        else:
            existing_arity = self.predicates[name].arity()
            if existing_arity != arity:
                raise ValueError(f"[SENTAKS İHLALİ] '{name}' predikat arite çakışması. Mevcut: {existing_arity}, İstenen: {arity}")
                
        return self.predicates[name]

    def parse(self, expr_str: str) -> z3.ExprRef:
        try:
            tree = ast.parse(expr_str, mode='eval').body
            return self._eval_node(tree, {}, current_depth=0)
        except SyntaxError as e:
            raise ValueError(f"[SENTAKS İHLALİ] Geçersiz FOL ifadesi derlenemez: {e}")

    def _eval_node(self, node: ast.AST, bound_vars: Dict[str, z3.ExprRef], current_depth: int) -> z3.ExprRef:
        if current_depth > self.max_depth:
            raise RecursionError(f"[ÇÖKÜŞ] AST Derinlik Limiti ({self.max_depth}) aşıldı. Combinatorial Explosion engellendi.")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise SyntaxError("Yüksek dereceli fonksiyon çağrıları (Higher-order functions) reddedildi.")
            
            func_name = node.func.id
            
            # FOL Operatörleri
            if func_name == 'Implies':
                return z3.Implies(self._eval_node(node.args[0], bound_vars, current_depth + 1), 
                                  self._eval_node(node.args[1], bound_vars, current_depth + 1))
            elif func_name == 'And':
                return z3.And(*[self._eval_node(arg, bound_vars, current_depth + 1) for arg in node.args])
            elif func_name == 'Or':
                return z3.Or(*[self._eval_node(arg, bound_vars, current_depth + 1) for arg in node.args])
            elif func_name == 'Not':
                return z3.Not(self._eval_node(node.args[0], bound_vars, current_depth + 1))
            
            # Niceleyiciler (Quantifiers)
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
            
            # Yüklem Çağrıları (N-Ary)
            else:
                args = [self._eval_node(arg, bound_vars, current_depth + 1) for arg in node.args]
                arity = len(args)
                predicate = self.get_or_create_predicate(func_name, arity)
                return predicate(*args)

        elif isinstance(node, ast.Name):
            if node.id in bound_vars:
                return bound_vars[node.id]
            else:
                raise NameError(f"Bağlı olmayan değişken (Unbound Variable): '{node.id}' tespit edildi.")
        
        raise TypeError(f"Desteklenmeyen AST Düğümü: {type(node).__name__}. Yalnızca FOL kısıtlarına izin verilir.")