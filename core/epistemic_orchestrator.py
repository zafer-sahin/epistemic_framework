import copy
from typing import Dict, Any, List, Optional, Tuple
import re
from linguistics.ilm_wad_adapter import IlmWadAdapter, SemanticStatementIR, NestedPredicate
from linguistics.sarf_parser import MorphologicalAnalysis
from core.layer1_graph import Layer1HeuristicGraph
from core.layer2_rules import Layer2RuleEngine
from schools.base_usul import AbstractSchoolUsul
from core.exceptions import DiachronicViolationError, OutOfOntologyError

# Bir okumanın kendi usûlünde tutarlı bulunduğunu gösteren hükümler (Selefî bilâ-keyf okuması dahil).
# Te'vil denendikten sonra da çelişkili kalan (FALLBACK_TRIGGERED) okuma bu kümede değildir.
CONSISTENT_STATUSES = ("SAT", "SAT_BILA_KAYF")

class EpistemicOrchestrator:
    def __init__(self, adapter: IlmWadAdapter, l1: Layer1HeuristicGraph, l2: Layer2RuleEngine, l3_circuit_breaker):
        self.adapter = adapter
        self.l1 = l1
        self.l2 = l2
        self.l3 = l3_circuit_breaker

        # Air-gap'in sınırı olan ortak ontoloji, leksikal zehirlenme denetiminin de ortak zeminidir.
        self.adapter.lexicon.bind_shared_ontology(self.l1.entity_map.keys())

    def _extract_conflict_nodes_from_core(self, unsat_core: str) -> List[str]:
        conflict_nodes = set()
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
        [FAZ 4 YAMASI]: 'LocatedIn' operatörü beyaz listeye eklendi.
        """
        allowed_system_prefixes = ("Rel_", "Role_", "GrammarNode_")
        allowed_operators = {
            "Wajib_Fiqh", "Haram_Fiqh", "Istifham_Inkari", "Kasr_Universal_Exclusion", 
            "Luzumi", "Inadi_Hakikiyye", "Inadi_Maniatul_Cem", "Inadi_Maniatul_Huluv",
            "Kasr_Sifat_to_Mevsuf", "Kasr_Mevsuf_to_Sifat", "LocatedIn"
        }

        def _scan_items(items):
            for item in items:
                if isinstance(item, tuple):
                    pred_id = item[0]
                    if not pred_id.startswith(allowed_system_prefixes) and pred_id not in allowed_operators:
                        if pred_id not in self.l1.entity_map:
                            is_differentia = any(ent.differentia_id == pred_id for ent in self.l1.entity_map.values() if ent.differentia_id)
                            if not is_differentia:
                                raise OutOfOntologyError(f"[AIR-GAP İHLALİ] '{pred_id}' kavramı statik Porphyrios Ağacında (Klasik Ontoloji) bulunamadı. Dışarıdan seküler/tanımsız düğüm sızdırılması reddedildi.")
                elif hasattr(item, 'args'):
                    _scan_items(item.args)

        _scan_items(ir_matrix.predicates)

    def _resolve_ilm_i_beyan(self, ir_matrix: SemanticStatementIR, flagged_elements: List[str], school_rules: Dict[str, Any]) -> Tuple[bool, List[str], List[Tuple[str, Any]]]:
        """
        [FAZ 3 ENTEGRASYONU] Deterministik Te'vil ve Ma'nâ el-Ma'nâ (İlm-i Beyân) İşlemcisi.
        [HATA DÜZELTMESİ - P0-2]: Her te'vil adayı yalnızca kendi köprüleriyle sınanır; başarısız adayın
        köprüleri hiçbir yerde kalmaz. Kabul edilen köprüler, nihai kontrolde yeniden kullanılmak üzere döner.
        """
        allow_tevil = school_rules.get("allow_tevil", False)
        blocked_nodes = school_rules.get("blocked_nodes", [])
        bridge_messages = []
        accepted_bridges: List[Tuple[str, Any]] = []

        if not allow_tevil:
            return False, bridge_messages, accepted_bridges

        tevil_basarili = False

        for flagged in flagged_elements:
            try:
                amil_str, mamul_str = flagged.split("::", 1)
            except ValueError:
                continue

            nodes_to_try = []
            if amil_str not in blocked_nodes:
                nodes_to_try.append(amil_str)
            if mamul_str not in blocked_nodes:
                nodes_to_try.append(mamul_str)

            for node_str in nodes_to_try:
                node_entity = self.l1.entity_map.get(node_str)
                if not node_entity:
                    continue

                potential_targets = [rel.target_id for rel in node_entity.relations if getattr(rel, 'alaka_type', None) is not None]

                for target_id in potential_targets:
                    chain_data = self.l1.find_mana_el_mana_chain(node_str, target_id)
                    
                    if chain_data.get("is_found"):
                        bridge_axioms = self.l3.prove_metaphorical_bridge(chain_data)

                        if bridge_axioms:
                            # MATRİS MUTASYONU ÖNCESİ ORİJİNAL DURUMU YEDEKLE (BACKTRACKING)
                            original_predicates = copy.deepcopy(ir_matrix.predicates)
                            
                            if hasattr(self.adapter, 'update_ir_predicate'):
                                self.adapter.update_ir_predicate(ir_matrix, node_str, target_id)
                            else:
                                def _replace_in_tuple(tup: Tuple[str, str, int]) -> Tuple[str, str, int]:
                                    p_id, a_id, arity = tup
                                    new_pred = target_id if p_id == node_str else p_id
                                    if arity == 1:
                                        new_arg = target_id if a_id == node_str else a_id
                                    else:
                                        args = a_id.split("::")
                                        new_args = [target_id if a == node_str else a for a in args]
                                        new_arg = "::".join(new_args)
                                    return (new_pred, new_arg, arity)
                                
                                def _traverse_and_replace(preds):
                                    new_preds = []
                                    for item in preds:
                                        if isinstance(item, tuple):
                                            new_preds.append(_replace_in_tuple(item))
                                        elif hasattr(item, 'args'): 
                                            new_item = copy.deepcopy(item)
                                            new_item.args = _traverse_and_replace(new_item.args)
                                            new_preds.append(new_item)
                                    return new_preds
                                
                                ir_matrix.predicates = _traverse_and_replace(ir_matrix.predicates)
                            
                            # YENİ MATRİSİN SAT KONTROLÜ (köprüler yalnızca bu kontrolün kapsamında geçerli)
                            l3_result = self.l3.execute_sat_check(ir_matrix, bridge_axioms=bridge_axioms)
                            if l3_result["status"] == "SAT":
                                alaka_str = chain_data.get("alaka_type", "Unknown")
                                bridge_messages.append(f"İlm-i Beyân Çıkarımı: {node_str} -> {target_id} ({alaka_str}) zihinsel köprüsü Z3'e ispatlatıldı.")
                                accepted_bridges = bridge_axioms
                                tevil_basarili = True
                                break
                            else:
                                # UNSAT ALINDI: MATRİSİ ESKİ HALİNE DÖNDÜR VE SIRADAKİ ADAYA GEÇ (ROLLBACK)
                                ir_matrix.predicates = original_predicates

                if tevil_basarili:
                    break

        return tevil_basarili, bridge_messages, accepted_bridges

    def process_statement(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]], usul_profile: AbstractSchoolUsul, auto_lexicon: Dict[str, MorphologicalAnalysis] = None) -> Dict[str, Any]:
        return self.evaluate_statement(tokens, dependencies, usul_profile, auto_lexicon)[0]

    def evaluate_statement(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]], usul_profile: AbstractSchoolUsul, auto_lexicon: Dict[str, MorphologicalAnalysis] = None) -> Tuple[Dict[str, Any], Optional[SemanticStatementIR]]:
        """
        `process_statement` ile aynı değerlendirme; ek olarak hükme esas olan IR'yi (te'vil uygulandıysa
        te'vil sonrası okumayı) döndürür. Mu'ârazada hem Mucîb'in iddiası hem Sâil'in okuması buradan gelir.
        """
        max_tevil_retries = usul_profile.dsl_ruleset.get("max_tevil_retries", 1)
        current_attempt = 0
        tevil_flagged_nodes = []
        
        has_condition = any(t.lower() in ["in", "iza", "law", "amma", "imma", "aw", "ya"] for t in tokens)
        proposition_type = "Kadiyye-i_Sartiyye" if has_condition else "Kadiyye-i_Hamliyye"
        
        try:
            ir_matrix = self.adapter.generate_ir(
                tokens, dependencies, usul_profile.namespace, auto_lexicon, tevil_flagged_nodes, proposition_type, epoch="Classical"
            )
            
            if not ir_matrix.is_valid_for_z3:
                return {
                    "status": "PRAGMATICS_REJECT",
                    "message": "İlm-i Ma'ânî İhlali: İnşâî form (İstifham-ı Hakikî) veya Muktazâ el-Hâl uyumsuzluğu."
                }, ir_matrix
            
            self._verify_air_gapped_ontology(ir_matrix)
            
            execution_result = usul_profile.execute_dag(ir_matrix, self.l1, self.l2, self.l3, current_attempt)
            
            if execution_result.get("status") == "FALLBACK_TRIGGERED" and current_attempt < max_tevil_retries:
                l1_analysis = self.l1.analyze_ir(ir_matrix)
                flagged = l1_analysis.get("flagged_elements", [])
                
                resolved, bridge_messages, accepted_bridges = self._resolve_ilm_i_beyan(ir_matrix, flagged, usul_profile.dsl_ruleset)

                if resolved:
                    l3_result = self.l3.execute_sat_check(ir_matrix, bridge_axioms=accepted_bridges)
                    if l3_result["status"] == "SAT":
                        execution_result["status"] = "SAT"
                        execution_result["tevil_applied"] = True
                        execution_result["tevil_bridges"] = [name for name, _ in accepted_bridges]
                        msg_append = f" (Te'vil uygulandı)"
                        if bridge_messages:
                            msg_append += " | " + " | ".join(bridge_messages)
                        execution_result["message"] = execution_result.get("message", "") + msg_append
                        return execution_result, ir_matrix

            return execution_result, ir_matrix

        except (DiachronicViolationError, OutOfOntologyError) as e:
            return {"status": "EPISTEMIC_BREACH", "message": str(e)}, None

    def execute_cross_school_muaradah(self, 
                                      mujib_claim_ir: SemanticStatementIR, 
                                      mujib_usul: AbstractSchoolUsul, 
                                      sail_tokens: List[str],
                                      sail_dependencies: List[Tuple[str, str, str, str]],
                                      sail_usul: AbstractSchoolUsul,
                                      sail_auto_lexicon: Dict[str, MorphologicalAnalysis] = None,
                                      fsm_engine: Any = None) -> Dict[str, Any]:
        """
        [FAZ 5 ENTEGRASYONU] FSM Asenkron Mu'aradah Tetikleyicisi.
        Sâil'in 'AWAITING_ATTACK' durumunda gönderdiği karşı-argümanı (Anti-Tez) Mucîb'in argümanıyla
        çarpıştırır. Çapraz ekol kilitlenmesi FSM durumunu günceller.
        [FAZ 4 YAMASI]: Kripke Uzayı (SpaceSort) eksik parametresi eklendi.
        [HATA DÜZELTMESİ]: Karşılaştırmaya Sâil'in kendi usûlündeki (te'vil dahil) okuması girer;
        cümlesi Mucîb'in sözlüğüyle yeniden okunmaz.
        [HATA DÜZELTMESİ - P0-7]: Karşılaştırma ontolojisiz bir Optimize örneğinde değil, L3'ün ortak
        ontolojisinde yapılır. Ontolojiyle kendi başına çelişen Mucîb iddiası MUJIB_INVALID, iki okuma
        bağdaşmıyorsa MUARADAH_SUCCESS, bağdaşıyorsa MUARADAH_INEFFECTIVE döner. Çözücü karar veremezse
        (MUARADAH_UNDECIDED) münazara açık kalır.
        """
        
        if fsm_engine and getattr(fsm_engine, "current_state", None) != "AWAITING_ATTACK":
            return {
                "status": "FSM_VIOLATION",
                "message": "[DİYALEKTİK İHLAL] Mu'aradah saldırısı sadece Sâil'in 'AWAITING_ATTACK' evresinde yapılabilir."
            }
        
        try:
            # Sâil'in karşı delili kendi usûlünde (te'vil dahil) tam olarak değerlendirilir; zerk edilen de bu okumadır.
            sail_result, sail_reading_ir = self.evaluate_statement(sail_tokens, sail_dependencies, sail_usul, sail_auto_lexicon)

            if sail_result["status"] == "EPISTEMIC_BREACH":
                return {"status": "EPISTEMIC_BREACH", "message": f"Sâil'in argümanı ontolojik sızıntı barındırıyor: {sail_result['message']}"}

            if sail_result["status"] not in CONSISTENT_STATUSES:
                return {
                    "status": "MUARADAH_FAILED",
                    "message": f"Sâil'in karşı delili kendi L2/L3 uzayında ({sail_usul.namespace}) geçersiz: {sail_result.get('reason', sail_result.get('message'))}"
                }

            # Ontolojiyle kendi başına çelişen bir Mucîb iddiası mu'ârazaya konu olamaz.
            mujib_check = self.l3.execute_sat_check(mujib_claim_ir)
            if mujib_check["status"] == "UNSAT":
                if fsm_engine:
                    fsm_engine.resolve_debate()
                return {
                    "status": "MUJIB_INVALID",
                    "message": f"Mucîb'in iddiası ortak ontolojiyle kendi başına çelişiyor; mu'ârazaya konu olacak tutarlı bir iddia yok. {mujib_check['message']}",
                    "sail_reading": sail_reading_ir.predicates
                }

            joint_check = mujib_check
            if mujib_check["status"] == "SAT":
                joint_check = self.l3.execute_joint_sat_check({"Mujib": mujib_claim_ir, "Sail": sail_reading_ir})

            if joint_check["status"] == "SAT":
                if fsm_engine:
                    fsm_engine.resolve_debate()
                return {
                    "status": "MUARADAH_INEFFECTIVE",
                    "message": "Mu'aradah Başarısız: Sâil'in okuması Mucîb'inkiyle ortak ontolojide bağdaşıyor; ontolojik bir çelişki yaratmadı (Paralel Gerçeklik). Mucîb kazandı (İlzam).",
                    "sail_reading": sail_reading_ir.predicates
                }

            if joint_check["status"] == "UNSAT":
                if fsm_engine:
                    # Çapraz kilitlenme sağlandı, FSM diyalektiği sonuçlandırır.
                    fsm_engine.resolve_debate()
                conflict_axioms = joint_check['conflict']['axioms']
                # [HATA DÜZELTMESİ - P0-6] Çatışmaya hiçbir aksiyom girmiyorsa okumalar birbirinin nakîzidir
                # (Ör: "Zeyd vurur" / "Zeyd vurmaz"); ontolojiye başvurmadan çelişirler.
                reason = f"ortak ontolojide bağdaşmıyor {conflict_axioms}" if conflict_axioms else "doğrudan çelişiyor (tenâkuz); ikisi birlikte doğru olamaz"
                return {
                    "status": "MUARADAH_SUCCESS",
                    "message": f"Mu'aradah Başarılı: Sâil'in ({sail_usul.namespace}) okuması, Mucîb'in okumasıyla {reason}. Diyalektik Kilitlenme (Stalemate).",
                    "sail_reading": sail_reading_ir.predicates,
                    "conflict": joint_check["conflict"]
                }

            if joint_check["status"] == "ERROR":
                return {"status": "ERROR", "message": f"Mu'aradah SMT Çöküşü: {joint_check['message']}"}

            # Çözücünün karar verememesi (UNKNOWN) bir hüküm değildir; münazara açık kalır.
            return {
                "status": "MUARADAH_UNDECIDED",
                "message": f"Mu'aradah karara bağlanamadı: okumaların ortak ontolojide bağdaşıp bağdaşmadığı belirlenemedi. {joint_check['message']}",
                "sail_reading": sail_reading_ir.predicates
            }
        except (DiachronicViolationError, OutOfOntologyError) as e:
            return {"status": "EPISTEMIC_BREACH", "message": f"Sâil'in argümanı ontolojik sızıntı barındırıyor: {e}"}
        except Exception as e:
            return {"status": "ERROR", "message": f"Mu'aradah SMT Çöküşü: {e}"}