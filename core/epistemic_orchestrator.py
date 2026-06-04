import z3
from typing import Dict, Any, List, Tuple
import re
from linguistics.ilm_wad_adapter import IlmWadAdapter, SemanticStatementIR
from linguistics.sarf_parser import MorphologicalAnalysis
from core.layer1_graph import Layer1HeuristicGraph
from core.layer2_rules import Layer2RuleEngine
from schools.base_usul import AbstractSchoolUsul
from core.exceptions import DiachronicViolationError, OutOfOntologyError

class EpistemicOrchestrator:
    def __init__(self, adapter: IlmWadAdapter, l1: Layer1HeuristicGraph, l2: Layer2RuleEngine, l3_circuit_breaker):
        self.adapter = adapter
        self.l1 = l1
        self.l2 = l2
        self.l3 = l3_circuit_breaker

    def _extract_conflict_nodes_from_core(self, unsat_core: str) -> List[str]:
        conflict_nodes = set()
        # Z3 Core formatını (AXIOM_DISJOINT_Wajib_AND_Mumkin vb.) parse et
        matches = re.findall(r'AXIOM_[A-Z]+_([A-Za-z0-9_]+)', unsat_core)
        for match in matches:
            parts = match.split('_AND_')
            conflict_nodes.update(parts)
        return list(conflict_nodes)

    def _verify_air_gapped_ontology(self, ir_matrix: SemanticStatementIR) -> None:
        """
        [FAZ 1 - AIR-GAPPED ONTOLOGY DENETİMİ]
        Semantik ara temsildeki (IR) hiçbir kavramın Porphyrios Ağacı 
        (Base Ontology) dışından seküler bir varlık olarak Z3 Kripke uzayına 
        sızmamasını garanti altına alan donanımsal güvenlik duvarı.
        """
        allowed_system_prefixes = ("Rel_", "Role_", "GrammarNode_")
        allowed_operators = {
            "Wajib_Fiqh", "Haram_Fiqh", "Istifham_Inkari", "Kasr_Universal_Exclusion", 
            "Luzumi", "Inadi_Hakikiyye", "Inadi_Maniatul_Cem", "Inadi_Maniatul_Huluv"
        }

        def _scan_items(items):
            for item in items:
                if isinstance(item, tuple):
                    pred_id = item[0]
                    if not pred_id.startswith(allowed_system_prefixes) and pred_id not in allowed_operators:
                        # Kavram statik Porphyrios haritasında yoksa ve bir Differentia (Fasıl) ID'si değilse patlat
                        if pred_id not in self.l1.entity_map:
                            is_differentia = any(ent.differentia_id == pred_id for ent in self.l1.entity_map.values() if ent.differentia_id)
                            if not is_differentia:
                                raise OutOfOntologyError(f"[AIR-GAP İHLALİ] '{pred_id}' kavramı statik Porphyrios Ağacında (Klasik Ontoloji) bulunamadı. Dışarıdan seküler/tanımsız düğüm sızdırılması reddedildi.")
                elif hasattr(item, 'args'):
                    _scan_items(item.args)

        _scan_items(ir_matrix.predicates)

    def process_statement(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]], usul_profile: AbstractSchoolUsul, auto_lexicon: Dict[str, MorphologicalAnalysis] = None) -> Dict[str, Any]:
        max_tevil_retries = usul_profile.dsl_ruleset.get("max_tevil_retries", 1)
        current_attempt = 0
        tevil_flagged_nodes = []
        bridge_messages = []
        
        has_condition = any(t.lower() in ["in", "iza", "law", "amma", "imma", "aw", "ya"] for t in tokens)
        proposition_type = "Kadiyye-i_Sartiyye" if has_condition else "Kadiyye-i_Hamliyye"
        
        try:
            while current_attempt <= max_tevil_retries:
                # [FAZ 1 ENTEGRASYONU] Zorunlu "Classical" zaman damgası (Epoch)
                ir_matrix = self.adapter.generate_ir(
                    tokens, dependencies, usul_profile.namespace, auto_lexicon, tevil_flagged_nodes, proposition_type, epoch="Classical"
                )
                
                if not ir_matrix.is_valid_for_z3:
                    return {
                        "status": "PRAGMATICS_REJECT", 
                        "message": "İlm-i Ma'ânî İhlali: İnşâî form (İstifham-ı Hakikî) veya Muktazâ el-Hâl uyumsuzluğu."
                    }
                
                # Air-Gapped Ontology Mührü Denetimi
                self._verify_air_gapped_ontology(ir_matrix)
                
                execution_result = usul_profile.execute_dag(ir_matrix, self.l1, self.l2, self.l3, current_attempt)
                
                # [FAZ 3 ENTEGRASYONU]: İlm-i Beyân Te'vil (Metaphorical Bridge) Çıkarımı
                if execution_result.get("status") == "FALLBACK_TRIGGERED" and current_attempt < max_tevil_retries:
                    if usul_profile.dsl_ruleset.get("allow_tevil", False):
                        unsat_core_str = str(execution_result.get("unsat_core", ""))
                        conflicts = self._extract_conflict_nodes_from_core(unsat_core_str)
                        
                        # Eğer doğrudan UNSAT core okunamadıysa, IR Matrisindeki Literal nodeları tespit et
                        for item in ir_matrix.predicates:
                            if isinstance(item, tuple) and len(item) == 3:
                                args = item[1].split("::")
                                for arg in args:
                                    if "Literal" in arg and arg not in conflicts:
                                        conflicts.append(arg)
                        
                        if conflicts:
                            for conflict_node in conflicts:
                                if "Literal" in conflict_node:
                                    target_metaphor = conflict_node.replace("Literal", "Metaphor")
                                    
                                    # 1. L1 Graph üzerinden deterministik Alâka (Nexus) yolunu bul
                                    chain = self.l1.find_mana_el_mana_chain(conflict_node, target_metaphor)
                                    if chain:
                                        # 2. Bulunan Alâka yolunu L3 Z3 motoruna Köprü Aksiyomu olarak zerk et
                                        if self.l3.prove_metaphorical_bridge(chain):
                                            bridge_messages.append(f"İlm-i Beyân Çıkarımı: {chain} ardışık lüzumiyeti Z3'e ispatlatıldı.")
                                        
                            tevil_flagged_nodes.extend(conflicts)
                            current_attempt += 1
                            continue
                        else:
                            break
                    else:
                        break

                if current_attempt > 0 and execution_result.get("status") == "SAT":
                    execution_result["tevil_applied"] = True
                    msg_append = f" (Te'vil uygulandı: {tevil_flagged_nodes})"
                    if bridge_messages:
                        msg_append += " | " + " | ".join(bridge_messages)
                    execution_result["message"] += msg_append
                    
                return execution_result
                
            return execution_result
            
        except (DiachronicViolationError, OutOfOntologyError) as e:
            return {"status": "EPISTEMIC_BREACH", "message": str(e)}

    def execute_cross_school_muaradah(self, 
                                      mujib_claim_ir: SemanticStatementIR, 
                                      mujib_usul: AbstractSchoolUsul, 
                                      sail_tokens: List[str],
                                      sail_dependencies: List[Tuple[str, str, str, str]],
                                      sail_usul: AbstractSchoolUsul,
                                      sail_auto_lexicon: Dict[str, MorphologicalAnalysis] = None) -> Dict[str, Any]:
        
        try:
            # [FAZ 1 ENTEGRASYONU] Zorunlu "Classical" zaman damgası (Epoch)
            sail_native_ir = self.adapter.generate_ir(sail_tokens, sail_dependencies, sail_usul.namespace, sail_auto_lexicon, epoch="Classical")
            self._verify_air_gapped_ontology(sail_native_ir)
            
            sail_result = sail_usul.execute_dag(sail_native_ir, self.l1, self.l2, self.l3, current_attempt=0)

            if sail_result["status"] not in ["SAT", "FALLBACK_TRIGGERED"]:
                return {
                    "status": "MUARADAH_FAILED",
                    "message": f"Sâil'in karşı delili kendi L2/L3 uzayında ({sail_usul.namespace}) geçersiz: {sail_result.get('reason', sail_result.get('message'))}"
                }

            cross_injected_ir = self.adapter.generate_ir(sail_tokens, sail_dependencies, mujib_usul.namespace, sail_auto_lexicon, epoch="Classical")
            self._verify_air_gapped_ontology(cross_injected_ir)
            
            # SMT Solver yerine SMT Optimizer kullanarak ontolojik önceliklendirme
            optimizer = z3.Optimize()
            
            w_base = z3.Const('w_base', self.l3.core_solver.builder.WorldSort)
            tz_base = z3.Const('tz_base', self.l3.core_solver.builder.TimeSortZati)
            tv_base = z3.Const('tv_base', self.l3.core_solver.builder.TimeSortVasfi)
            
            # Mucîb'in iddiaları Soft Constraint (Ödünç alınmış uzay) olarak düşük maliyetle eklenir
            for item in mujib_claim_ir.predicates:
                z3_expr = self.l3._build_z3_expr(item, w_base, tz_base, tv_base)
                optimizer.add_soft(z3_expr, weight=1)
                
            # Sâil'in anti-tezi Hard Constraint (Mutlak İhlal) olarak eklenir
            for item in cross_injected_ir.predicates:
                z3_expr = self.l3._build_z3_expr(item, w_base, tz_base, tv_base)
                optimizer.add(z3_expr)

            cross_status = optimizer.check()

            if cross_status == z3.sat:
                # Soft Constraint'lerin ne kadarının ihlal edildiğini ölç
                model = optimizer.model()
                penalty_score = optimizer.objectives()[0]
                
                # Eğer maliyet 0 ise tamamen paralel, çelişmeyen iddialardır.
                if model.eval(penalty_score).as_long() == 0:
                    return {
                        "status": "MUARADAH_INEFFECTIVE",
                        "message": "Mu'aradah Başarısız: Sâil'in karşı delili Mucîb'in argümanıyla ontolojik bir çelişki (Penalty=0) yaratmadı. (Paralel Gerçeklik)."
                    }
                else:
                    return {
                        "status": "MUARADAH_SUCCESS",
                        "message": f"Mu'aradah Başarılı: Sâil ({sail_usul.namespace}), Mucîb'in uzayını kendi anti-teziyle {model.eval(penalty_score).as_long()} ağırlık maliyetiyle kırdı. Diyalektik Kilitlenme (Stalemate)."
                    }
            else:
                return {
                    "status": "MUJIB_INVALID",
                    "message": "Mucîb'in argümanları ile Sâil'in iddiaları yapısal olarak z3.Optimize düzleminde bile çözülemez bir kilitlenme yarattı."
                }
        except (DiachronicViolationError, OutOfOntologyError) as e:
            return {"status": "EPISTEMIC_BREACH", "message": f"Sâil'in argümanı ontolojik sızıntı barındırıyor: {e}"}
        except Exception as e:
            return {"status": "ERROR", "message": f"Mu'aradah SMT Çöküşü: {e}"}