import os
import sys
from pathlib import Path
from typing import List

# Kök dizini PYTHONPATH'e ekleyerek modül çözünürlüğü (Module Resolution) güvenceye alınır.
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from utils.literate_weaver import DarsiNizamiWeaver

class ComputableBookCompiler:
    """
    Epistemic Framework içerisindeki AST düğümlerinde yer alan felsefi şerhleri
    (Literate Programming tag'leri) derleyerek, statik bir PDF/HTML dokümantasyon
    uzayına (Quarto/Sphinx) hazırlayan hiyerarşik orkestratör (Orchestrator).
    Bilişsel yük matrisini korumak için dizin (Index) topolojisini otonom olarak inşa eder.
    """
    
    def __init__(self, target_directories: List[str], output_dir: str):
        self.target_directories = [project_root / d for d in target_directories]
        self.output_dir = project_root / output_dir
        self.index_file = self.output_dir / "index.md"
        self._ensure_output_environment()

    def _ensure_output_environment(self):
        """
        Derleme öncesi I/O bariyerlerini ve namespace dizinini hazırlar.
        """
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
        for target in self.target_directories:
            if not target.exists():
                print(f"[UNKNOWN_VARIABLE] Hedef derleme dizini bulunamadı: {target}")

    def run_compiler_pipeline(self):
        """
        Tangle ve Weave süreçlerini yürüten ana event loop.
        Dizinleri tarar, her bir Python dosyasındaki epistemik düğümleri çeker
        ve hiyerarşik Markdown parçalarına (chunks) dönüştürür.
        """
        compiled_files = []
        
        for directory in self.target_directories:
            if not directory.exists():
                continue
                
            for py_file in directory.rglob("*.py"):
                # `__init__.py` ve test dosyaları epistemik matrisin dışında tutulur
                if py_file.name.startswith("__") or "test_" in py_file.name:
                    continue
                    
                weaver = DarsiNizamiWeaver(str(py_file))
                
                # Z3 SMT veya felsefi kısıt tag'i bulunmayan dosyalar sessizce atlanır (Noise Reduction)
                if not weaver.extract_chunks():
                    continue
                    
                output_path = weaver.export(str(self.output_dir))
                compiled_files.append((py_file.relative_to(project_root), output_path.name))
                
        self._generate_master_index(compiled_files)

    def _generate_master_index(self, compiled_files: List[tuple]):
        """
        Derlenen bağımsız markdown (.md) dosyalarını birbirine bağlayan
        (Hyperlinked) ana ontolojik fihristi oluşturur.
        Bu fihrist, Quarto `_quarto.yml` veya Sphinx `index.rst` için referans noktasıdır.
        """
        index_content = [
            "# 📘 Dars-i Nizâmî: Hesaplanabilir Gramer Kitabı (Computable Grammar)",
            "\n*Bu doküman, Literate Programming paradigması ile Epistemic Framework kaynak kodlarından (AST) otonom olarak üretilmiştir.*\n",
            "## Ontolojik ve Sentaktik Fihrist\n"
        ]
        
        # Modül bazlı gruplama (Örn: linguistics, core, schools)
        grouped_files = {}
        for original_path, woven_name in compiled_files:
            module_name = original_path.parts[0]
            if module_name not in grouped_files:
                grouped_files[module_name] = []
            grouped_files[module_name].append((original_path, woven_name))
            
        for module, files in sorted(grouped_files.items()):
            index_content.append(f"### 🗃️ {module.capitalize()} Modülü")
            for orig_path, woven_name in sorted(files):
                index_content.append(f"- [{orig_path.name}](./{woven_name})")
            index_content.append("")
            
        with open(self.index_file, "w", encoding="utf-8") as f:
            f.write("\n".join(index_content))

if __name__ == "__main__":
    # Sistemin epistemolojik yoğunluğunun en yüksek olduğu çekirdek dizinler.
    # Bilişsel yükü düşük tutmak adına sadece bu modüller derlemeye tabi tutulur.
    TARGET_DIRS = ["linguistics", "core", "schools"]
    OUTPUT_DOCS_DIR = "docs/computable_book"
    
    compiler = ComputableBookCompiler(target_directories=TARGET_DIRS, output_dir=OUTPUT_DOCS_DIR)
    compiler.run_compiler_pipeline()