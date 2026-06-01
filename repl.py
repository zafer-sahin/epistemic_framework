import cmd
import sys
import traceback
from pathlib import Path

# Core & Yürütme Katmanları
from core.models import OntologyLoader
from core.logic_engine import AristotelianSolver
from core.layer1_graph import Layer1HeuristicGraph
from core.layer2_rules import Layer2RuleEngine
from core.layer3_smt import Layer3SMTCircuitBreaker
from core.epistemic_orchestrator import EpistemicOrchestrator

# Dilbilim ve Semantik Katmanları
from linguistics.tokenizer import EpistemicTokenizer
from linguistics.sarf_parser import SarfEngine
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister
from linguistics.ilm_wad_adapter import IlmWadAdapter

# Polimorfik Ekol (Usûl) Profilleri
from schools.salafi_usul import SalafiUsul
from schools.ashari_usul import AshariUsul
from schools.maturidi_usul import MaturidiUsul

class EpistemicShell(cmd.Cmd):
    intro = """
=============================================================================
[AKTİF] N-TIER EPİSTEMİK ÇIKARIM MOTORU VE DİYALEKTİK REPL
Durum: 0 Entropi | Rejim: Asenkron Çoklu-Ekol (Polymorphic Multi-Agent)
Varsayılan Ekol: Eş'arî (AshariUsul)
Komutlar için 'help' yazın. Çıkmak için 'exit' veya Ctrl+D.
=============================================================================
"""
    prompt = "Epistemic-Engine [Ashari]> "

    def __init__(self):
        super().__init__()
        self.active_usul = AshariUsul()
        self.available_schools = {
            "salafi": SalafiUsul(),
            "ashari": AshariUsul(),
            "maturidi": MaturidiUsul()
        }
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        try:
            loader = OntologyLoader()
            self.ontology = loader.load(Path("data/base_ontology.json"))
            self.solver = AristotelianSolver(self.ontology)
            
            self.tokenizer = EpistemicTokenizer()
            self.sarf_engine = SarfEngine()
            self.nahiv_parser = NahivDependencyCompiler()
            
            self.lexicon = ContextualLexicon()
            self.discourse = DiscourseRegister()
            
            # Faz 9.5: Leksikon kayıtları kök (Cidr) formlarına çekildi
            self.lexicon.register_word("yad", "Salafi", "Sifat_Yed_Literal")
            self.lexicon.register_word("yad", "Ashari", "Sifat_Yed_Metaphor")
            self.lexicon.register_word("allah", "Base", "Wajib_al_Wujud")
            
            self.adapter = IlmWadAdapter(self.lexicon, self.discourse)

            self.l1 = Layer1HeuristicGraph(self.ontology)
            self.l2 = Layer2RuleEngine()
            self.l3 = Layer3SMTCircuitBreaker(self.solver, timeout_ms=3000)

            self.orchestrator = EpistemicOrchestrator(self.adapter, self.l1, self.l2, self.l3)

            print("[SİSTEM] N-Tier Boru Hattı (Pipeline) başarıyla bağlandı ve izole edildi.")
        except Exception as e:
            print(f"[KRİTİK HATA] Motor mimarisi başlatılamadı: {e}")
            sys.exit(1)

    def do_set_usul(self, arg):
        """
        Aktif diyalektik ekolü (Usûl) değiştirir.
        Kullanım: set_usul salafi | set_usul ashari
        """
        target = arg.strip().lower()
        if target in self.available_schools:
            self.active_usul = self.available_schools[target]
            self.prompt = f"Epistemic-Engine [{self.active_usul.namespace}]> "
            self.discourse.clear_memory()
            print(f"[BAĞLAM DEĞİŞİMİ] Aktif Usûl Profiline Geçildi: {self.active_usul.namespace}")
        else:
            print(f"[RED] Tanımsız Usûl. Mevcut seçenekler: {list(self.available_schools.keys())}")

    def do_parse_sentence(self, arg):
        """
        Ham metni Tokenize -> Sarf -> Nahiv (AST) -> Orkestratör (L1-L2-L3)
        zincirinden geçirerek ontolojik zorunluluğunu ve mezhepsel geçerliliğini test eder.
        Kullanım: parse_sentence yadun allahun
        """
        if not arg:
            print("[HATA] Analiz edilecek cümleyi girin.")
            return

        try:
            tokens = self.tokenizer.tokenize(arg)
            auto_lexicon = self.sarf_engine.derive_lexicon(tokens)
            
            ast_dependencies = self.nahiv_parser.suggest_dependencies(tokens, auto_lexicon)
            print(f"\n[SENTAKS] Üretilen Bağımlılık Ağacı (AST): {ast_dependencies}")

            print(f"[YÜRÜTME] Orkestratör Aktif Profil ({self.active_usul.namespace}) ile tetikleniyor...\n")
            
            # Faz 9.4 Senkronizasyonu: auto_lexicon parametresi eklendi
            result = self.orchestrator.process_statement(tokens, ast_dependencies, self.active_usul, auto_lexicon)

            print(f"[{result.get('status', 'BİLİNMİYOR')}]")
            if "reason" in result:
                print(f"Gerekçe: {result['reason']}")
            if "message" in result:
                print(f"Mesaj: {result['message']}")
            if "l2_context" in result:
                print(f"L2 Otorite Kararı: {result['l2_context']}")

        except Exception as e:
            print(f"\n[SİSTEM ÇÖKÜŞÜ] Boru Hattı İhlali:")
            traceback.print_exc()

    def do_clear_memory(self, arg):
        """Söylem belleğindeki (Anafora/Zamir) geçmiş bağlamı sıfırlar."""
        self.discourse.clear_memory()
        print("[BELLEK] Söylem hafızası sıfırlandı.")

    def do_exit(self, arg):
        """Sistemi kapatır."""
        print("[SİSTEM] Kapatılıyor.")
        return True

    def emptyline(self):
        pass

if __name__ == '__main__':
    EpistemicShell().cmdloop()