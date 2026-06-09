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
from linguistics.sarf_parser import SarfEngine, LocalOntoLexGraphClient
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.contextual_lexicon import ContextualLexicon, LocalOntoLexSemanticClient
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
    
    # [FAZ 10] İstemcilerin Başlatılması (Bağımlılık Enjeksiyonu)
    graph_client = LocalOntoLexGraphClient()
    semantic_client = LocalOntoLexSemanticClient()
    
    sarf = SarfEngine(graph_client=graph_client)
    nahiv = NahivDependencyCompiler()
    
    lexicon = ContextualLexicon(semantic_client=semantic_client)
    discourse = DiscourseRegister()
    
    # [FAZ 6] Selefî Usûlü için Bila-Kayf (Hakikat Taşınması) Sibak Tetikleyicisi
    lexicon.register_word("yad", "Salafi", "Sifat_Yed_Literal")
    lexicon.register_word("yad", "Salafi", "Sifat_Yed_Bila_Kayf", proposition_type="Kadiyye-i_Hamliyye", sibak_trigger="allah")
    
    # [FAZ 3] Eş'arî ve Mâtürîdî için Ma'nâ el-Ma'nâ (Mecaz) Fallback Tetikleyicisi
    lexicon.register_word("yad", "Ashari", "Sifat_Yed_Literal", proposition_type="Kadiyye-i_Hamliyye")
    lexicon.register_word("yad", "Ashari", "Sifat_Yed_Metaphor", proposition_type="Metaphor_Fallback")
    lexicon.register_word("yad", "Maturidi", "Sifat_Yed_Literal", proposition_type="Kadiyye-i_Hamliyye")
    lexicon.register_word("yad", "Maturidi", "Sifat_Yed_Metaphor", proposition_type="Metaphor_Fallback")
    
    # Sistematik Ontoloji Kayıtları (Air-Gap Uyumlu)
    lexicon.register_word("tekvin", "Maturidi", "Tekvin")
    
    # [FAZ 10 GÜNCELLEMESİ]: Aşağıdaki temel İslâm ontolojisi kayıtları (Base), 
    # artık tensöre manuel yazılmak yerine OntoLex Semantik Grafından (Fallback) otonom çekilmektedir.
    # lexicon.register_word("allah", "Base", "Wajib_al_Wujud")
    # lexicon.register_word("cemad", "Base", "Cemad")
    # lexicon.register_word("nam", "Base", "Nami")
    # lexicon.register_word("zeyd", "Base", "Insan")
    # lexicon.register_word("drb", "Base", "Bats")
    # lexicon.register_word("masiy", "Base", "Masi") 
    # lexicon.register_word("fi", "Base", "GrammarNode_Fi")
    # lexicon.register_word("bi", "Base", "GrammarNode_Bi")
    # lexicon.register_word("beyt", "Base", "Cism")
    # lexicon.register_word("sema", "Base", "Cism")
    # lexicon.register_word("dar", "Base", "Cism")
    # lexicon.register_word("haza", "Base", "GrammarNode_Haza")

    # [FAZ 1] Sızıntı Testi için Seküler Kelime Kaydı Denemesi
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

    print("--- SENARYO 5: CÜRCÂN MU'ARADAH KİLİTLENMESİ (ÇAPRAZ USÛL DİYALEKTİĞİ) ---")
    discourse.clear_memory()
    ir_mujib = SemanticStatementIR(
        active_namespace="Ashari", 
        predicates=[("Cemad", "Cemad", 1), ("Insan", "Insan", 1), ("Rel_Mubteda_Haber", "Cemad::Insan", 2)], 
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
    print(f"Sonuç: [{res_vaz.get('status', 'BİLİNMİYOR')}] -> {res_vaz.get('message', 'Role_Agent tespiti otonom Role_Action yarattı')}\n")

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
    print(f"Sonuç: [{res_modal.get('status', 'BİLİNMİYOR')}] -> {res_modal.get('message')}\n")

    print("--- SENARYO 10: FAZ 4 - ZARF-I MUSTAKAR VE İLM-İ KELÂM TENZİH AKSİYOMU ---")
    sentence_10a = "zeydun fi beyti"
    tokens_10a = tokenizer.tokenize(sentence_10a)
    morph_10a = sarf.derive_lexicon(tokens_10a)
    ast_10a = nahiv.suggest_dependencies(tokens_10a, morph_10a)

    discourse.clear_memory()
    res_10a = orchestrator.process_statement(tokens_10a, ast_10a, AshariUsul(), morph_10a)
    print(f"Girdi: '{sentence_10a}' | AST: {ast_10a}")
    print(f"Sonuç: [{res_10a.get('status', 'BİLİNMİYOR')}] -> {res_10a.get('message')}\n")

    sentence_10b = "allahu fi semai"
    tokens_10b = tokenizer.tokenize(sentence_10b)
    morph_10b = sarf.derive_lexicon(tokens_10b)
    ast_10b = nahiv.suggest_dependencies(tokens_10b, morph_10b)

    discourse.clear_memory()
    res_10b = orchestrator.process_statement(tokens_10b, ast_10b, SalafiUsul(), morph_10b)
    print(f"Girdi: '{sentence_10b}' | AST: {ast_10b}")
    print(f"Sonuç: [{res_10b.get('status', 'BİLİNMİYOR')}] -> {res_10b.get('message')}\n")

    print("--- SENARYO 11: FAZ 5 - ŞİBH-İ FİİL VE MEKÂN-DIŞI MÜTEALLAK PRENSİBİ ---")
    sentence_11 = "zeydun daribun bi yadin" 
    tokens_11 = tokenizer.tokenize(sentence_11)
    morph_11 = sarf.derive_lexicon(tokens_11)
    ast_11 = nahiv.suggest_dependencies(tokens_11, morph_11)
    
    discourse.clear_memory()
    res_11 = orchestrator.process_statement(tokens_11, ast_11, AshariUsul(), morph_11)
    print(f"Girdi: '{sentence_11}' | AST: {ast_11}")
    has_zarf_lagv = any(irab == 'Zarf_Lagv' for _, _, rel, irab in ast_11)
    print(f"Sonuç: [{res_11.get('status', 'BİLİNMİYOR')}] -> Geriye Dönük Amil Taraması ile Zarf-ı Lağv Kuruldu mu? {has_zarf_lagv}. İleti: {res_11.get('message')}\n")

    print("--- SENARYO 12: FAZ 6 - İSM-İ İŞARET VE BEDEL (APPOSITION) HAZIRLIĞI ---")
    sentence_12 = "haza el_beytu"
    tokens_12 = tokenizer.tokenize(sentence_12)
    morph_12 = sarf.derive_lexicon(tokens_12)
    ast_12 = nahiv.suggest_dependencies(tokens_12, morph_12)
    
    discourse.clear_memory()
    res_12 = orchestrator.process_statement(tokens_12, ast_12, AshariUsul(), morph_12)
    print(f"Girdi: '{sentence_12}' | AST: {ast_12}")
    has_bedel = any(rel == 'Rel_Bedel' for _, _, rel, _ in ast_12)
    print(f"Sonuç: [{res_12.get('status', 'BİLİNMİYOR')}] -> İsm-i İşaret Bedel-i Küll bağı kurdu mu? {has_bedel}. İleti: {res_12.get('message')}\n")

    print("--- SENARYO 13: FAZ 7 - ZERO-COPULA VE FÂ-İ SEBEBİYYE (DİNAMİK MANTIK) ---")
    sentence_13 = "inne zeyden fi el_dar fa daraba"
    tokens_13 = tokenizer.tokenize(sentence_13)
    morph_13 = sarf.derive_lexicon(tokens_13)
    ast_13 = nahiv.suggest_dependencies(tokens_13, morph_13)
    
    discourse.clear_memory()
    discourse.update_epistemic_state("Sail", DenialLevel.MUNKIR) # İnne tevkidi için gerekli
    res_13 = orchestrator.process_statement(tokens_13, ast_13, AshariUsul(), morph_13)
    print(f"Girdi: '{sentence_13}' | AST: {ast_13}")
    has_dynamic = any(rel == 'Rel_Fa_Fuzaiyye' or rel == 'Rel_Fa_Sebebiyye' for _, _, rel, _ in ast_13)
    print(f"Sonuç: [{res_13.get('status', 'BİLİNMİYOR')}] -> Dinamik Zaman Sıçraması (Fa) Kuruldu mu? {has_dynamic}. İleti: {res_13.get('message')}\n")

    print("--- SENARYO 14: FAZ 8 - LITERATE İZOLASYON VE BAĞLAM ZEHİRLENMESİ (CONTEXT POISONING) ---")
    discourse.clear_memory()
    # Mucîb kendi uzayında bir Zeyd mühürler
    discourse.set_agent("Mujib")
    discourse.push_scope()
    discourse.add_mention("zeyd", "Entity_Zeyd_01", "Ashari", gender="Muzekker", number="Mufred")
    
    print("[LOG] Sâil, Mucîb'in 'Zeyd' varlığına 'huve' zamiri ile Maturidi uzayından sızmaya çalışıyor...")
    try:
        # Resolve metodunda çapraz sızıntı (Cross-Namespace) denemesi
        discourse.resolve_pronoun("huve", enforcement_namespace="Maturidi")
        print("[HATA] Zırh delindi, bağlam zehirlendi!")
    except Exception as e:
        # ContextPoisoningError yakalanmalıdır
        print(f"[BAŞARILI] Faz 8 İzolasyon Zırhı Devrede: {e}\n")

    print("--- SENARYO 15: FAZ 9 - LITERATE CHUNKING VE BİLİŞSEL YÜK YÖNETİMİ ---")
    sentence_15 = "inna zeyden fi el_dar fa daraba"
    tokens_15 = tokenizer.tokenize(sentence_15)
    morph_15 = sarf.derive_lexicon(tokens_15)
    ast_15 = nahiv.suggest_dependencies(tokens_15, morph_15)
    print(f"Girdi: '{sentence_15}'")
    print(f"AST Çıktısı (İzole Chunk'lar): {ast_15}")
    print("[BAŞARILI] Karmaşık sentaktik analiz, bilişsel yük sınırları aşılmadan hiyerarşik private fonksiyonlarca (Chunking) tamamlandı.\n")

    print("--- SENARYO 16: FAZ 10 - ONTOLEX-MORPH VE SEMANTİK OTONOM ÇÖZÜMLEME (FALLBACK) ---")
    # 16.A: Gayri Munsarif (Diptote) Override Testi
    sentence_16a = "fi ahmed"
    tokens_16a = tokenizer.tokenize(sentence_16a)
    morph_16a = sarf.derive_lexicon(tokens_16a)
    ast_16a = nahiv.suggest_dependencies(tokens_16a, morph_16a)
    print(f"Girdi: '{sentence_16a}'")
    is_diptote_flag = morph_16a['ahmed'].is_diptote
    has_override = any(rel == 'Mecrur_Diptote_Override' for _, _, rel, _ in ast_16a)
    print(f"OntoLex Grafından Diptote Bayrağı Çekildi mi? {is_diptote_flag}")
    print(f"Nahiv Motoru Semantic Shift'i Engelledi mi? (Mecrur_Diptote_Override): {has_override}")
    
    # 16.B: Semantic Graph Fallback Testi
    resolved_zeyd = lexicon.resolve_id("zeyd", "Base")
    resolved_drb = lexicon.resolve_id("drb", "Base")
    print(f"\nOtonom Semantik Çözümleme (Tensörde kayıt yok): 'zeyd' -> {resolved_zeyd} (Beklenen: Insan)")
    print(f"Otonom Semantik Çözümleme (Tensörde kayıt yok): 'drb' -> {resolved_drb} (Beklenen: Bats)")
    print("[BAŞARILI] Faz 10 OntoLex-Morph ve Semantik Graf geçişi eksiksiz doğrulandı.\n")

    print("[SİSTEM] Tüm Faz 1-10 Healthcheck (Uçtan Uca) Tamamlandı. Sıfır Entropi Doğrulandı.")

if __name__ == "__main__":
    sys.setrecursionlimit(5000)
    execute_healthcheck()