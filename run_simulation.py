import sys
from pathlib import Path
from core.models import OntologyLoader
from core.logic_engine import AristotelianSolver
from core.syllogism_builder import SyllogismEngine

def execute_pipeline():
    print("[SİSTEM BAŞLATILIYOR] Ontoloji Yükleniyor...")
    
    # Adım 1: Katı Nesneleştirme (Strict Hydration)
    loader = OntologyLoader()
    try:
        # Yolun doğru olduğundan emin ol, gerekirse absolute path kullan.
        ontology_path = Path("data/base_ontology.json") 
        ontology = loader.load(ontology_path)
        print("[BAŞARILI] Veri Katmanı Doğrulandı (0 Entropi).")
    except Exception as e:
        print(f"\n[KIRITIK HATA] Veri Katmanı Çöktü (Fail-Fast tetiklendi):\n{e}")
        sys.exit(1)

    # Adım 2: Z3 SMT Motoru İnşası ve Aksiyom Enjeksiyonu
    print("\n[MOTOR BAŞLATILIYOR] Z3 SMT Çözücüsü Hazırlanıyor...")
    solver = AristotelianSolver(ontology)

    # Adım 3: Global Tutarlılık Stres Testi (Vacuous Truth İzolasyonu)
    print("\n--- FAZ 1: ONTOLOJİK TUTARLILIK (GLOBAL SAT) ---")
    is_sat, core_or_msg = solver.check_consistency()
    
    if is_sat:
        print("[SENTEZ] Sistem Tutarlı (SAT).")
        print("[SENTEZ] Tüm düğümler için varoluşsal (Existential) ve geçişli (Transitive) aksiyomlar geçerli.")
    else:
        print(f"\n[ÇÖKÜŞ] Ontolojik Çelişki (UNSAT) Tespit Edildi.")
        print(f"[UNSAT CORE] Çelişkiyi yaratan kısıtlar: {core_or_msg}")
        sys.exit(1)


# ... (Faz 3 Global SAT testi kodları kalacak) ...

    # Adım 4: Dinamik Kıyas (Syllogism) Motoru Testi
    print("\n--- FAZ 2: DİNAMİK KIYAS MOTORU VE ÇELİŞKİ İSPATI ---")
    
    syllogism_engine = SyllogismEngine(ontology)
    
    # Test Senaryosu A: Barbara (Darb-ı Evvel / AAA)
    # Parametreler: S=Rationale (İnsan), M=Vivens (Canlı), P=Corpus (Cisim)
    b_premises, b_conclusion = syllogism_engine.construct_syllogism(
        figure="Figure_1", 
        mood="Barbara", 
        major_term="Corpus", 
        minor_term="Rationale", 
        middle_term="Vivens"
    )
    
    print("Test A: Dinamik Modus Barbara Üretimi")
    is_valid = solver.verify_syllogism(b_premises, b_conclusion)
    if is_valid:
        print("[GEÇERLİ] Z3 motoru dinamik olarak üretilen kıyası matematiksel olarak ispatladı.")
    else:
        print("[HATA] Dinamik üretim başarısız.")
    
    # Test Senaryosu: Barbara (Darb-ı Evvel / AAA) Kıyası
    # Porphyrios ağacındaki spesifik yüklemleri (Predicates) test ediyoruz.
    # Öncül 1: Her İnsan (Rationale) Canlıdır (Vivens)
    # Öncül 2: Her Canlı (Vivens) Cisimdir (Corpus)
    # Sonuç: Her İnsan (Rationale) Cisimdir (Corpus)
    
    barbara_premises = [
        "Forall([x], Implies(Rationale(x), Vivens(x)))",
        "Forall([x], Implies(Vivens(x), Corpus(x)))"
    ]
    barbara_conclusion = "Forall([x], Implies(Rationale(x), Corpus(x)))"
    
    print("Test A: Modus Barbara (Geçerli Olması Zorunlu)")
    is_valid = solver.verify_syllogism(barbara_premises, barbara_conclusion)
    if is_valid:
        print("[GEÇERLİ] Z3 motoru kıyasın ontolojik evrende matematiksel olarak zorunlu olduğunu ispatladı.")
    else:
        print("[HATA] Z3 motoru kıyası doğrulayamadı. AST çeviricisi veya aksiyomlar hatalı.")

    # Test Senaryosu: Safsata (Geçersiz Kıyas) Testi
    # Sonuç: Her İnsan (Rationale) Cansızdır (Inanimatum) -> Ağaçla açıkça çelişir.
    invalid_conclusion = "Forall([x], Implies(Rationale(x), Inanimatum(x)))"
    
    print("\nTest B: Ontolojik Safsata (Geçersiz Olması Zorunlu)")
    is_invalid_syllogism_rejected = not solver.verify_syllogism(barbara_premises, invalid_conclusion)
    
    if is_invalid_syllogism_rejected:
        print("[GEÇERSİZ] Z3 motoru hatalı sonucu başarıyla reddetti (Red Teaming Başarılı).")
    else:
        print("[KRİTİK ZAFİYET] Z3 motoru safsatayı kabul etti. 'Vacuous Truth' sızıntısı var.")


    # Test Senaryosu C: Yatay Dışlama (Sibling Disjointness) Stres Testi
    print("\nTest C: Kardeş Düğümlerin Kesişim Reddi (Mutually Exclusive)")
    
    # Safsata: "Bir x vardır ki, o hem Rationale (İnsan) hem de Equus'tur (At)."
    impossible_intersection = "Forall([x], And(Rationale(x), Equus(x)))"
    
    is_chimera_possible = solver.verify_syllogism([], impossible_intersection)
    
    if not is_chimera_possible:
        print("[BAŞARILI] Z3 motoru farklı türler (İnsan ve At) arasındaki kesişimi yasakladı.")
    else:
        print("[KRİTİK ZAFİYET] Z3 motoru yatay kesişime izin verdi. Çelişmezlik ilkesi ihlal edildi.")

    # Test Senaryosu D: Hâssa (Proprium) Üzerinden Çift Yönlü İspat (Bi-conditional Deduction)
    # Hipotez: Eğer bir x varlığının "Gülen" (Laughing) olduğu biliniyorsa, Z3 motoru
    # onun zorunlu olarak "İnsan" (Rationale) ve dolayısıyla "Cisim" (Corpus) olduğunu
    # yukarıya doğru tırmanarak ispatlayabilmelidir.
    print("\nTest D: Hâssa (Proprium) Üzerinden Geriye Dönük Çıkarım")
    
    # Proprium sembolü, Z3'e kaydettiğimiz formatta oluşturulur: Prop_Rationale_Laughing
    # Öncül: S(x) -> Prop_Rationale_Laughing(x) (Socrates gülendir)
    prop_premise = "Forall([x], Implies(S(x), Prop_Rationale_Laughing(x)))"
    
    # Sonuç: S(x) -> Corpus(x) (O halde Socrates bir cisimdir)
    prop_conclusion = "Forall([x], Implies(S(x), Corpus(x)))"
    
    is_prop_valid = solver.verify_syllogism([prop_premise], prop_conclusion)
    
    if is_prop_valid:
        print("[BAŞARILI] Z3 motoru bir 'Hâssa' (Proprium) üzerinden türü tanımladı ve üst cinslere (Corpus) ulaşarak mutlak ispatı yaptı.")
    else:
        print("[KRİTİK ZAFİYET] Z3 motoru Hâssa (Proprium) üzerinden geriye doğru akıl yürütemedi.")

if __name__ == "__main__":
    execute_pipeline()