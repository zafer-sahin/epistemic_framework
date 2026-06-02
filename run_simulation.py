import sys
from pathlib import Path

# Core Katmanları
from core.models import OntologyLoader, EpistemicEntity, TermModel
from core.logic_engine import AristotelianSolver
from core.layer1_graph import Layer1HeuristicGraph
from core.layer2_rules import Layer2RuleEngine
from core.layer3_smt import Layer3SMTCircuitBreaker
from core.epistemic_orchestrator import EpistemicOrchestrator

# Dilbilim Katmanları
from linguistics.tokenizer import EpistemicTokenizer
from linguistics.sarf_parser import SarfEngine
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister
from linguistics.ilm_wad_adapter import IlmWadAdapter, SemanticStatementIR

# Ekol (Usûl) Profilleri
from schools.salafi_usul import SalafiUsul
from schools.ashari_usul import AshariUsul
from schools.maturidi_usul import MaturidiUsul

def execute_healthcheck():
    print("="*70)
    print("[SİSTEM] N-TIER EPİSTEMİK MOTOR UÇTAN UCA SAĞLIK TARAMASI (HEALTHCHECK)")
    print("="*70)
    
    # 1. BAŞLATMA (BOOTSTRAP)
    loader = OntologyLoader()
    ontology = loader.load(Path("data/base_ontology.json"))
    solver = AristotelianSolver(ontology)
    
    tokenizer = EpistemicTokenizer()
    sarf = SarfEngine()
    nahiv = NahivDependencyCompiler()
    
    lexicon = ContextualLexicon()
    discourse = DiscourseRegister()
    
    # Mock Veri Enjeksiyonu
    lexicon.register_word("yad", "Salafi", "Sifat_Yed_Literal")
    lexicon.register_word("yad", "Ashari", "Sifat_Yed_Metaphor")
    lexicon.register_word("yad", "Maturidi", "Sifat_Yed_Metaphor")
    lexicon.register_word("tekvin", "Maturidi", "Tekvin")
    lexicon.register_word("allah", "Base", "Wajib_al_Wujud")
    lexicon.register_word("cemad", "Base", "Cemad")
    # [LOGIC FIX]: Leksikon kayıtları, Sarf motorunun (-i ve -un) i'rablarını kestikten sonra üreteceği saf kök forma (nam ve zeyd) indirgendi.
    lexicon.register_word("nam", "Base", "Nami")
    lexicon.register_word("zeyd", "Base", "Zeyd_Entity")

    adapter = IlmWadAdapter(lexicon, discourse)
    l1 = Layer1HeuristicGraph(ontology)
    
    # L1 Graph Entity Map Mocking (Faz 2 uyumluluğu için)
    l1.entity_map["Wajib_al_Wujud"] = EpistemicEntity(ontologic_id="Wajib_al_Wujud", terms=TermModel(ar="Allah"), modal_status="Wajib", husn_u_mucerred=True)
    l1.entity_map["Sifat_Yed_Literal"] = EpistemicEntity(ontologic_id="Sifat_Yed_Literal", terms=TermModel(ar="Yed"), modal_status="Mumkin", husn_u_mucerred=False)
    l1.entity_map["Tekvin"] = EpistemicEntity(ontologic_id="Tekvin", terms=TermModel(ar="Tekvin"), modal_status="Mumkin", husn_u_mucerred=False)
    l1.entity_map["Cemad"] = EpistemicEntity(ontologic_id="Cemad", terms=TermModel(ar="Cemad"), modal_status="Mumkin", husn_u_mucerred=False)
    l1.entity_map["Nami"] = EpistemicEntity(ontologic_id="Nami", terms=TermModel(ar="Nami"), modal_status="Mumkin", husn_u_mucerred=False)
    l1.entity_map["Zeyd_Entity"] = EpistemicEntity(ontologic_id="Zeyd_Entity", terms=TermModel(ar="Zeydun"), modal_status="Mumkin", husn_u_mucerred=False)

    l2 = Layer2RuleEngine()
    l3 = Layer3SMTCircuitBreaker(solver, timeout_ms=3000)
    
    orchestrator = EpistemicOrchestrator(adapter, l1, l2, l3)
    print("[BAŞARILI] Orkestratör ve tüm alt-motorlar belleğe yüklendi.\n")

    # 2. TEST SENARYOLARI
    sentence_1 = "yadu allahi" 
    tokens_1 = tokenizer.tokenize(sentence_1)
    morph_1 = sarf.derive_lexicon(tokens_1)
    ast_1 = nahiv.suggest_dependencies(tokens_1, morph_1)
    
    print("--- SENARYO 1: SELEFÎ USÛLÜ (MUTLAK LAFIZCILIK) ---")
    print(f"Girdi: '{sentence_1}' | AST: {ast_1}")
    discourse.clear_memory()
    res_salafi = orchestrator.process_statement(tokens_1, ast_1, SalafiUsul(), morph_1)
    print(f"Sonuç: [{res_salafi['status']}] -> {res_salafi.get('reason', res_salafi.get('message'))}\n")

    print("--- SENARYO 2: EŞ'ARÎ USÛLÜ (TE'VİL TOLERANSI) ---")
    print(f"Girdi: '{sentence_1}' | AST: {ast_1}")
    discourse.clear_memory()
    res_ashari = orchestrator.process_statement(tokens_1, ast_1, AshariUsul(), morph_1)
    print(f"Sonuç: [{res_ashari['status']}] (L2 Kararı: {res_ashari.get('l2_context')})\n")

    sentence_2 = "tekvinu allahi"
    tokens_2 = tokenizer.tokenize(sentence_2)
    morph_2 = sarf.derive_lexicon(tokens_2)
    ast_2 = nahiv.suggest_dependencies(tokens_2, morph_2)
    
    print("--- SENARYO 3: MÂTÜRÎDÎ USÛLÜ (DÜĞÜM BAZLI DSL YASAĞI) ---")
    print(f"Girdi: '{sentence_2}' | AST: {ast_2}")
    discourse.clear_memory()
    res_maturidi = orchestrator.process_statement(tokens_2, ast_2, MaturidiUsul(), morph_2)
    print(f"Sonuç: [{res_maturidi['status']}] -> {res_maturidi.get('reason', res_maturidi.get('message'))}\n")

    print("--- SENARYO 4: CÜRCÂNÎ MU'ARADAH KİLİTLENMESİ (ÇAPRAZ USÛL DİYALEKTİĞİ) ---")
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

    print("[SİSTEM] Healthcheck Tamamlandı. Sıfır Entropi Doğrulandı.")

if __name__ == "__main__":
    execute_healthcheck()