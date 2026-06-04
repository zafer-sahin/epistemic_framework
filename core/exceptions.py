class EpistemicEngineError(Exception):
    """
    Epistemic Framework N-Tier Motoru temel exception sınıfı.
    Sistemin felsefi, mantıksal veya teolojik kurallarının ihlalinde fırlatılır.
    """
    pass

class DiachronicViolationError(EpistemicEngineError):
    """
    [FAZ 1 - ONTOLOJİK SIZINTI KORUMASI]
    Sisteme Klasik Arapça (CA) evreni dışında (Örn: Modern Standart Arapça, 
    seküler sözlükler veya aracı İngilizce çeviriler) bir kelime veya ontolojik 
    düğüm girmeye çalıştığında (Semantic Shift / Generalization) fırlatılır.
    Leksikon tensöründeki 'epoch' boyutunun 'Classical' olmasını zorunlu kılar.
    """
    pass

class OutOfOntologyError(EpistemicEngineError):
    """
    [FAZ 1 - AIR-GAPPED ONTOLOGY]
    Sarf motoru geçerli bir kelime türetse bile, bu kelime statik ve mühürlü 
    Porphyrios Ağacı'nda (Base Ontology) tanımlı bir Cins (Genus) veya Nev' (Species)
    düğümüne bağlanamıyorsa fırlatılır. Seküler kavram kilitlerini işletir.
    """
    pass

class ContextPoisoningError(EpistemicEngineError):
    """
    [FAZ 4 - SÖYLEM BELLEĞİ YALITIMI]
    Seyyid Şerif el-Cürcânî'nin Âdâb-ı Bahs (Münazara Kuralları) işletilirken,
    Sâil ve Mucîb'in çapraz sorgularında (Mu'aradah) farklı uzaylardan (namespaces) 
    gelen zamirlerin (Anafora) birbirine karışmasını engeller.
    """
    pass

class CombinatorialExplosionError(EpistemicEngineError):
    """
    Z3 SMT çözücüsünde, Birinci Dereceden Mantık (FOL) matrislerinin 
    Kripke Kısıtları (Dünya ve Zaman) altında sonsuz döngüye girmesini (Undecidability) 
    engellemek adına devreyi kesen donanımsal hata sınıfıdır.
    """
    pass