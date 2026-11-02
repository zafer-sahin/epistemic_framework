import ast
import textwrap
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path

@dataclass
class EpistemicChunk:
    """
    Dars-i Nizâmî ontolojisinde 'Metin' (deterministik kod) ile 'Şerh/Hâşiye' 
    (felsefi ve pedagojik anlatı) katmanlarının eşzamanlı taşındığı atomik veri yapısı.
    Bilişsel yükü (cognitive load) izole etmek adına her bir AST düğümü 
    bu bağımsız chunk'lar (parçalar) halinde kapsüllenir.
    """
    node_name: str
    node_type: str
    source_code: str
    pedagojik_anlati: str = ""
    felsefe_notu: str = ""
    mantik_kurali: str = ""
    satir_numarasi: int = 0

class EpistemicASTVisitor(ast.NodeVisitor):
    """
    Python AST (Abstract Syntax Tree) üzerinde dolaşarak, deterministik Z3/FOL 
    komutları ile bu komutların felsefi uzantılarını (docstring etiketleri) 
    ayrıştıran (Extraction) statik analiz mekanizması.
    """
    def __init__(self, raw_source: str):
        self.raw_source = raw_source
        self.chunks: List[EpistemicChunk] = []
        self.source_lines = raw_source.splitlines()

    def _extract_source_segment(self, node: ast.AST) -> str:
        """
        AST düğümünün (Fonksiyon veya Sınıf) raw kod karşılığını,
        docstring'lerden arındırarak salt 'Metin' (deterministik kural) olarak çeker.
        """
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            return ""
        
        # Orijinal kodu satır satır al
        segment_lines = self.source_lines[node.lineno - 1 : node.end_lineno]
        
        # Eğer ilk ifade bir docstring ise, onu atlayarak salt metni elde et
        body = node.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            docstring_node = body[0]
            # Docstring'in bittiği satırı bulup kodu oradan kes
            start_idx = docstring_node.end_lineno - node.lineno + 1
            segment_lines = [segment_lines[0]] + segment_lines[start_idx:]
            
        return textwrap.dedent("\n".join(segment_lines))

    def _parse_docstring_tags(self, docstring: str) -> Dict[str, str]:
        """
        ReST (reStructuredText) benzeri pedagojik etiketleri (.. etiket::) 
        durum makinesi (state machine) yaklaşımıyla parse eder. 
        Regex yerine deterministik satır okuması kullanılarak semantik kayıplar önlenir.
        """
        tags = {
            "pedagojik_anlati": [],
            "felsefe_notu": [],
            "mantik_kurali": []
        }
        
        if not docstring:
            return {k: "" for k in tags}

        lines = textwrap.dedent(docstring).splitlines()
        current_state = None

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(".. pedagojik_anlati::"):
                current_state = "pedagojik_anlati"
                continue
            elif stripped.startswith(".. felsefe_notu::"):
                current_state = "felsefe_notu"
                continue
            elif stripped.startswith(".. mantik_kurali::"):
                current_state = "mantik_kurali"
                continue
            elif stripped.startswith(".. "):
                # Bilinmeyen bir directive, state'i sıfırla
                current_state = None
                continue

            if current_state and line:
                # İçerik satırları genellikle indentasyonludur, boşlukları koru
                tags[current_state].append(line.lstrip())

        return {k: "\n".join(v).strip() for k, v in tags.items()}

    def _process_node(self, node: ast.AST, node_name: str, node_type: str):
        docstring = ast.get_docstring(node)
        if not docstring:
            return # Yalnızca şerh (docstring) barındıran epistemik düğümler dokunur

        tags = self._parse_docstring_tags(docstring)
        
        # Eğer yapılandırılmış tag'lerden hiçbiri yoksa bu standart bir fonksiyondur, atla
        if not any(tags.values()):
            return

        source_code = self._extract_source_segment(node)

        chunk = EpistemicChunk(
            node_name=node_name,
            node_type=node_type,
            source_code=source_code,
            pedagojik_anlati=tags.get("pedagojik_anlati", ""),
            felsefe_notu=tags.get("felsefe_notu", ""),
            mantik_kurali=tags.get("mantik_kurali", ""),
            satir_numarasi=node.lineno
        )
        self.chunks.append(chunk)

    def visit_ClassDef(self, node: ast.ClassDef):
        self._process_node(node, node.name, "Class")
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._process_node(node, node.name, "Function")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._process_node(node, node.name, "AsyncFunction")
        self.generic_visit(node)


