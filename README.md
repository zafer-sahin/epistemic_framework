# Epistemic Framework (N-Tier İslâm Mantık ve Dilbilim Motoru)

Bu proje; Aristotelesçi/İbn Sînâcı mantık geleneğini, Klasik Arapça dilbilimini ('İlm-i Sarf ve Nahiv) ve İslâm düşünce usûllerini (Mezhep/Ekol Kuralları) modern **Z3 SMT (Satisfiability Modulo Theories)** çözücüsü ile birleştiren otonom, deterministik ve N-Katmanlı bir Bilişsel Çıkarım Motorudur.

Sistem, yapılandırılmamış doğal dil argümanlarını alır, sentaktik ve morfolojik analizden geçirir ve diyalektik (*Âdâbu'l-Bahs ve'l-Münâzara*) protokollerine göre Birinci Dereceden Mantık (FOL) matrislerinde ispatlar veya çürütür.

## 🚀 Temel Özellikler ve Mimari Yenilikler

- **Polimorfik Ontoloji (Sharding):** Tekil hakikat yanılgısı yerine Eş'arî, Selefî veya Mâtürîdî gibi farklı usûllerin kendi ontolojik gerçekliklerini izole isim alanlarında (Namespace) korumasını sağlar.
- **N-Tier Yürütme Zinciri (DAG):**
  - **L1 (Heuristic Graph):** Porphyrios Ağacı (Porphyrian Tree) üzerinde *Lowest Common Ancestor (LCA)* algoritması ile kavramlar arası ontolojik mesafeyi ölçer. Karîne-i Mânia (mecaz/te'vil) ihtimallerini matematiksel olarak saptar.
  - **L2 (Rule Engine):** Mezheplerin usûl kaidelerine göre (Örn: *Zero-Transformation* kısıtı) L1'den gelen te'vil ihtimallerini engeller veya Z3'e geçişine onay verir.
  - **L3 (SMT Circuit Breaker):** Kombinatoryal patlamaları engelleyen önbellekleme (Memoization) ve zaman aşımı limitlerine sahip izole teorem ispatlayıcı katman.
- **Diyalektik Senkronizasyon (Discourse Stack):** Söylem belleğindeki zamirlerin (Anafora - Huve, Hiye) Z3 `push/pop` stateleriyle eşzamanlı çalışarak bağlam zehirlenmesini engellediği bellek mimarisi.
- **Üretken Morfoloji ('İlm-i Sarf):** Statik kelime sözlükleri veya regex kalıpları yerine kelimelerin sessiz harf dizilimini (Consonant-Vowel İmzası) çıkartarak kalıpları (Vezin) ve kökleri deterministik olarak türeten motor.
- **Monolingual Pipeline (Sıfır Çeviri Safsatası):** Z3 motorundaki değişkenler ve aksiyomlar, Batı terminolojisinin anlamsal sapmalarından korunmak üzere saf Arapça transliterasyon (Örn: `Cevher`, `Cism`, `Insan`, `Nami`) üzerine kurulmuştur.

## ⚙️ Bileşenler ve Akış

1. **`linguistics/`**: Metni token'lara böler, *Sarf* (vezin) imzalarını çıkarır, *Nahiv* (ast) bağımlılıklarını belirler. *'İlm-i Ma'ânî* filtresi inşâî cümleleri engellerken, *'İlm-i Vaz* adaptörü bağımlılıkları semantik matrise (IR) döker.
2. **`core/`**: Orkestratör L1-L2-L3 katmanlarını yönetir. Porphyrios ağacını belleğe alır ve Pydantic veri modelleriyle doğrular.
3. **`schools/`**: Farklı usûl profillerini (`AshariUsul`, `SalafiUsul`) yönetir ve yürütme mantığını polimorfik olarak belirler.
4. **`data/`**: Z3'ün üzerine inşa edileceği mutlak varlık aksiyomlarını ve kıyas modlarını (Örn: Barbara) barındırır.

## 🛠️ Kurulum

```bash
# Python gereksinimlerini yükleyin
pip install z3-solver pydantic

# Red-Teaming (Güvenlik ve Çelişki) testlerini çalıştırın
python3 -m unittest discover tests/

# Uçtan uca sistem simülasyonunu başlatın
python3 run_simulation.py