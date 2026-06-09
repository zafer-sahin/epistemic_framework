#!/bin/bash

# Çıktı dosyasını ana dizinde yaratıyoruz
OUTPUT_FILE="epistemic_linguistics_dump.txt"

# Eski dump dosyasını tamamen boşalt (Sıfır Entropi)
> "$OUTPUT_FILE"

echo "[SİSTEM] Mac BSD Uyumlu Kod Tabanı Konsolidasyonu Başlatılıyor..."

# 1. DOSYA LİSTELEME FONKSİYONU
# Sadece bulunulan dizin (root), ./linguistics ve ./tests/linguistics altındaki dosyaları hedefler.
# Kök dizindeki ve ./tests altındaki diğer klasörleri tamamen izole eder.
generate_file_list() {
    {
        # 1. Bulunulan dizindeki (root) dosyalar (Derinlik sınırlandırıldı)
        find . -maxdepth 1 -type f -not -name ".DS_Store" -not -name "*.pyc" -not -name "*.png" -not -name "$OUTPUT_FILE"

        # 2. ./linguistics dizini altındaki dosyalar
        if [ -d "./linguistics" ]; then
            find ./linguistics -type d \( -name ".git" -o -name "venv" -o -name "env" -o -name "__pycache__" \) -prune -o \
                 -type f -not -name ".DS_Store" -not -name "*.pyc" -not -name "*.png" -not -name "$OUTPUT_FILE" -print
        fi

        # 3. ./tests/linguistics dizini altındaki dosyalar
        if [ -d "./tests/linguistics" ]; then
            find ./tests/linguistics -type d \( -name ".git" -o -name "venv" -o -name "env" -o -name "__pycache__" \) -prune -o \
                 -type f -not -name ".DS_Store" -not -name "*.pyc" -not -name "*.png" -not -name "$OUTPUT_FILE" -print
        fi
    } | sort
}

# 1. PROJE AĞACI (Klasörleri budayarak hızlı arama)
echo "==================================================" >> "$OUTPUT_FILE"
echo "PROJE AĞACI (PROJECT TREE)" >> "$OUTPUT_FILE"
echo "==================================================" >> "$OUTPUT_FILE"

generate_file_list >> "$OUTPUT_FILE"

echo -e "\n\n" >> "$OUTPUT_FILE"

# 2. KAYNAK KODLARIN ÇIKARTILMASI
echo "[SİSTEM] Kaynak kodlar ve JSON verileri çıkarılıyor..."

generate_file_list | while read -r file; do
    # Uzantı kontrolü: Sadece belirlenen uzantılara sahip dosyaları işle
    case "$file" in
        *.py|*.json|*.md|*.txt)
            echo ">> Derleniyor: $file"
            echo "==================================================" >> "$OUTPUT_FILE"
            echo "DOSYA: $file" >> "$OUTPUT_FILE"
            echo "==================================================" >> "$OUTPUT_FILE"
            cat "$file" >> "$OUTPUT_FILE"
            echo -e "\n\n" >> "$OUTPUT_FILE"
            ;;
        *)
            # Belirlenen uzantılar dışındakileri filtrele
            ;;
    esac
done

echo "[BAŞARILI] Konsolidasyon sıfır entropi ile tamamlandı. Çıktı: $OUTPUT_FILE"