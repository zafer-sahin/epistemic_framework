import z3
from typing import Dict, Any, Tuple, Union, List
from collections import OrderedDict
from core.logic_engine import AristotelianSolver
from linguistics.ilm_wad_adapter import SemanticStatementIR, NestedPredicate

# Mübteda ile haber arasındaki hükmî nisbet (haml) ilişkileri.
HAML_RELATIONS = ("Rel_Rabita_Predication", "Rel_Rabita_Identity", "Rel_Mubteda_Haber")

class Layer3SMTCircuitBreaker:
    """
    Z3 Birinci Dereceden Mantık (FOL) Derleyicisi ve Devre Kesici.
    [FAZ 1 ENTEGRASYONU - BİLGİ]: Gayr-i Munsarif (Diptote) zırhı upstream (Sarf ve Nahiv) 
    katmanlarında çözümlendiği için, bu katmanın deterministik _build_z3_expr metodu 
    hiçbir ek koda ihtiyaç duymadan Semantic Shift'i (Fail-Meful kaymasını) matematiksel 
    olarak engeller.
    [FAZ 3 ENTEGRASYONU]: 'İnne' ve kardeşlerinin ürettiği 'Epistemic_Necessity' operatörü 
    Zorunluluk Operatörü (□) olarak Kripke uzayına (z3.ForAll ile) işlenmiştir.
    [FAZ 3.1 ENTEGRASYONU]: İsm-i Mevsûl (`SubClause_Sila`), Âid Zamiri (`Rel_Pointer_Alias`) ve
    Cümle-i Fiiliye Haber (`Rel_Rabita_Action`) yapıları SMT çözümleyiciye tanıtılmıştır.
    [FAZ 4 ENTEGRASYONU]: Kripke Uzayına Mekânsal Boyut (SpaceSort) eklendi. Tüm Modal,
    Deontik ve Epistemik operatörler s_const (Space) düzleminde kısıtlanmıştır.
    [FAZ 5 ENTEGRASYONU]: Mekân (Zarfiyye) ve Harf-i Cer müteallak bağları için Çift-Yönlü
    Zerk (Dual-Injection) ve Kasr (Hasr) döngülerinde Arity Mismatch koruması entegre edildi.
    [HATA DÜZELTMESİ - P0-2/P0-3]: Te'vil köprüleri kalıcı (global) değildir; yalnızca verildikleri
    kontrolün push/pop kapsamında, izlenerek (unsat core'da adlarıyla) yer alır. Önbellek anahtarı
    IR'ye ek olarak köprüleri ve çözücü bağlamını içerir; önbellek boyutu hükmü değil, yalnızca
    performansı etkiler.
    [HATA DÜZELTMESİ - P0-7]: Çapraz-ekol mu'ârazada iki okuma bu çözücünün ontolojisiyle birlikte
    sınanır (`execute_joint_sat_check`); karşılaştırma ontolojisiz bir Optimize örneğinde yapılmaz.
    [HATA DÜZELTMESİ - P0-5]: IR'deki sabitler kavramlar değil, lafızların gösterdiği fertlerdir. Haml,
    mübtedanın ferdinin haberle varlıkta birleşmesi (ittihâd) ya da haberin onda kâim olmasıdır. İzafet
    özdeşlik değil nisbettir; bir arazın izafeti, onun muzâfun ileyhte kâim olmasıdır.
    """
    def __init__(self, solver: AristotelianSolver, timeout_ms: int = 3000, max_cache_size: int = 1000):
        self.core_solver = solver
        self.max_cache_size = max_cache_size

        self.core_solver.solver.set("timeout", timeout_ms)
        self.core_solver.solver.set("smt.mbqi", True)
        self.core_solver.solver.set("smt.macro_finder", True)

        self._memoization_cache: Dict[Tuple, Dict[str, Any]] = OrderedDict()

    def _freeze_ir_matrix(self, predicates: list) -> Tuple:
        frozen_elements = []
        for item in predicates:
            if isinstance(item, tuple):
                frozen_elements.append(item)
            elif isinstance(item, NestedPredicate):
                frozen_elements.append((item.operator, self._freeze_ir_matrix(item.args)))
        return tuple(sorted(frozen_elements, key=lambda x: str(x)))

    def _build_z3_expr(self, item: Union[Tuple[str, str, int], NestedPredicate], w_const: z3.ExprRef, tz_const: z3.ExprRef, tv_const: z3.ExprRef, s_const: z3.ExprRef) -> z3.ExprRef:
        if isinstance(item, tuple):
            pred_id, arg_id, arity = item
            if arity == 1:
                entity_const = z3.Const(arg_id, self.core_solver.builder.EntitySort)
                predicate = self.core_solver.builder.get_or_create_predicate(pred_id, arity=1)
                return predicate(w_const, tz_const, tv_const, s_const, entity_const)
            elif arity == 2:
                amil_str, mamul_str = arg_id.split('::', 1) 
                amil_const = z3.Const(amil_str, self.core_solver.builder.EntitySort)
                mamul_const = z3.Const(mamul_str, self.core_solver.builder.EntitySort)
                
                # [FAZ 3 ENTEGRASYONU] Rel_Pointer_Alias: Hafıza eşdeğerliği (âid zamiri merciinin ferdidir)
                if pred_id == "Rel_Pointer_Alias":
                    return amil_const == mamul_const

                # [HATA DÜZELTMESİ - P0-5] Haml: haber (amil) mübtedanın (mamul) ferdiyle ya varlıkta birleşir
                # (haml-i hüve hüve: "Zeyd insandır") ya da onda kâim olur (haml-i iştikâk: "Zeyd dâribdir").
                # Hangisinin mümkün olduğuna ontoloji karar verir: cevher başka bir şeyde kâim olmaz.
                if pred_id in HAML_RELATIONS:
                    nisbet = self.core_solver.builder.get_or_create_predicate(pred_id, arity=2)
                    kiyam = self.core_solver.builder.get_or_create_predicate("Rel_Kiyam", arity=2)
                    return z3.And(
                        nisbet(w_const, tz_const, tv_const, s_const, amil_const, mamul_const),
                        z3.Or(mamul_const == amil_const, kiyam(w_const, tz_const, tv_const, s_const, amil_const, mamul_const))
                    )
                
                # [FAZ 5 ENTEGRASYONU] Çift-Yönlü Mekân/Müteallak Zerk İşlemi
                if pred_id == "LocatedIn":
                    # 1. Kripke Tahayyuz Kısıtı (Abstract Space Binding)
                    loc_constraint = self.core_solver.builder.LocatedIn(w_const, tz_const, tv_const, s_const, amil_const)
                    # 2. Zarfiyye Ontolojik Bağıntısı (Concrete Entity-to-Entity)
                    zarfiyye_pred = self.core_solver.builder.get_or_create_predicate("Rel_Zarfiyye", arity=2)
                    rel_constraint = zarfiyye_pred(w_const, tz_const, tv_const, s_const, amil_const, mamul_const)
                    return z3.And(loc_constraint, rel_constraint)

                # [FAZ 3 ENTEGRASYONU] Cümle-i Fiiliye Haber
                # Özneyi doğrudan eylem mantığına birleştirir
                if pred_id == "Rel_Rabita_Action":
                    action_pred = self.core_solver.builder.get_or_create_predicate("Role_Action", arity=1)
                    return action_pred(w_const, tz_const, tv_const, s_const, mamul_const)

                predicate = self.core_solver.builder.get_or_create_predicate(pred_id, arity=2)
                return predicate(w_const, tz_const, tv_const, s_const, amil_const, mamul_const)
            else:
                raise ValueError(f"[SENTAKS İHLALİ] Desteklenmeyen arite: {arity}")
        else:
            args = [self._build_z3_expr(a, w_const, tz_const, tv_const, s_const) for a in item.args]
            
            # [FAZ 3 ENTEGRASYONU] Sıla Cümlesi (İsm-i Mevsûl Lambda İzdüşümü)
            # Sıla cümlesindeki tüm önermelerin, Mevsûl varlığıyla eş zamanlı (And) geçerli olmasını sağlar.
            if item.operator == "SubClause_Sila":
                return z3.And(args)
            elif item.operator == "Luzumi":
                if len(args) == 2:
                    return z3.Implies(args[0], args[1])
                return z3.And(args) 
            elif item.operator == "Inadi_Hakikiyye":
                if len(args) == 2:
                    return z3.And(z3.Or(args[0], args[1]), z3.Not(z3.And(args[0], args[1])))
                return z3.Or(args)
            elif item.operator == "Inadi_Maniatul_Cem":
                if len(args) == 2:
                    return z3.Not(z3.And(args[0], args[1]))
                return z3.Not(z3.And(args))
            elif item.operator == "Inadi_Maniatul_Huluv":
                if len(args) == 2:
                    return z3.Or(args[0], args[1])
                return z3.Or(args)
            elif item.operator == "Wajib_Fiqh":
                body = args[0] if len(args) == 1 else z3.And(args)
                # [FAZ 2/4 ENTEGRASYONU] Deontik Emir: Vasfî zaman ve Vasfî mekân lüzumiyeti.
                return z3.ForAll([w_const, tv_const, s_const], body)
            elif item.operator == "Haram_Fiqh":
                body = args[0] if len(args) == 1 else z3.And(args)
                # [FAZ 2/4 ENTEGRASYONU] Nehiyler (Yasaklar): Vasfî zaman ve mekânda varoluşsal yokluk.
                return z3.Not(z3.Exists([w_const, tv_const, s_const], body))
            elif item.operator == "Istifham_Inkari":
                body = args[0] if len(args) == 1 else z3.And(args)
                return z3.ForAll([w_const, tz_const, tv_const, s_const], z3.Not(body))
            elif item.operator == "Epistemic_Necessity":
                # [FAZ 3/4 ENTEGRASYONU] İnne ve Kardeşleri (Tahkik / Yakîn Makamı)
                body = args[0] if len(args) == 1 else z3.And(args)
                return z3.ForAll([w_const, tz_const, tv_const, s_const], body)
            elif item.operator == "Exists_Virtual_Agent":
                # [FAZ 2 ENTEGRASYONU] Edilgen Fiil/Mebnî lil-Meçhul Ontolojik Zırhı
                # Unknown_Agent_Virtual Skolem sabiti olmaktan çıkarılarak varoluşsal niceleyici (∃x) yapılır.
                body = args[0] if len(args) == 1 else z3.And(args)
                virtual_agent_const = z3.Const("Unknown_Agent_Virtual", self.core_solver.builder.EntitySort)
                return z3.Exists([virtual_agent_const], body)
            elif item.operator == "Kasr_Sifat_to_Mevsuf":
                base_truth = args[0] if len(args) == 1 else z3.And(args)
                exclusion_axioms = []
                
                for a in item.args:
                    if isinstance(a, tuple) and a[2] == 2 and '::' in a[1]:
                        pred_id, arg_id, arity = a
                        amil_str, mamul_str = arg_id.split('::', 1)
                        
                        # [FAZ 5 YAMASI] Arity Mismatch Koruması ve System Constraints Baypası
                        if pred_id in ["Rel_Mudaf_MudafIlayh", "Rel_Mubteda_Haber", "Rel_Pointer_Alias"]:
                            continue
                            
                        target_pred_id = "Rel_Zarfiyye" if pred_id == "LocatedIn" else pred_id
                        predicate = self.core_solver.builder.get_or_create_predicate(target_pred_id, arity=2)
                        
                        y_kasr = z3.Const('y_kasr', self.core_solver.builder.EntitySort)
                        amil_const = z3.Const(amil_str, self.core_solver.builder.EntitySort)
                        mamul_const = z3.Const(mamul_str, self.core_solver.builder.EntitySort)
                        
                        exclusion = z3.ForAll([w_const, tz_const, tv_const, s_const, y_kasr],
                            z3.Implies(
                                y_kasr != mamul_const,
                                z3.Not(predicate(w_const, tz_const, tv_const, s_const, amil_const, y_kasr))
                            )
                        )
                        exclusion_axioms.append(exclusion)
                        
                if exclusion_axioms:
                    return z3.And(base_truth, *exclusion_axioms)
                return base_truth
            elif item.operator == "Kasr_Mevsuf_to_Sifat":
                base_truth = args[0] if len(args) == 1 else z3.And(args)
                exclusion_axioms = []
                
                for a in item.args:
                    if isinstance(a, tuple) and a[2] == 2 and '::' in a[1]:
                        pred_id, arg_id, arity = a
                        amil_str, mamul_str = arg_id.split('::', 1)
                        
                        # [FAZ 5 YAMASI] Arity Mismatch Koruması ve System Constraints Baypası
                        if pred_id in ["Rel_Mudaf_MudafIlayh", "Rel_Mubteda_Haber", "Rel_Pointer_Alias"]:
                            continue
                            
                        target_pred_id = "Rel_Zarfiyye" if pred_id == "LocatedIn" else pred_id
                        predicate = self.core_solver.builder.get_or_create_predicate(target_pred_id, arity=2)
                        
                        x_kasr = z3.Const('x_kasr', self.core_solver.builder.EntitySort)
                        amil_const = z3.Const(amil_str, self.core_solver.builder.EntitySort)
                        mamul_const = z3.Const(mamul_str, self.core_solver.builder.EntitySort)
                        
                        exclusion = z3.ForAll([w_const, tz_const, tv_const, s_const, x_kasr],
                            z3.Implies(
                                x_kasr != amil_const,
                                z3.Not(predicate(w_const, tz_const, tv_const, s_const, x_kasr, mamul_const))
                            )
                        )
                        exclusion_axioms.append(exclusion)
                        
                if exclusion_axioms:
                    return z3.And(base_truth, *exclusion_axioms)
                return base_truth
            else:
                raise ValueError(f"[SENTAKS İHLALİ] Bilinmeyen hiyerarşik operatör: {item.operator}")

    def _inject_structural_axioms(self) -> None:
        w_var = z3.Const('w_vaz', self.core_solver.builder.WorldSort)
        tz_var = z3.Const('tz_vaz', self.core_solver.builder.TimeSortZati)
        tv_var = z3.Const('tv_vaz', self.core_solver.builder.TimeSortVasfi)
        s_var = z3.Const('s_vaz', self.core_solver.builder.SpaceSort)
        x_var = z3.Const('x_var', self.core_solver.builder.EntitySort)
        y_var = z3.Const('y_var', self.core_solver.builder.EntitySort)

        role_agent = self.core_solver.builder.get_or_create_predicate("Role_Agent", arity=1)
        role_patient = self.core_solver.builder.get_or_create_predicate("Role_Patient", arity=1)
        role_action = self.core_solver.builder.get_or_create_predicate("Role_Action", arity=1)

        agent_axiom = z3.ForAll(
            [w_var, tz_var, tv_var, s_var, x_var],
            z3.Implies(
                role_agent(w_var, tz_var, tv_var, s_var, x_var),
                z3.Exists([y_var], role_action(w_var, tz_var, tv_var, s_var, y_var))
            )
        )
        self.core_solver.solver.add(agent_axiom)

        patient_axiom = z3.ForAll(
            [w_var, tz_var, tv_var, s_var, x_var],
            z3.Implies(
                role_patient(w_var, tz_var, tv_var, s_var, x_var),
                z3.Exists([y_var], role_action(w_var, tz_var, tv_var, s_var, y_var))
            )
        )
        self.core_solver.solver.add(patient_axiom)

        # [HATA DÜZELTMESİ - P0-5] İzafet özdeşlik değil nisbettir. Muzâf bir araz ise ("Zeyd'in eli")
        # nisbet, onun muzâfun ileyhte kâim olmasıdır; cevherin izafeti ("Beytullah") kıyâm doğurmaz.
        izafet = self.core_solver.builder.get_or_create_predicate("Rel_Mudaf_MudafIlayh", arity=2)
        kiyam = self.core_solver.builder.get_or_create_predicate("Rel_Kiyam", arity=2)
        araz = self.core_solver.builder.get_or_create_predicate("Araz", arity=1)
        izafet_axiom = z3.ForAll(
            [w_var, tz_var, tv_var, s_var, x_var, y_var],
            z3.Implies(
                z3.And(izafet(w_var, tz_var, tv_var, s_var, x_var, y_var), araz(w_var, tz_var, tv_var, s_var, x_var)),
                kiyam(w_var, tz_var, tv_var, s_var, x_var, y_var)
            )
        )
        self.core_solver.solver.assert_and_track(izafet_axiom, "AXIOM_IZAFET_ARAZ_KIYAM")

    def prove_metaphorical_bridge(self, chain_data: Dict[str, Any]) -> List[Tuple[str, z3.ExprRef]]:
        """
        [FAZ 3/4 ENTEGRASYONU] İlm-i Beyân Ma'nâ el-Ma'nâ İspatı.
        L1'den gelen İlm-i Beyân analiz paketini, 4 Boyutlu Kripke Semantiğine (w, tz, tv, s)
        uygun Z3 aksiyomlarına dönüştürür.
        Köprüler saklanmaz: dönen (ad, aksiyom) çiftleri yalnızca `execute_sat_check(..., bridge_axioms=...)`
        ile verildikleri kontrolde geçerlidir. Te'vil karîneye bağlıdır; bir cümlenin te'vili başka bir
        cümlenin (veya başka bir ekolün) hükmüne sızmamalıdır.
        """
        if not chain_data or not chain_data.get("is_found"):
            return []

        path = chain_data.get("path", [])
        if not path or len(path) < 2:
            return []

        alaka_type = chain_data.get("alaka_type", "Unknown")
        luzum_derecesi = chain_data.get("luzum_derecesi", "Luzum_u_Zihni")
        bridge_type = chain_data.get("type")

        w_var = z3.Const('w_beyan', self.core_solver.builder.WorldSort)
        tz_var = z3.Const('tz_beyan', self.core_solver.builder.TimeSortZati)
        tv_var = z3.Const('tv_beyan', self.core_solver.builder.TimeSortVasfi)
        s_var = z3.Const('s_beyan', self.core_solver.builder.SpaceSort)
        x_var = z3.Const('x_beyan', self.core_solver.builder.EntitySort)

        bridges: List[Tuple[str, z3.ExprRef]] = []
        for i in range(len(path) - 1):
            source_id = path[i]
            target_id = path[i+1]

            bridge_id = f"AXIOM_BEYAN_{alaka_type}_{source_id}_TO_{target_id}"

            source_pred = self.core_solver.builder.get_or_create_predicate(source_id, arity=1)
            target_pred = self.core_solver.builder.get_or_create_predicate(target_id, arity=1)

            if bridge_type == "Istiare":
                mushabehat = chain_data.get("mushabehat", [])
                for trait in mushabehat:
                    trait_pred = self.core_solver.builder.get_or_create_predicate(trait, arity=1)
                    trait_axiom_src = z3.ForAll([w_var, tz_var, tv_var, s_var, x_var], z3.Implies(source_pred(w_var, tz_var, tv_var, s_var, x_var), trait_pred(w_var, tz_var, tv_var, s_var, x_var)))
                    trait_axiom_tgt = z3.ForAll([w_var, tz_var, tv_var, s_var, x_var], z3.Implies(target_pred(w_var, tz_var, tv_var, s_var, x_var), trait_pred(w_var, tz_var, tv_var, s_var, x_var)))
                    bridges.append((f"{bridge_id}_MUSHABEHAT_{trait}_SRC", trait_axiom_src))
                    bridges.append((f"{bridge_id}_MUSHABEHAT_{trait}_TGT", trait_axiom_tgt))

            if luzum_derecesi == "Luzum_u_Harici":
                w_base = z3.Const('w_base', self.core_solver.builder.WorldSort)
                bridge_axiom = z3.ForAll([tz_var, tv_var, s_var, x_var], 
                    z3.Implies(source_pred(w_base, tz_var, tv_var, s_var, x_var), target_pred(w_base, tz_var, tv_var, s_var, x_var))
                )
            else:
                bridge_axiom = z3.ForAll([w_var, tz_var, tv_var, s_var, x_var],
                    z3.Implies(source_pred(w_var, tz_var, tv_var, s_var, x_var), target_pred(w_var, tz_var, tv_var, s_var, x_var))
                )

            bridges.append((bridge_id, bridge_axiom))

        return bridges

    def _context_fingerprint(self) -> Tuple[int, int]:
        """
        Önbellek anahtarına giren çözücü bağlamı: açık scope sayısı ve aksiyom sayısı.
        Çözücüye dışarıdan push/add yapıldığında (ör. paylaşılan bir münazara oturumu),
        eski bağlamda hesaplanmış bir sonuç yeniden kullanılmaz.
        """
        solver = self.core_solver.solver
        return solver.num_scopes(), len(solver.assertions())

    def execute_sat_check(self, ir_matrix: SemanticStatementIR, bridge_axioms: List[Tuple[str, z3.ExprRef]] = None) -> Dict[str, Any]:
        bridge_axioms = list(bridge_axioms or [])
        matrix_signature = (
            self._freeze_ir_matrix(ir_matrix.predicates),
            tuple(sorted((name, axiom.sexpr()) for name, axiom in bridge_axioms)),
            self._context_fingerprint(),
        )

        if matrix_signature in self._memoization_cache:
            self._memoization_cache.move_to_end(matrix_signature)
            return self._memoization_cache[matrix_signature]

        self.core_solver.solver.push()

        try:
            self._inject_structural_axioms()

            # Köprüler izlenerek eklenir: çelişkiye katılırlarsa unsat core'da adlarıyla görünürler.
            for name, axiom in bridge_axioms:
                self.core_solver.solver.assert_and_track(axiom, name)

            w_base = z3.Const('w_base', self.core_solver.builder.WorldSort)
            tz_base = z3.Const('tz_base', self.core_solver.builder.TimeSortZati)
            tv_base = z3.Const('tv_base', self.core_solver.builder.TimeSortVasfi)
            s_base = z3.Const('s_base', self.core_solver.builder.SpaceSort)
            
            for item in ir_matrix.predicates:
                z3_expr = self._build_z3_expr(item, w_base, tz_base, tv_base, s_base)
                self.core_solver.solver.add(z3_expr)
            
            result = self.core_solver.solver.check()
            
            if result == z3.sat:
                response = {"status": "SAT", "message": "Ontolojik Uyum Sağlandı."}
            elif result == z3.unsat:
                core = self.core_solver.solver.unsat_core()
                response = {"status": "UNSAT", "message": f"Ontolojik Çelişki: {[str(c) for c in core]}"}
            else:
                response = {"status": "UNKNOWN", "message": f"Devre Kesici Tetiklendi veya Kararsız Durum: {self.core_solver.solver.reason_unknown()}"}
                
            if len(self._memoization_cache) >= self.max_cache_size:
                self._memoization_cache.popitem(last=False)
                
            self._memoization_cache[matrix_signature] = response
            return response
            
        except Exception as e:
            return {"status": "ERROR", "message": f"L3 SMT Derleme Çöküşü: {e}"}
        finally:
            self.core_solver.solver.pop()

    def execute_joint_sat_check(self, readings: Dict[str, SemanticStatementIR]) -> Dict[str, Any]:
        """
        [HATA DÜZELTMESİ - P0-7]: Mu'ârazada tarafların okumalarını aynı ontoloji ve yapısal aksiyomlarla
        birlikte sınar. Her yüklem kendi okumasının etiketiyle izlenir; çelişkide unsat core, hangi okumanın
        hangi yüklemlerinin hangi aksiyomlarla çatıştığını gösterir. Te'vil köprüleri bir tarafın kendi
        muhakemesidir; ortak karşılaştırmaya girmez.
        """
        self.core_solver.solver.push()

        try:
            self._inject_structural_axioms()

            w_base = z3.Const('w_base', self.core_solver.builder.WorldSort)
            tz_base = z3.Const('tz_base', self.core_solver.builder.TimeSortZati)
            tv_base = z3.Const('tv_base', self.core_solver.builder.TimeSortVasfi)
            s_base = z3.Const('s_base', self.core_solver.builder.SpaceSort)

            tracked_items: Dict[str, Tuple[str, Any]] = {}
            for label, ir_matrix in readings.items():
                for index, item in enumerate(ir_matrix.predicates):
                    track_name = f"READING_{label}_{index}"
                    tracked_items[track_name] = (label, item)
                    z3_expr = self._build_z3_expr(item, w_base, tz_base, tv_base, s_base)
                    self.core_solver.solver.assert_and_track(z3_expr, track_name)

            result = self.core_solver.solver.check()

            if result == z3.sat:
                return {"status": "SAT", "message": "Okumalar ortak ontolojide bağdaşıyor."}
            if result == z3.unsat:
                core_names = {str(c) for c in self.core_solver.solver.unsat_core()}
                conflict: Dict[str, List[Any]] = {"axioms": sorted(core_names - tracked_items.keys())}
                for label in readings:
                    conflict[label] = [item for name, (owner, item) in tracked_items.items() if owner == label and name in core_names]
                return {"status": "UNSAT", "message": f"Ontolojik Çelişki: {conflict['axioms']}", "conflict": conflict}
            return {"status": "UNKNOWN", "message": f"Devre Kesici Tetiklendi veya Kararsız Durum: {self.core_solver.solver.reason_unknown()}"}

        except Exception as e:
            return {"status": "ERROR", "message": f"L3 SMT Derleme Çöküşü: {e}"}
        finally:
            self.core_solver.solver.pop()