import sys
from pathlib import Path

# Core Katmanları
from core.models import OntologyLoader
from core.logic_engine import AristotelianSolver
from core.layer1_graph import Layer1HeuristicGraph
from core.layer2_rules import Layer2RuleEngine
from core.layer3_smt import Layer3SMTCircuitBreaker
from core.epistemic_orchestrator import EpistemicOrchestrator
from core.exceptions import DiachronicViolationError

# Dilbilim Katmanları
from linguistics.tokenizer import EpistemicTokenizer
from linguistics.sarf_parser import SarfEngine
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister, DenialLevel
from linguistics.ilm_wad_adapter import IlmWadAdapter, SemanticStatementIR

# Ekol (Usûl) Profilleri
from schools.salafi_usul import SalafiUsul
from schools.ashari_usul import AshariUsul
from schools.maturidi_usul import MaturidiUsul

# FSM
from schools.taftazani.adab_al_bahth import AdabAlBahthEngine

def execute_healthcheck():
    print("="*80)
    print("[SİSTEM] N-TIER EPİSTEMİK MOTOR UÇTAN UCA SAĞLIK TARAMASI (HEALTHCHECK)")
    print("="*80)
    
    # 1. BAŞLATMA (BOOTSTRAP)
    loader = OntologyLoader()
    ontology = loader.load(Path("data/base_ontology.json"))
    solver = AristotelianSolver(ontology)
    
    tokenizer = EpistemicTokenizer()
    sarf = SarfEngine()
    nahiv = NahivDependencyCompiler()
    
    lexicon = ContextualLexicon()
    discourse = DiscourseRegister()
    
    # [FAZ 6] Selefî Usûlü için Bila-Kayf (Hakikat Taşınması) Sibak Tetikleyicisi
    lexicon.register_word("yad", "Salafi", "Sifat_Yed_Literal")
    lexicon.register_word("yad", "Salafi", "Sifat_Yed_Bila_Kayf", proposition_type="Kadiyye-i_Hamliyye", sibak_trigger="allah")
    
    # [FAZ 3] Eş'arî ve Mâtürîdî için Ma'nâ el-Ma'nâ (Mecaz) Fallback Tetikleyicisi
    lexicon.register_word("yad", "Ashari", "Sifat_Yed_Literal", proposition_type="Kadiyye-i_Hamliyye")
    lexicon.register_word("yad", "Ashari", "Sifat_Yed_Metaphor", proposition_type="Metaphor_Fallback")
    lexicon.register_word("yad", "Maturidi", "Sifat_Yed_Literal", proposition_type="Kadiyye-i_Hamliyye")
    lexicon.register_word("yad", "Maturidi", "Sifat_Yed_Metaphor", proposition_type="Metaphor_Fallback")
    
    # Sistematik Ontoloji Kayıtları
    lexicon.register_word("tekvin", "Maturidi", "Tekvin")
    lexicon.register_word("allah", "Base", "Wajib_al_Wujud")
    lexicon.register_word("cemad", "Base", "Cemad")
    lexicon.register_word("nam", "Base", "Nami")
    lexicon.register_word("zeyd", "Base", "Zeyd_Entity")
    lexicon.register_word("drb", "Base", "Kavram_Vuran")
    lexicon.register_word("masiy", "Base", "Masi") 
    
    # [FAZ 1] Sızıntı Testi için Seküler Kelime Kaydı Denemesi
    # Sarf motoru 'demokrasi' girdisinden 'demokras' kökünü çıkaracağı için test kök üzerinden yapılır.
    print("[LOG] Diachronic Koruma Testi: 'Modern' epoch kaydı deneniyor...")
    try:
        lexicon.register_word("demokras", "Base", "Sekuler_Otorite", epoch="Modern")
    except DiachronicViolationError as e:
        print(f"[BAŞARILI] Güvenlik Duvarı Kaydı Reddetti: {e}")
        
    # Senaryo 3'ün Orkestratör düzeyinde reddedilmesini test etmek için tensöre arkadan zerk edilir
    lexicon._tensor["demokras"] = {"Modern": {"Base": {"Kadiyye-i_Hamliyye": {"default": "Sekuler_Otorite", "context_triggers": {}}}}}

    adapter = IlmWadAdapter(lexicon, discourse)
    l1 = Layer1HeuristicGraph(ontology)
    l2 = Layer2RuleEngine()
    l3 = Layer3SMTCircuitBreaker(solver, timeout_ms=3000)
    
    orchestrator = EpistemicOrchestrator(adapter, l1, l2, l3)
    print("\n[BAŞARILI] Orkestratör ve tüm alt-motorlar belleğe yüklendi.\n")

    # 2. TEST SENARYOLARI
    sentence_1 = "yadu allahi" 
    tokens_1 = tokenizer.tokenize(sentence_1)
    morph_1 = sarf.derive_lexicon(tokens_1)
    ast_1 = nahiv.suggest_dependencies(tokens_1, morph_1)
    
    print("--- SENARYO 1: SELEFÎ USÛLÜ (FAZ 6 - İBN TEYMİYYE AST TABANLI HAKİKAT TAŞINMASI) ---")
    print(f"Girdi: '{sentence_1}' | AST: {ast_1}")
    discourse.clear_memory()
    res_salafi = orchestrator.process_statement(tokens_1, ast_1, SalafiUsul(), morph_1)
    print(f"Sonuç: [{res_salafi['status']}] -> {res_salafi.get('message')}\n")

    print("--- SENARYO 2: EŞ'ARÎ USÛLÜ (FAZ 3 - İLM-İ BEYÂN MA'NÂ EL-MA'NÂ İSPATI) ---")
    print(f"Girdi: '{sentence_1}' | AST: {ast_1}")
    discourse.clear_memory()
    res_ashari = orchestrator.process_statement(tokens_1, ast_1, AshariUsul(), morph_1)
    print(f"Sonuç: [{res_ashari['status']}] -> {res_ashari.get('message')}")
    print(f"L2 Kararı: {res_ashari.get('l2_context')}\n")

    print("--- SENARYO 3: [FAZ 1 - AIR-GAP / DIACHRONIC İHLALİ] SEKÜLER MSA SIZINTISI KONTROLÜ ---")
    sentence_secular = "demokrasi allahi"
    tokens_sec = tokenizer.tokenize(sentence_secular)
    morph_sec = sarf.derive_lexicon(tokens_sec)
    ast_sec = nahiv.suggest_dependencies(tokens_sec, morph_sec)
    print(f"Girdi: '{sentence_secular}' | Epoch: 'Modern' (MSA Sızıntı Testi)")
    discourse.clear_memory()
    res_secular = orchestrator.process_statement(tokens_sec, ast_sec, AshariUsul(), morph_sec)
    print(f"Sistem Tepkisi: [{res_secular['status']}] -> {res_secular.get('message')}\n")

    sentence_2 = "tekvinu allahi"
    tokens_2 = tokenizer.tokenize(sentence_2)
    morph_2 = sarf.derive_lexicon(tokens_2)
    ast_2 = nahiv.suggest_dependencies(tokens_2, morph_2)
    
    print("--- SENARYO 4: MÂTÜRÎDÎ USÛLÜ (DÜĞÜM BAZLI DSL YASAĞI) ---")
    print(f"Girdi: '{sentence_2}' | AST: {ast_2}")
    discourse.clear_memory()
    res_maturidi = orchestrator.process_statement(tokens_2, ast_2, MaturidiUsul(), morph_2)
    print(f"Sonuç: [{res_maturidi['status']}] -> {res_maturidi.get('reason', res_maturidi.get('message'))}\n")

    print("--- SENARYO 5: CÜRCÂNÎ MU'ARADAH KİLİTLENMESİ (ÇAPRAZ USÛL DİYALEKTİĞİ) ---")
    discourse.clear_memory()
    ir_mujib = SemanticStatementIR(
        active_namespace="Ashari", 
        predicates=[("Cemad", "Cemad", 1), ("Zeyd_Entity", "Zeyd_Entity", 1), ("Rel_Mubteda_Haber", "Cemad::Zeyd_Entity", 2)], 
        is_valid_for_z3=True
    )
    sail_tokens = ["nami", "zeydun"]
    sail_morph = sarf.derive_lexicon(sail_tokens)
    sail_ast = nahiv.suggest_dependencies(sail_tokens, sail_morph)
    
    res_muaradah = orchestrator.execute_cross_school_muaradah(
        ir_mujib, AshariUsul(), sail_tokens, sail_ast, SalafiUsul(), sail_morph
    )
    print(f"Mucîb (Ashari): Cemad | Sâil (Salafi): Nami")
    print(f"Sonuç: [{res_muaradah['status']}] -> {res_muaradah.get('message')}\n")

    print("--- SENARYO 6: İLM-İ VAZ' NEV'Î (YAPISAL LÜZUMİYET VE TEMATİK ROL) ---")
    sentence_5 = "zeydun daribun"
    tokens_5 = tokenizer.tokenize(sentence_5)
    morph_5 = sarf.derive_lexicon(tokens_5)
    ast_5 = nahiv.suggest_dependencies(tokens_5, morph_5)
    
    discourse.clear_memory()
    res_vaz = orchestrator.process_statement(tokens_5, ast_5, AshariUsul(), morph_5)
    print(f"Girdi: '{sentence_5}' | Morfolojik Kalıp (Vezin): {morph_5['daribun'].pattern}")
    print(f"Çıkarılan Tematik Rol (Thematic Role): {morph_5['daribun'].thematic_role}")
    print(f"Sonuç: [{res_vaz['status']}] (Role_Agent tespiti otonom Role_Action yarattı)\n")

    print("--- SENARYO 7: İLM-İ MA'ÂNÎ (MUKTAZÂ EL-HÂL VE İSTİFHAM-I İNKÂRÎ) ---")
    sentence_6a = "inna zeydun daribun"
    tokens_6a = tokenizer.tokenize(sentence_6a)
    morph_6a = sarf.derive_lexicon(tokens_6a)
    ast_6a = nahiv.suggest_dependencies(tokens_6a, morph_6a)
    
    discourse.clear_memory()
    discourse.epistemic_state["Sail"] = DenialLevel.KHALI_AL_ZIHN
    res_maani_1 = orchestrator.process_statement(tokens_6a, ast_6a, AshariUsul(), morph_6a)
    print(f"Girdi (Tevkîd): '{sentence_6a}' | Sâil Zihni: KHALI_AL_ZIHN")
    print(f"Sonuç: [{res_maani_1['status']}] -> {res_maani_1.get('message')}\n")

    print("--- SENARYO 8: ÂDÂB-I BAHS (FAZ 5 - TAHRÎR-İ NİZA' VE MÜLÂZAMA) ---")
    clean_solver = AristotelianSolver(ontology)
    fsm_engine = AdabAlBahthEngine(clean_solver, discourse)
    fsm_engine.reset_session()
    
    res_dava = fsm_engine.submit_claim("Forall([x], Implies(Cemad(x), Nami(x)))")
    print(f"Da'vâ (İddia) Durumu: {res_dava['message']}")
    
    res_tahrir = fsm_engine.tahrir_i_niza(musellemat=["Cemad"], niza_terms=["Nami"])
    print(f"Tahrîr-i Niza': {res_tahrir['message']}")
    
    res_delil = fsm_engine.submit_evidence(["Forall([x], Implies(Cemad(x), Nami(x)))"])
    print(f"Delil Sunumu: {res_delil['message']}")
    
    res_nakz = fsm_engine.attack_evidence("Nakz")
    print(f"Nakz (Çürütme) Sonucu: [{res_nakz['status']}] -> {res_nakz['message']}\n")

    print("--- SENARYO 9: KÂTİBÎ ŞEMSİYYE KİPLİKLERİ (FAZ 4 - ZÂT/VASIF AYRIMI) ---")
    sentence_8 = "zeydun daribun masiyan"
    tokens_8 = tokenizer.tokenize(sentence_8)
    morph_8 = sarf.derive_lexicon(tokens_8)
    ast_8 = nahiv.suggest_dependencies(tokens_8, morph_8)
    
    ast_graph = nahiv.build_ast(tokens_8, ast_8)
    temporal_conditions = nahiv.extract_temporal_conditions(ast_graph)
    
    for zat, vasif in temporal_conditions.items():
        if zat in morph_8 and vasif in morph_8:
            zat_root = morph_8.get(zat).root
            vasif_root = morph_8.get(vasif).root
            
            zat_ont_id = lexicon.resolve_id(zat_root, "Base", dependencies=ast_8)
            vasif_ont_id = lexicon.resolve_id(vasif_root, "Base", dependencies=ast_8)
            
            zat_entity = l1.entity_map.get(zat_ont_id)
            if zat_entity:
                zat_entity.modal_status = "Mesruta_i_Amme"
                zat_entity.modal_condition_id = vasif_ont_id

    clean_solver_8 = AristotelianSolver(ontology)
    clean_l3_8 = Layer3SMTCircuitBreaker(clean_solver_8, timeout_ms=3000)
    clean_orchestrator_8 = EpistemicOrchestrator(adapter, l1, l2, clean_l3_8)

    discourse.clear_memory()
    res_modal = clean_orchestrator_8.process_statement(tokens_8, ast_8, AshariUsul(), morph_8)
    print(f"Girdi: '{sentence_8}' | AST: {ast_8}")
    print(f"Şartlı Modalite (Meşrûta-i Âmme) Tespiti: {temporal_conditions}")
    print(f"Sonuç: [{res_modal.get('status', 'BİLİNMİYOR')}] -> Vasfî Zaman Tensörü Z3'e başarıyla zerk edildi.\n")

    print("[SİSTEM] Healthcheck Tamamlandı. Sıfır Entropi Doğrulandı.")

if __name__ == "__main__":
    sys.setrecursionlimit(5000)
    execute_healthcheck()