class DarsiNizamiWeaver:
    """
    Literate Programming prensipleri uyarınca (Tangle/Weave), AST'den çıkarılan
    deterministik kod bloklarını (Metin) ve felsefi docstring'leri (Şerh)
    akademik formata (LaTeX entegreli Markdown) dokuyan (Weaving) motor.
    """
    
    def __init__(self, target_filepath: str):
        self.target_filepath = Path(target_filepath)
        if not self.target_filepath.exists():
            raise FileNotFoundError(f"[UNKNOWN_VARIABLE] Kaynak dosya bulunamadı: {target_filepath}")

        with open(self.target_filepath, 'r', encoding='utf-8') as f:
            self.raw_source = f.read()

        self.visitor = EpistemicASTVisitor(self.raw_source)
        self.ast_tree = ast.parse(self.raw_source, filename=self.target_filepath.name)

    def extract_chunks(self) -> List[EpistemicChunk]:
        """
        AST ağacını dolaşır ve epistemolojik yük barındıran düğümleri çıkarır.
        """
        self.visitor.visit(self.ast_tree)
        # Satır numarasına göre kronolojik sıralama, pedagojik akış (narrative flow) için zorunludur.
        self.visitor.chunks.sort(key=lambda x: x.satir_numarasi)
        return self.visitor.chunks

    def weave_to_markdown(self) -> str:
        """
        Semantik entropiyi engellemek ve bilişsel yükü düşürmek için hiyerarşik 
        okuma (Chunking) matrisi üretir. 
        Çıktı, LaTeX render motorları (örn: Quarto, Sphinx) tarafından derlenmeye hazırdır.
        """
        chunks = self.extract_chunks()
        
        if not chunks:
            return f"**Uyarı:** `{self.target_filepath.name}` içerisinde epistemik dokuma etiketleri bulunamadı.\n"

        woven_doc = []
        woven_doc.append(f"# Epistemolojik Çıkarım Matrisi: `{self.target_filepath.name}`\n")
        woven_doc.append("*Dars-i Nizâmî Otonom Şerh Motoru tarafından derlenmiştir.*\n\n---\n")

        for chunk in chunks:
            woven_doc.append(f"## {chunk.node_type}: `{chunk.node_name}`\n")
            
            if chunk.pedagojik_anlati:
                woven_doc.append("### 📖 Şerh (Pedagojik Anlatı)")
                woven_doc.append(f"{chunk.pedagojik_anlati}\n")
                
            if chunk.mantik_kurali:
                woven_doc.append("### ➗ Kadiyye (Mantıksal/FOL İzdüşüm)")
                # LaTeX FOL formüllerini güvenceye al
                woven_doc.append(f"{chunk.mantik_kurali}\n")
                
            if chunk.felsefe_notu:
                woven_doc.append("### 🏛️ Hâşiye (Ontolojik/Felsefi Kısıtlar)")
                woven_doc.append(f"> {chunk.felsefe_notu}\n")
                
            woven_doc.append("### ⚙️ Metin (Deterministik Çekirdek)")
            woven_doc.append("```python")
            woven_doc.append(chunk.source_code)
            woven_doc.append("```\n")
            woven_doc.append("---\n")

        return "\n".join(woven_doc)

    def export(self, output_dir: str):
        """
        Dokunan metni, belirlenen dizine .md dosyası olarak kaydeder.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        
        md_content = self.weave_to_markdown()
        output_file = out_path / f"{self.target_filepath.stem}_woven.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        return output_file