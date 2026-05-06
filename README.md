# Epistemic Framework (İslami Mantık ve Dilbilim Motoru)

Bu proje, Aristotelesçi/İbn Sinacı mantık geleneğini ve klasik Arapça dilbilim (Sarf/Nahiv) teorilerini, modern **Z3 SMT (Satisfiability Modulo Theories)** çözücüsü ve **Pydantic** veri modelleriyle birleştiren n-boyutlu bir bilişsel çıkarım motorudur.

## 🧠 Mimari Katmanlar

### 1. Ontolojik Çekirdek (Core)
- **Z3 SMT Integration:** Mantıksal çıkarımları Birinci Dereceden Mantık (FOL) düzeyinde çözer.
- **Porphyrian Tree:** Varlık hiyerarşisini (Cins, Fasıl, Hâssa) deterministik olarak modeller.
- **N-Ary Logic Parser:** Çok değişkenli ilişkileri (Örn: `Fail(x, y)`) dinamik olarak işleyen AST derleyicisi.

### 2. Diyalektik Motor (Schools)
- **Taftâzânî/Cürcânî Engine:** *Âdâbu'l-Bahs ve'l-Münâzara* protokollerini (Men', Nakz, İlzâm) uygular.
- **Mukâbere Defense:** Çelişkili öncüllerden hatalı sonuç türetilmesini (Ex Falso Quodlibet) engelleyen SAT denetimi.

### 3. Dilbilim Katmanı (Linguistics)
- **Sarf (Morfoloji):** Kelime köklerinden otomatik leksikon türetimi.
- **Nahiv (Sentaks):** Âmil-Ma'mûl ilişkilerini Z3 geçici bellek (Push/Pop) scope'larında doğrulayan bağımlılık derleyicisi.

## 🚀 Mevcut Yetenekler (Faz 16)
- [x] Aristotelesçi Tasım (Syllogism) üretimi ve doğrulaması.
- [x] Otonom Sözlük (Lexicon) üretimi üzerinden cümle tutarlılık analizi.
- [x] Diyalektik tartışma oturumları (Dispute Mode).
- [x] N-Ary ilişkisel matris desteği.

## 🛠 Kurulum ve Kullanım
1. Bağımlılıkları yükleyin: `pip install z3-solver pydantic`
2. REPL'i başlatın: `python3 repl.py`