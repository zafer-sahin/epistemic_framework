from typing import List, Dict, Any, Tuple
from linguistics.discourse_state import DiscourseRegister, DenialLevel

"""
.. felsefe_notu::
    Klasik İslâm Dilbiliminde 'İlm-i Ma'ânî (Semantik Pragmatik), kelimelerin 
    sözlük anlamlarıyla değil, cümlenin "Muktazâ el-Hâl"e (bağlamın ve muhatabın 
    psikolojik durumunun gerekliliğine) uygunluğuyla ilgilenir. Bu modül, 
    Z3 SMT çözücüsüne gidecek olan Soyut Sentaks Ağaçlarını (AST) filtreleyerek,
    mantıksal bir doğruluk/yanlışlık değeri taşımayan "İnşâî" (Emir, Soru) 
    cümlelerini eler. Sadece hakikat iddiası taşıyan "Haberî" önermelerin 
    mantık matrisine (Semantic IR) geçmesine izin verir.
"""

class MaaniSpeechActAnalyzer:
    """
    'İlm-i Ma'ânî Söz Edimi ve Muktazâ el-Hâl Analizörü.
    Faz 2 - Adım 2.3: PragmaticsFilter'ın yerine inşa edilmiştir.
    Cümlenin formunu (vurgu/tevkîd) muhatabın epistemik inkâr derecesiyle (Denial Level) çapraz denetler.
    Faz 2 - Adım 2.4: İstifham-ı İnkârî (Reddedici Soru) tespiti.
    Faz 2 - Adım 2.5: Kasr/Hasr (Kısıtlama) ve İhtisas (Takdim/Te'hir) tespiti.
    Faz 2 - Adım 2.6: Kasr Operatörlerinde Yön Yitimi Onarımı (Kasr-ı Sıfat ale'l-Mevsuf / Kasr-ı Mevsuf ale's-Sıfat).
    [FAZ 3 ENTEGRASYONU]: 'İnne ve Kardeşleri'nin Tevkîd gücü korunurken (Muktazâ el-Hâl), 
    Kripke uzayı için 'Epistemic_Necessity' (Tahkik/Yakîn) sinyali üretmesi sağlandı.
    
    [FAZ 8 LITERATE PROGRAMMING]: Bilişsel yükü aşmamak için devasa analiz döngüsü; 
    İstifham, Deontik, Muktazâ el-Hâl ve Kasr alt-fonksiyonlarına (private methods) parçalanmıştır.
    Orijinal motorun tarihsel 'Faz' kayıtları ve if/else akışları %100 korunmuştur.
    """
    def __init__(self, discourse: DiscourseRegister):
        self.discourse = discourse
        self.inshai_markers = {
            "question": ["hal", "a", "mata", "kayfa", "man", "ma", "eyne"],
            "imperative": ["if'al", "la_taf'al", "ef'al", "li_yaf'al"]
        }
        self.nefy_markers = {"illa", "la", "ma", "lam", "lan"}
        self.kasr_markers = {"innema", "illa"}

    def _evaluate_istifham(self, first_token: str, has_nefy: bool) -> Dict[str, Any]:
        """
        1. İstifham-ı İnkârî ve Normal Soru Kontrolü (Faz 2.4)
        .. pedagojik_anlati::
            Eğer soru bir nefy (olumsuzluk) edatıyla geliyorsa ("Allah'tan başka ilah mı var?"),
            bu İstifham-ı İnkârî'dir ve Z3 matrisinde varoluşsal bir redde (\\neg \\exists x) dönüşür.
        """
        if first_token in self.inshai_markers["question"]:
            if has_nefy:
                return {
                    "is_valid": True, 
                    "type": "Istifham_i_Inkari", 
                    "message": "İstifham-ı İnkârî tespit edildi. Evrensel/Varoluşsal ret mantığına dönüştürülecek."
                }
            else:
                return {
                    "is_valid": False, 
                    "type": "Istifham_Hakiki", 
                    "message": "Gerçek soru cümleleri (İstifham-ı Hakikî) mantıksal değer taşımaz."
                }
        return {}

    def _evaluate_deontic(self, first_token: str) -> Dict[str, Any]:
        """2. Deontik Mantık (Emir/Nehiy)"""
        if first_token in self.inshai_markers["imperative"]:
            is_prohibitive = first_token.startswith("la_")
            return {"is_valid": True, "type": "Deontic", "operator": "Nehiy" if is_prohibitive else "Emir"}
        return {}

    def _evaluate_muktaza_el_hal(self, dependencies: List[Tuple[str, str, str, str]]) -> Dict[str, Any]:
        """
        3. Muktazâ el-Hâl (Bağlamsal Gereklilik) Denetimi (Faz 2.3 & FAZ 3)
        .. matematiksel_model::
            Muhatabın entropisi (Denial Level) ile Tevkîd (Pekiştirme) katsayısı çapraz denetlenir.
        """
        # [FAZ 3 GÜNCELLEMESİ]: 'Amel_Inne_Ism' veya 'Amel_Inne_Haber' bağımlılıkları da güçlü bir Tevkid (Pekiştirme) sayılır.
        tevkid_count = sum(1 for _, _, rel, _ in dependencies if rel == 'Tevkid_Modifier' or rel.startswith('Amel_Inne_'))
        opponent_denial_level = self.discourse.get_opponent_epistemic_state()

        if opponent_denial_level == DenialLevel.KHALI_AL_ZIHN and tevkid_count > 0:
            return {
                "is_valid": False,
                "type": "MAANI_VIOLATION",
                "message": "[ADAB_WARNING] Muktazâ el-Hâl İhlali: Muhatabın zihni boş (Khali_al_Zihn) iken tevkîd (pekiştirme) kullanılamaz."
            }
            
        if opponent_denial_level == DenialLevel.MUNKIR and tevkid_count == 0:
            return {
                "is_valid": False,
                "type": "MAANI_VIOLATION",
                "message": "[ADAB_WARNING] Muktazâ el-Hâl İhlali: Muhatap kesin inkar (Munkir) makamında iken tevkîd (pekiştirme) terk edilemez."
            }
        return {}

    def _extract_kasr_and_ihtisas(self, dependencies: List[Tuple[str, str, str, str]]) -> Dict[str, Any]:
        """
        4. İlm-i Ma'ânî: Kasr (Hasr) ve İhtisas Tespiti (Faz 2.5 & Faz 2.6 Yönlü Matris)
        """
        kasr_data = None
        
        # A. Takdim/Te'hir İhtisası (Mefulün Faile/Fiile Takdimi)
        ihtisas_deps = [dep for dep in dependencies if dep[2] == 'Rel_Ihtisas']
        if ihtisas_deps:
            amil = ihtisas_deps[0][0]
            mamul = ihtisas_deps[0][1]
            kasr_data = {
                "kasr_type": "Takdim_Ihtisas",
                "kasr_target": mamul,
                "kasr_predicate": amil,
                "kasr_direction": "Sifat_to_Mevsuf",  # Fiil eylemi (sıfat) tamamen takdim edilen mefule (mevsuf) hasredilir.
                "message": f"Takdim (İhtisas) tespit edildi. Eylem ({amil}) sadece hedefe ({mamul}) kısıtlanacak."
            }
        
        # B. Edatlı Kasr (İnnemâ / İllâ) - Yön (Direction) Tespiti
        if not kasr_data:
            kasr_deps = [dep for dep in dependencies if dep[2] == 'Kasr_Modifier']
            if kasr_deps:
                # dep formati: (hedef_kelime, edat, 'Kasr_Modifier', kasr_yonu)
                hedef_kelime = kasr_deps[0][0]
                edat = kasr_deps[0][1].lower()
                kasr_yonu = kasr_deps[0][3] # 'Mevsuf_to_Sifat' veya 'Sifat_to_Mevsuf'
                
                kasr_data = {
                    "kasr_type": f"Kasr_{edat.capitalize()}",
                    "kasr_target": hedef_kelime,
                    "kasr_direction": kasr_yonu,
                    "message": f"'{edat}' edatı ile yönlü Kasr ({kasr_yonu}) tespit edildi. Evrensel dışlama (Universal Exclusion) yönlü uygulanacak."
                }
        
        return kasr_data

    def analyze_pragmatics(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]]) -> Dict[str, Any]:
        if not tokens:
            return {"is_valid": False, "type": "Empty"}
        
        first_token = tokens[0].lower()
        has_nefy = any(t.lower() in self.nefy_markers for t in tokens)
        
        istifham_res = self._evaluate_istifham(first_token, has_nefy)
        if istifham_res: return istifham_res
            
        deontic_res = self._evaluate_deontic(first_token)
        if deontic_res: return deontic_res
            
        muktaza_res = self._evaluate_muktaza_el_hal(dependencies)
        if muktaza_res: return muktaza_res

        kasr_data = self._extract_kasr_and_ihtisas(dependencies)

        response = {"is_valid": True, "type": "Khabari"}
        
        # [FAZ 3 ENTEGRASYONU]: Epistemic Necessity (Tahkik) Tespiti
        has_epistemic_necessity = any(rel.startswith('Amel_Inne_') for _, _, rel, _ in dependencies)
        if has_epistemic_necessity:
            response["epistemic_modality"] = "Epistemic_Necessity"
            response["message"] = "İnne ve Kardeşleri (Huruf-u Müşebbehe bil-Fiil) tespit edildi: Tahkik (Epistemic Necessity) uygulanacak."

        if kasr_data:
            response["kasr_data"] = kasr_data
            if "message" in response:
                response["message"] += f" | {kasr_data['message']}"
            else:
                response["message"] = kasr_data['message']

        return response
        
    def is_khabari(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]]) -> bool:
        res = self.analyze_pragmatics(tokens, dependencies)
        return res["is_valid"]