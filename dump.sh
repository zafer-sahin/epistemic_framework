#!/bin/bash

# Çıktı dosyasını ana dizinde yaratıyoruz
OUTPUT_FILE="epistemic_dump.txt"

# Eski dump dosyasını tamamen boşalt (Sıfır Entropi)
> "$OUTPUT_FILE"

echo "[SİSTEM] Mac BSD Uyumlu Kod Tabanı Konsolidasyonu Başlatılıyor..."

# 1. PROJE AĞACI (Klasörleri budayarak hızlı arama)
echo "==================================================" >> "$OUTPUT_FILE"
echo "PROJE AĞACI (PROJECT TREE)" >> "$OUTPUT_FILE"
echo "==================================================" >> "$OUTPUT_FILE"

find . -type d \( -name ".git" -o -name "venv" -o -name "env" -o -name "__pycache__" \) -prune -o \
       -type f -not -name ".DS_Store" -not -name "*.pyc" -not -name "*.png" -not -name "$OUTPUT_FILE" -print \
       | sort >> "$OUTPUT_FILE"

echo -e "\n\n" >> "$OUTPUT_FILE"

# 2. KAYNAK KODLARIN ÇIKARTILMASI
echo "[SİSTEM] Kaynak kodlar ve JSON verileri çıkarılıyor..."

find . -type d \( -name ".git" -o -name "venv" -o -name "env" -o -name "__pycache__" \) -prune -o \
       -type f \( -name "*.py" -o -name "*.json" -o -name "*.md" -o -name "*.txt" \) -not -name "$OUTPUT_FILE" -print \
       | sort | while read -r file; do
    
    echo ">> Derleniyor: $file"
    echo "==================================================" >> "$OUTPUT_FILE"
    echo "DOSYA: $file" >> "$OUTPUT_FILE"
    echo "==================================================" >> "$OUTPUT_FILE"
    cat "$file" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"
    
done

echo "[BAŞARILI] Konsolidasyon sıfır entropi ile tamamlandı. Çıktı: $OUTPUT_FILE"