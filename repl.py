import cmd
import sys
import traceback
from pathlib import Path

from core.models import OntologyLoader
from core.logic_engine import AristotelianSolver
from core.layer1_graph import Layer1HeuristicGraph
from core.layer2_rules import Layer2RuleEngine
from core.layer3_smt import Layer3SMTCircuitBreaker
from core.epistemic_orchestrator import EpistemicOrchestrator

from linguistics.tokenizer import EpistemicTokenizer
from linguistics.sarf_parser import SarfEngine
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister
from linguistics.ilm_wad_adapter import IlmWadAdapter

from schools.salafi_usul import SalafiUsul
from schools.ashari_usul import AshariUsul
from schools.maturidi_usul import MaturidiUsul
from schools.taftazani.adab_al_bahth import AdabAlBahthEngine

class EpistemicShell(cmd.Cmd):
    intro = """
=============================================================================
[AKTİF] N-TIER EPİSTEMİK ÇIKARIM MOTORU VE DİYALEKTİK REPL
Durum: 0 Entropi | Rejim: Asenkron Çoklu-Ekol (Polymorphic Multi-Agent)
Varsayılan Ekol: Eş'arî (AshariUsul)
Komutlar: set_usul, parse_sentence, muaradah, claim, tahrir, evidence, attack, clear
Çıkmak için 'exit'.
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
        self.last_ir = None
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        try:
            loader = OntologyLoader()
            self.ontology = loader.load(Path("data/base_ontology.json"))
            self.solver = AristotelianSolver(self.ontology)
            
            self.tokenizer = EpistemicTokenizer()
            self.sarf = SarfEngine()
            self.nahiv = NahivDependencyCompiler()
            
            self.lexicon = ContextualLexicon()
            self.discourse = DiscourseRegister()
            
            # [FAZ 6] İbn Teymiyye Node Relocation Leksikon Yapılandırması
            self.lexicon.register_word("yad", "Salafi", "Sifat_Yed_Literal")
            self.lexicon.register_word("yad", "Salafi", "Sifat_Yed_Bila_Kayf", proposition_type="Kadiyye-i_Hamliyye", sibak_trigger="allah")
            
            # [FAZ 3] Ma'nâ el-Ma'nâ Leksikon Yapılandırması
            self.lexicon.register_word("yad", "Ashari", "Sifat_Yed_Metaphor")
            self.lexicon.register_word("yad", "Maturidi", "Sifat_Yed_Metaphor")
            self.lexicon.register_word("allah", "Base", "Wajib_al_Wujud")
            self.lexicon.register_word("tekvin", "Maturidi", "Tekvin")
            self.lexicon.register_word("nam", "Base", "Nami")
            self.lexicon.register_word("cemad", "Base", "Cemad")
            self.lexicon.register_word("zeyd", "Base", "Zeyd_Entity")
            
            self.adapter = IlmWadAdapter(self.lexicon, self.discourse)

            self.l1 = Layer1HeuristicGraph(self.ontology)
            self.l2 = Layer2RuleEngine()
            self.l3 = Layer3SMTCircuitBreaker(self.solver, timeout_ms=3000)

            self.orchestrator = EpistemicOrchestrator(self.adapter, self.l1, self.l2, self.l3)
            
            # [FAZ 5] Diyalektik FSM Motoru
            self.fsm = AdabAlBahthEngine(self.solver, self.discourse)

            print("[SİSTEM] N-Tier Boru Hattı ve Âdâb-ı Bahs FSM başarıyla başlatıldı.")
        except Exception as e:
            print(f"[KRİTİK HATA] Motor mimarisi başlatılamadı: {e}")
            sys.exit(1)

    def do_set_usul(self, arg):
        target = arg.strip().lower()
        if target in self.available_schools:
            self.active_usul = self.available_schools[target]
            self.prompt = f"Epistemic-Engine [{self.active_usul.namespace}]> "
            self.discourse.clear_memory()
            self.fsm.reset_session()
            self.last_ir = None
            print(f"[BAĞLAM DEĞİŞİMİ] Aktif Usûl Profiline Geçildi: {self.active_usul.namespace}")
        else:
            print(f"[RED] Tanımsız Usûl. Mevcut seçenekler: {list(self.available_schools.keys())}")

    def do_parse_sentence(self, arg):
        if not arg:
            print("[HATA] Analiz edilecek cümleyi girin.")
            return

        try:
            tokens = self.tokenizer.tokenize(arg)
            auto_lexicon = self.sarf.derive_lexicon(tokens)
            ast_dependencies = self.nahiv.suggest_dependencies(tokens, auto_lexicon)
            
            print(f"\n[SENTAKS] AST: {ast_dependencies}")
            
            self.last_ir = self.adapter.generate_ir(tokens, ast_dependencies, self.active_usul.namespace, auto_lexicon)
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

    def do_muaradah(self, arg):
        args = arg.split(maxsplit=1)
        if len(args) < 2:
            print("[HATA] Rakip usûl ve karşı cümleyi eksiksiz girin. Örn: muaradah salafi namun zeydun")
            return
            
        sail_usul_str, sail_sentence = args[0].strip().lower(), args[1]
        
        if sail_usul_str not in self.available_schools:
            print(f"[HATA] Geçersiz Sâil usûlü: {sail_usul_str}")
            return
            
        if not self.last_ir or not self.last_ir.is_valid_for_z3:
            print("[HATA] Çapraz sorgu için önce Mucîb (parse_sentence) olarak geçerli bir iddia sunmalısınız.")
            return

        sail_usul = self.available_schools[sail_usul_str]

        try:
            sail_tokens = self.tokenizer.tokenize(sail_sentence)
            sail_lexicon = self.sarf.derive_lexicon(sail_tokens)
            sail_ast = self.nahiv.suggest_dependencies(sail_tokens, sail_lexicon)
            
            print(f"\n[MU'ARADAH] Sâil ({sail_usul.namespace}) z3.Optimize çapraz saldırı protokolü başlatıldı...")
            
            result = self.orchestrator.execute_cross_school_muaradah(
                self.last_ir, self.active_usul, sail_tokens, sail_ast, sail_usul, sail_lexicon
            )
            
            print(f"[{result.get('status', 'BİLİNMİYOR')}] -> {result.get('message')}")
            
        except Exception as e:
            print(f"\n[SİSTEM ÇÖKÜŞÜ] Mu'aradah İhlali:")
            traceback.print_exc()

    # ==========================================
    # FAZ 5: ÂDÂB-I BAHS DİYALEKTİK KOMUTLARI
    # ==========================================

    def do_claim(self, arg):
        """[FAZ 5] Mucîb olarak tartışmaya Z3 FOL formatında iddia (Da'vâ) sürer."""
        if not arg:
            print("[HATA] Z3 FOL formatında bir iddia girin. Örn: Forall([x], Implies(Cemad(x), Nami(x)))")
            return
        try:
            res = self.fsm.submit_claim(arg)
            print(f"[{res['status']}] {res['message']}")
        except Exception as e:
            print(f"[FSM ÇÖKÜŞÜ] {e}")

    def do_tahrir(self, arg):
        """[FAZ 5] Kavramsal senkronizasyon. Format: <musellemat1,musellemat2> | <niza1,niza2>"""
        if "|" not in arg:
            print("[HATA] Format: musellem_terim | niza_terim. Örn: Cemad | Nami")
            return
        
        parts = arg.split("|")
        musellemat = [m.strip() for m in parts[0].split(",") if m.strip()]
        niza_terms = [n.strip() for n in parts[1].split(",") if n.strip()]
        
        try:
            res = self.fsm.tahrir_i_niza(musellemat, niza_terms)
            print(f"[{res['status']}] {res['message']}")
        except Exception as e:
            print(f"[FSM ÇÖKÜŞÜ] {e}")

    def do_evidence(self, arg):
        """[FAZ 5] Mucîb olarak Z3 FOL formatında delil (Öncül) sunar. Virgülle ayırarak çoklu öncül girilebilir."""
        if not arg:
            print("[HATA] Z3 FOL formatında öncül girin.")
            return
            
        premises = [p.strip() for p in arg.split(";") if p.strip()]
        try:
            res = self.fsm.submit_evidence(premises)
            print(f"[{res['status']}] {res['message']}")
        except Exception as e:
            print(f"[FSM ÇÖKÜŞÜ] {e}")

    def do_attack(self, arg):
        """[FAZ 5] Sâil olarak delile saldırır (Men, Nakz, Muaradah). Örn: attack Nakz"""
        args = arg.split(maxsplit=1)
        if not args:
            print("[HATA] Saldırı tipi belirtin: Men, Nakz, Muaradah")
            return
            
        attack_type = args[0].capitalize()
        target = args[1] if len(args) > 1 else None
        
        try:
            res = self.fsm.attack_evidence(attack_type, target)
            print(f"[{res['status']}] {res['message']}")
        except Exception as e:
            print(f"[FSM ÇÖKÜŞÜ] {e}")

    def do_clear(self, arg):
        self.discourse.clear_memory()
        self.fsm.reset_session()
        self.last_ir = None
        print("[BELLEK] Söylem hafızası ve FSM durumu sıfırlandı.")

    def do_exit(self, arg):
        print("[SİSTEM] Kapatılıyor.")
        return True

    def emptyline(self):
        pass

if __name__ == '__main__':
    EpistemicShell().cmdloop()