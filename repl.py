from schools.taftazani.adab_al_bahth import AdabAlBahthEngine
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.sarf_parser import SarfEngine
from linguistics.tokenizer import EpistemicTokenizer

import cmd
import sys
from pathlib import Path
import z3
import ast
from core.models import OntologyLoader
from core.logic_engine import AristotelianSolver
from core.syllogism_builder import SyllogismEngine

class EpistemicShell(cmd.Cmd):
    intro = """
=========================================================
[AKTİF] ARİSTOTELESÇİ Z3 ÇIKARIM MOTORU (EPİSTEMİK REPL)
Durum: 0 Entropi | Rejim: Katı (Strict) FOL
Komutlar için 'help' yazın. Çıkmak için 'exit' veya Ctrl+D.
=========================================================
"""
    prompt = "Z3-Engine> "

    def __init__(self):
        super().__init__()
        self._initialize_engine()

    def _initialize_engine(self):
        try:
            loader = OntologyLoader()
            ontology = loader.load(Path("data/base_ontology.json"))
            self.solver = AristotelianSolver(ontology)
            self.syllogism = SyllogismEngine(ontology)
            
            # Taftazani motorunu solver bağımlılığı ile başlat
            self.dialectics = AdabAlBahthEngine(self.solver)

             #Sentaktik Bağımlılık (Nahiv) Derleyicisi
            self.nahiv_compiler = NahivDependencyCompiler(self.solver)

            #Otonom Üretken Sarf Motoru
            self.sarf_engine = SarfEngine() 
            self.tokenizer = EpistemicTokenizer()
            
            print("[SİSTEM] Ontoloji yüklendi. Global SAT doğrulandı.")
        except Exception as e:
            print(f"[KRİTİK HATA] Motor başlatılamadı: {e}")
            sys.exit(1)

    def do_check(self, arg):
        """
        Global ontolojinin tutarlılığını (SAT) denetler.
        Kullanım: check
        """
        is_sat, msg = self.solver.check_consistency()
        if is_sat:
            print("[SAT] Sistem tutarlı. Ontolojik çelişki yok.")
        else:
            print(f"[UNSAT] Sistem çöktü. Kök neden (Unsat Core): {msg}")

    def do_assert(self, arg):
        """
        Evrene geçici olmayan mutlak bir kısıt (Axiom) enjekte eder.
        Kullanım: assert Forall([x], Implies(Rationale(x), Kâtip(x)))
        """
        if not arg:
            print("[HATA] Bir argüman girilmelidir.")
            return
        
        try:
            expr = self.solver.builder.parse(arg)
            self.solver.solver.add(expr)
            print(f"[KABUL] Kısıt evrene eklendi: {expr}")
        except Exception as e:
            print(f"[RED] Sentaks veya Derleme Hatası: {e}")

    def do_query(self, arg):
        """
        Dışarıdan verilen bir hipotezin ontolojik evrende ZORUNLU olup olmadığını test eder.
        (Çelişkiyle ispat metodunu kullanır, evrenin state'ini bozmaz).
        Kullanım: query Forall([x], Implies(Rationale(x), Corpus(x)))
        """
        if not arg:
            print("[HATA] Bir argüman girilmelidir.")
            return

        is_valid = self.solver.verify_syllogism([], arg)
        if is_valid:
            print("[İSPATLANDI / ZORUNLU] (GEÇERLİ)")
        else:
            print("[REDDEDİLDİ / ZORUNLU DEĞİL] (GEÇERSİZ veya MÜMKÜN)")

    def do_learn(self, arg):
        """
        Zorunlu olduğu ispatlanan bir hipotezi ontolojik veri katmanına (JSON) kalıcı olarak yazar.
        Kullanım: learn Forall([x], Implies(Rationale(x), Corpus(x)))
        """
        if not arg:
            print("[HATA] Bir argüman girilmelidir.")
            return

        # Adım A: Mantıksal Geçerlilik (Validity) Testi
        print("[SİSTEM] Hipotez Z3 motorunda test ediliyor...")
        is_valid = self.solver.verify_syllogism([], arg)
        
        if not is_valid:
            print("[REDDEDİLDİ] Bu hipotez mevcut ontolojide ZORUNLU DEĞİL. Veri katmanına yazılamaz.")
            return

        # Adım B: Pydantic Model Modifikasyonu
        print("[İSPATLANDI] Hipotez geçerli. Veri yapısına entegre ediliyor...")
        try:
            # Yeni öncül için dinamik bir anahtar (key) üretimi
            import time
            from core.models import TermModel
            
            rule_id = f"Derived_Axiom_{int(time.time())}"
            
            # Sadece İngilizce (en) referansını doldurarak basit bir TermModel oluştur
            new_term = TermModel(en=arg)
            
            # Bellekteki ontoloji objesini güncelle
            self.solver.ontology.logical_components.premises[rule_id] = new_term
            
            # Adım C: Fiziksel Diske Yazma (Serialization)
            # Pydantic model_dump_json ile strict kuralları koruyarak JSON'ı ez
            ontology_path = Path("data/base_ontology.json")
            json_data = self.solver.ontology.model_dump_json(indent=4, by_alias=True, exclude_none=True)
            
            ontology_path.write_text(json_data, encoding="utf-8")
            print(f"[BAŞARILI] Yeni teorem JSON dosyasına mühürlendi: {rule_id}")
            
            # Motorun evrenine kalıcı olarak ekle ki anlık REPL seansında da aktif olsun
            expr = self.solver.builder.parse(arg)
            self.solver.solver.add(expr)
            
        except Exception as e:
            print(f"[KRİTİK HATA] Veri katmanına yazma (I/O) başarısız oldu: {e}")
        
    def do_define(self, arg):
        """
        Bir varlığın Aristotelesçi mutlak tanımını (Hadd-i Tam: Yakın Cins + Fasıl) 
        ve ontolojik kalıtım şeceresini deterministik olarak hesaplar.
        Kullanım: define Rationale
        """
        if not arg:
            print("[HATA] Hedef varlığın ontolojik ismini girin. (Örn: define Rationale)")
            return

        # Bağımlılık (Dependency) hatası yaratmamak için REPL içi izole DFS arama motoru
        def find_path(node, target, path):
            if node.name == target:
                return path + [node]
            for child in node.children:
                result = find_path(child, target, path + [node])
                if result:
                    return result
            return None

        # Bellekteki (Hydrated) Porphyrios Ağacının kökünden aramayı başlat
        root = self.solver.ontology.porphyrian_tree.root
        path = find_path(root, arg, [])

        if not path:
            print(f"[RED] '{arg}' sembolü ontolojik evrende bulunamadı (Undefined Entity).")
            return

        entity = path[-1]
        parent = path[-2] if len(path) > 1 else None

        print(f"\n{'='*50}\n[{arg.upper()}] MUTLAK TANIMI (DEFINITIO)\n{'='*50}")
        
        # 1. Cins (Genus - Üst Küme)
        genus = parent.name if parent else "[KÖK VARLIK - CİNSİ YOK (Summum Genus)]"
        
        # 2. Fasıl (Differentia - Yatay Ayırıcı Kısıt)
        diff = "Yok"
        if entity.differentia:
             diff = entity.differentia.en or entity.differentia.tr or "Tanımsız"
             
        # Aristotelesçi Hadd-i Tam (Cins + Fasıl)
        print(f"Hadd-i Tam (Tanım)      : {genus} olan ve '{diff}' özelliği taşıyan varlıktır.")
        
        # 3. Hâssalar (Propria - Z3 Bi-conditional Tetikleyicileri)
        propria = [p.en or p.tr for p in entity.propria] if entity.propria else ["Yok"]
        print(f"Zorunlu Nitelik (Hâssa) : {', '.join(propria)}")
        
        # 4. Ontolojik Şecere (Lineage - Geçişlilik/Transitivity Zinciri)
        lineage_names = [n.name for n in reversed(path)]
        print(f"Geçişlilik Zinciri      : {' -> '.join(lineage_names)}")
        print("=" * 50 + "\n")

    def do_syllogism(self, arg):
        """
        Dinamik Kıyas Motorunu tetikler.
        Kullanım: syllogism <Figure> <Mood> <Major> <Minor> <Middle>
        Örnek: syllogism Figure_1 Barbara Corpus Rationale Vivens
        """
        args = arg.split()
        if len(args) != 5:
            print("Kullanım Hatası. Örnek: syllogism Figure_1 Barbara Corpus Rationale Vivens")
            return
            
        fig, mood, major, minor, middle = args
        try:
            premises, conclusion = self.syllogism.construct_syllogism(fig, mood, major, minor, middle)
            print(f"\n[ÖNCÜL 1] {premises[0]}")
            print(f"[ÖNCÜL 2] {premises[1]}")
            print(f"[SONUÇ]   {conclusion}")
            
            is_valid = self.solver.verify_syllogism(premises, conclusion)
            print(f"\n[MOTOR SONUCU] {'GEÇERLİ (ZORUNLU)' if is_valid else 'GEÇERSİZ'}")
        except Exception as e:
            print(f"[HATA] {e}")

    def do_exit(self, arg):
        """Sistemi kapatır."""
        print("[SİSTEM] Kapatılıyor.")
        return True

    def emptyline(self):
        pass

    def do_dispute(self, arg):
        """
        Taftâzânî / Cürcânî Diyalektik Motoru (Âdâbu'l-Bahs).
        Kullanım: dispute Forall([x], Implies(Corpus(x), Rationale(x)))
        """
        if not arg:
            print("[HATA] Bir iddia (Da'vâ) girilmelidir.")
            return

        print(f"\n{'='*50}\n[MÜNÂZARA BAŞLADI] İddia: {arg}\n{'='*50}")
        
        # Faz 1: İddia Değerlendirmesi
        claim_result = self.dialectics.evaluate_claim(arg)
        
        if claim_result["status"] == "ERROR":
            print(f"[FASİD İDDİA] {claim_result['message']}")
            return
        elif claim_result["status"] == "TAHSIL_I_HASIL":
            print(f"[TESLİM] {claim_result['message']}")
            return
            
        print(f"[{claim_result['status']}] {claim_result['message']}")
        print("Delilinizi (Öncüller) FOL formatında noktalı virgülle (;) ayırarak girin veya 'terk' yazın.\n")
        
        delil_input = input("Müddeî > ")
        if delil_input.lower().strip() == 'terk':
            print("[SONUÇ] Müddeî çekildi.")
            return
            
        premises = [p.strip() for p in delil_input.split(';') if p.strip()]
        
        # Faz 2: Delil Değerlendirmesi
        print("\n[TAHKİK] Deliller Z3 Motorunda çözümleniyor...")
        evidence_result = self.dialectics.evaluate_evidence(arg, premises)
        
        print(f"[{evidence_result['status']}] {evidence_result['message']}")

    def do_parse(self, arg):
        """
        Otonom Morfolojik ve Sentaktik AST Doğrulama.
        Kullanım: parse [('Daraba', 'Zeydun', 'Fail', 'Marfu')]
        """
        if not arg:
            print("[HATA] Sentaktik AST dizisi girilmelidir.")
            return

        try:
            dependencies = ast.literal_eval(arg.strip())
            if not isinstance(dependencies, list):
                raise ValueError("Girdi, Tuple'lardan oluşan bir liste ([]) formatında olmalıdır.")

            print(f"\n{'='*50}\n[FAZ 1] SARF MOTORU: Kelimeler Morfolojik Olarak Çözümleniyor...")
            
            # Cümledeki tüm benzersiz (unique) kelimeleri çıkart
            unique_words = set()
            for amil, mamul, _, _ in dependencies:
                unique_words.add(amil)
                unique_words.add(mamul)
                
            # Sarf motoru ile Lexicon'u otomatik türet
            auto_lexicon = self.sarf_engine.derive_lexicon(list(unique_words))
            print(f"[BAŞARILI] Otomatik Leksikon Üretildi: {auto_lexicon}")

            print(f"\n[FAZ 2] NAHİV MOTORU: Sentaks ve Ontoloji Z3 Geçici Scope'ta Çarpıştırılıyor...\n{'='*50}")
            
            is_valid = self.nahiv_compiler.verify_sentence_ast(dependencies, auto_lexicon)
            
            if is_valid:
                print("[GEÇERLİ - SAT] Cümle dizilimi ve kelime türleri ontolojik aksiyomlarla kusursuz uyuşuyor.")
            else:
                print("[MANTIK HATASI - UNSAT] ÇELİŞKİ TESPİT EDİLDİ!")
                print("Cümlenin bağımlılık kurgusu (AST), kelimelerin morfolojik türleriyle (Sarf) uyuşmuyor.")

        except Exception as e:
            print(f"[SİSTEM HATASI]: {e}")


    def do_parse_sentence(self, arg):
        """
        Ham metni alıp Tokenize-Sarf-Nahiv-Z3 boru hattında otonom olarak doğrular.
        Kullanım: parse_sentence Daraba Zeydun Amran
        """
        try:
            # 1. Tokenization
            tokens = self.tokenizer.tokenize(arg)
            
            # 2. Otonom Sarf (Lexicon Generation)
            lexicon = self.sarf_engine.derive_lexicon(tokens)
            
            # 3. Otonom Nahiv (Dependency Suggestion)
            ast_suggested = self.nahiv_compiler.suggest_dependencies(tokens, lexicon)
            
            print(f"\n[SİSTEM] Önerilen AST: {ast_suggested}")
            
            # 4. Z3 Semantik/Sentaktik Çarpıştırma
            is_valid = self.nahiv_compiler.verify_sentence_ast(ast_suggested, lexicon)
            
            if is_valid:
                print("[GEÇERLİ - SAT] Cümle ontolojik ve sentaktik olarak tescillendi.")
            else:
                print("[UNSAT] Cümle kurgusunda mantıksal çelişki tespit edildi.")
        except Exception as e:
            print(f"[HATA] {e}")

if __name__ == '__main__':
    EpistemicShell().cmdloop()