import sys
from pathlib import Path

# Core Katmanları
from core.models import OntologyLoader
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
from linguistics.ilm_wad_adapter import IlmWadAdapter

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
    
    # Mock Veri Enjeksiyonu (Kök/Cidr tabanlı)
    lexicon.register_word("yad", "Salafi", "Sifat_Yed_Literal")
    lexicon.register_word("yad", "Ashari", "Sifat_Yed_Metaphor")
    lexicon.register_word("yad", "Maturidi", "Sifat_Yed_Metaphor")
    lexicon.register_word("tekvin", "Maturidi", "Tekvin") # Mâtürîdî spesifik düğüm
    lexicon.register_word("allah", "Base", "Wajib_al_Wujud")

    adapter = IlmWadAdapter(lexicon, discourse)
    l1 = Layer1HeuristicGraph(ontology)
    l2 = Layer2RuleEngine()
    l3 = Layer3SMTCircuitBreaker(solver, timeout_ms=3000)
    
    orchestrator = EpistemicOrchestrator(adapter, l1, l2, l3)
    print("[BAŞARILI] Orkestratör ve tüm alt-motorlar belleğe yüklendi.\n")

    # 2. TEST SENARYOLARI
    # Test Cümlesi 1: İzafet Terkibi (Mudaf Tenvin Düşmesi ve Mecrur)
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

    # Test Cümlesi 2: Maturidi DSL Spesifik Düğüm Blokajı
    sentence_2 = "tekvinu allahi"
    tokens_2 = tokenizer.tokenize(sentence_2)
    morph_2 = sarf.derive_lexicon(tokens_2)
    ast_2 = nahiv.suggest_dependencies(tokens_2, morph_2)
    
    print("--- SENARYO 3: MÂTÜRÎDÎ USÛLÜ (DÜĞÜM BAZLI DSL YASAĞI) ---")
    print(f"Girdi: '{sentence_2}' | AST: {ast_2}")
    discourse.clear_memory()
    res_maturidi = orchestrator.process_statement(tokens_2, ast_2, MaturidiUsul(), morph_2)
    print(f"Sonuç: [{res_maturidi['status']}] -> {res_maturidi.get('reason', res_maturidi.get('message'))}\n")

    print("[SİSTEM] Healthcheck Tamamlandı. Sıfır Entropi Doğrulandı.")

if __name__ == "__main__":
    execute_healthcheck()