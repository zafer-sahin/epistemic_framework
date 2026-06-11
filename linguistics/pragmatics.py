from typing import List, Dict, Any, Tuple
from linguistics.discourse_state import DiscourseRegister, DenialLevel

"""
.. felsefe_notu:: İlm-i Ma'ânî ve Hakikatin Psikolojik Düzlemi
    Klasik İslâm Dilbiliminde (özellikle Sa'deddin et-Taftazânî'nin 'Mutavvel' şerhinde 
    sistematize edildiği üzere) 'İlm-i Ma'ânî (Semantik/Pragmatik), lafızların salt sözlük 
    anlamlarıyla (Lügat) değil, önermenin "Muktazâ el-Hâl"e, yani bağlamın ve muhatabın 
    (Sâil) psikolojik inkâr durumunun gerekliliğine uygunluğuyla ilgilenir. 
    
    Deterministik Z3 SMT çözücüsü her girdiyi Boolean mantığında "True/False" olarak 
    işlemeye çalışır; oysa dilde mantıksal bir doğruluk/yanlışlık değeri taşımayan 
    "İnşâî" (Emir, Soru, Temenni) yapılar vardır. Bu modül, sentaks ağaçlarını (AST) 
    Kripke uzayına inmeden önce felsefi bir filtreden geçirerek, sadece ontolojik 
    hakikat iddiası taşıyan "Haberî" (Khabari) önermelerin hesaplanmasına izin verir 
    veya İnşâî yapıları Modal/Deontik operatörlere dönüştürür.
"""

class MuktazaHalAnalyzer:
    """
    .. pedagojik_anlati:: Muktazâ el-Hâl (Entropi ve Tevkîd Uyumu)
    Âdâb-ı Bahs (Münazara Kuralları) uyarınca muhatabın şüphe seviyesi (Denial Level) ile 
    cümlenin yapısal pekiştirmesi (Tevkîd katsayısı) matematiksel olarak dengelenmelidir.
    Bu sınıf, bağlam-duyarlı (context-aware) bir hakem olarak çalışır ve "Gereksiz 
    Zorunluluk" (Unnecessary Necessity) atamalarını SMT'ye ulaşmadan engeller.
    """
    def __init__(self, discourse: DiscourseRegister):
        self.discourse = discourse

    def evaluate_balance(self, dependencies: List[Tuple[str, str, str, str]]) -> Dict[str, Any]:
        """
        .. mantik_kurali:: Denge Denklemi (Balance Equation)
        Eğer muhatabın zihni boşsa (Khali_al_Zihn), tevkîd (pekiştirme) kullanmak retorik 
        bir israftır (Fazlalık). Z3 SMT'de bu israf, gereksiz z3.ForAll kapsüllerine yol açar.
        Eğer muhatap kesin inkâr (Munkir) durumundaysa, cümleyi pekiştirmeden kurmak hakikatin 
        savunulmasında acziyettir. Sistem bu dengesizlikleri otonom olarak reddeder.
        """
        tevkid_count = sum(1 for _, _, rel, _ in dependencies if rel == 'Tevkid_Modifier' or str(rel).startswith('Amel_Inne_'))
        
        try:
            opponent_denial_level = self.discourse.get_opponent_epistemic_state()
        except AttributeError:
            opponent_denial_level = DenialLevel.KHALI_AL_ZIHN

        if opponent_denial_level == DenialLevel.KHALI_AL_ZIHN and tevkid_count > 0:
            return {
                "is_valid": False,
                "type": "MAANI_VIOLATION",
                "message": "[ADAB_WARNING] Muktazâ el-Hâl İhlali: Muhatabın zihni boş (Khali_al_Zihn) iken tevkîd (pekiştirme) kullanılamaz. Z3 Kripke uzayına gereksiz Zorunluluk (Necessity) matrisi basmak Kombinatoryal Patlamaya yol açar."
            }
            
        if opponent_denial_level == DenialLevel.MUNKIR and tevkid_count == 0:
            return {
                "is_valid": False,
                "type": "MAANI_VIOLATION",
                "message": "[ADAB_WARNING] Muktazâ el-Hâl İhlali: Muhatap kesin inkar (Munkir) makamında iken tevkîd (pekiştirme) terk edilemez. Önerme, epistemik zorunluluk taşımadığı için geçersiz kılınmıştır."
            }
            
        return {}


class MaaniSpeechActAnalyzer:
    """
    .. pedagojik_anlati:: Söz Edimi (Speech Act) ve Abdülkâhir el-Cürcânî'nin Nazm Teorisi
    Bu sınıf, cümlenin formunu (vurgu/tevkîd) muhatabın epistemik inkâr derecesiyle 
    (Denial Level) çapraz denetler. SMT motoruna salt bir veri akışı sağlamak yerine, 
    cümledeki Kasr (Kısıtlama) ve İstifham (Soru) gibi yapıları Cürcânî'nin 'Nazm' 
    (Sentaktik-Semantik Örgü) teorisine uygun olarak Modal Mantık (Deontik ve Epistemik) 
    operatörlerine dönüştürür.
    
    [FAZ 3.2 VAZ' VE MA'ÂNÎ ENTEGRASYONU]: İlm-i Ma'ânî kısıtları atomize edilmiş, 
    MuktazaHalAnalyzer izole edilmiş ve İstifham-ı İnkârî yapıları mantıksal ret (z3.Not)
    kapsüllerine dönüştürülecek şekilde yapılandırılmıştır.
    """
    def __init__(self, discourse: DiscourseRegister):
        self.discourse = discourse
        self.muktaza_analyzer = MuktazaHalAnalyzer(discourse)
        
        # .. mantik_kurali:: İnşâî Önermeler (Performatives)
        # Soru (İstifham) ve Emir (Talep) cümleleri diş dünyayı (A'yân) tasvir etmezler, 
        # dolayısıyla Kadiyye (Önerme) sayılmazlar ve SMT'nin SAT/UNSAT kararına doğrudan tabi tutulamazlar.
        self.inshai_markers = {
            "question": ["hal", "a", "mata", "kayfa", "man", "ma", "eyne"],
            "imperative": ["if'al", "la_taf'al", "ef'al", "li_yaf'al"]
        }
        self.nefy_markers = {"illa", "la", "ma", "lam", "lan"}
        
        # .. mantik_kurali:: Hasr ve Monadlar
        # Yüklemi özneye mutlak surette hapseden evrensel dışlama (Universal Exclusion) operatörleri.
        self.kasr_markers = {"innema", "illa"}

    def _evaluate_istifham(self, first_token: str, has_nefy: bool) -> Dict[str, Any]:
        """
        .. pedagojik_anlati:: İstifham-ı İnkârî ve Varoluşsal Red (Existential Negation)
        Gerçek soru cümleleri (İstifham-ı Hakikî) mantıksal değer (True/False) taşımaz. 
        Ancak, eğer soru bir nefy (olumsuzluk) edatıyla geliyorsa ("Allah'tan başka ilah mı var?"),
        bu retorik bir söz edimi olan 'İstifham-ı İnkârî'dir. İlm-i Ma'ânî gereği bu yapı, 
        soru formunda görünse de Z3 matrisinde kesin bir varoluşsal redde veya evrensel 
        olumsuzlamaya dönüştürülmelidir.
        
        FOL Denklemi: $\\neg \\exists x (P(x))$ veya $\\forall x \\neg P(x)$
        """
        if first_token in self.inshai_markers["question"]:
            if has_nefy:
                return {
                    "is_valid": True, 
                    "type": "Istifham_i_Inkari", 
                    "z3_operator_hint": "Universal_Negation", 
                    "message": "İstifham-ı İnkârî tespit edildi. Evrensel/Varoluşsal ret mantığına (z3.Not) dönüştürülecek."
                }
            else:
                return {
                    "is_valid": False, 
                    "type": "Istifham_Hakiki", 
                    "message": "Gerçek soru cümleleri (İstifham-ı Hakikî) mantıksal değer taşımaz."
                }
        return {}

    def _evaluate_deontic(self, first_token: str) -> Dict[str, Any]:
        """
        .. mantik_kurali:: Deontik Mantık (Emir ve Nehiy)
        Emir (Yap) ve Nehiy (Yapma) kipleri mevcut Kripke dünyasını ($W_0$) tasvir etmezler. 
        Onlar, ahlaki veya hukuki (Fıkhî) olarak erişilebilir (accessible) ideal dünyalarda 
        ($W_1$) geçerli olması gereken kuralları mühürlerler.
        
        Matematiksel Karşılığı: 
        $O(P)$ -> Obligatory (Wajib_Fiqh)
        $F(P)$ -> Forbidden (Haram_Fiqh)
        """
        if first_token in self.inshai_markers["imperative"]:
            is_prohibitive = first_token.startswith("la_")
            return {"is_valid": True, "type": "Deontic", "operator": "Nehiy" if is_prohibitive else "Emir"}
        return {}

    def _extract_kasr_and_ihtisas(self, dependencies: List[Tuple[str, str, str, str]]) -> Dict[str, Any]:
        """
        .. felsefe_notu:: Kasr, İhtisas ve Evrensel Dışlama
        Klasik Arapçada sentaktik dizilimin (Takdim/Te'hir) bozulması veya Kasr edatlarının 
        kullanımı, eylemi belirli bir varlığa mülk kılar. 
        Örn: (İyyâke Na'budu - Yalnız sana ibadet ederiz). 
        
        Z3 FOL matrisinde bu durum, sıradan bir varoluşsal beyandan ($\\exists x$), 
        çift yönlü gerektirmeli (Biconditional) bir evrensel dışlama fonksiyonuna yükseltilir:
        $$\\forall x (\\text{Action}(x) \\iff \\text{Target}(x))$$
        
        Yönün (Sıfat'tan Mevsuf'a veya tersi) yanlış tespiti, ontolojide fatal hatalara (Semantic Shift) yol açar.
        """
        kasr_data = None
        
        ihtisas_deps = [dep for dep in dependencies if dep[2] == 'Rel_Ihtisas']
        if ihtisas_deps:
            amil = ihtisas_deps[0][0]
            mamul = ihtisas_deps[0][1]
            kasr_data = {
                "kasr_type": "Takdim_Ihtisas",
                "kasr_target": mamul,
                "kasr_predicate": amil,
                "kasr_direction": "Sifat_to_Mevsuf", 
                "message": f"Takdim (İhtisas) tespit edildi. Eylem ({amil}) sadece hedefe ({mamul}) kısıtlanacak."
            }
        
        if not kasr_data:
            kasr_deps = [dep for dep in dependencies if dep[2] == 'Kasr_Modifier']
            if kasr_deps:
                hedef_kelime = kasr_deps[0][0]
                edat = kasr_deps[0][1].lower()
                kasr_yonu = kasr_deps[0][3]
                
                kasr_data = {
                    "kasr_type": f"Kasr_{edat.capitalize()}",
                    "kasr_target": hedef_kelime,
                    "kasr_direction": kasr_yonu,
                    "message": f"'{edat}' edatı ile yönlü Kasr ({kasr_yonu}) tespit edildi. Evrensel dışlama (Universal Exclusion) yönlü uygulanacak."
                }
        
        return kasr_data

    def analyze_pragmatics(self, tokens: List[str], dependencies: List[Tuple[str, str, str, str]]) -> Dict[str, Any]:
        """
        .. pedagojik_anlati:: İlm-i Ma'ânî Orkestrasyonu
        Soyut Sentaks Ağacını (AST) baştan sona tarayarak cümlenin ontolojik meşruiyetini 
        tescil eden ana hakemdir. Eğer cümle Haberî (Khabari) ise ve Muktazâ el-Hâl 
        ihlal edilmemişse Z3 çözümleyicisine geçit (pass) verilir.
        """
        if not tokens:
            return {"is_valid": False, "type": "Empty"}
        
        first_token = tokens[0].lower()
        has_nefy = any(t.lower() in self.nefy_markers for t in tokens)
        
        istifham_res = self._evaluate_istifham(first_token, has_nefy)
        if istifham_res: return istifham_res
            
        deontic_res = self._evaluate_deontic(first_token)
        if deontic_res: return deontic_res
            
        muktaza_res = self.muktaza_analyzer.evaluate_balance(dependencies)
        if muktaza_res: return muktaza_res

        kasr_data = self._extract_kasr_and_ihtisas(dependencies)

        response = {"is_valid": True, "type": "Khabari"}
        
        # .. mantik_kurali:: Tahkik ve Epistemik Zorunluluk (Epistemic Necessity)
        has_epistemic_necessity = any(str(rel).startswith('Amel_Inne_') for _, _, rel, _ in dependencies)
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
        """
        .. felsefe_notu:: Kadiyye (Önerme) Onayı
        Eğer cümle tüm İlm-i Ma'ânî testlerinden geçip 'is_valid: True' döndürürse, 
        bu söz diziminin artık mantıksal bir yalanlanma veya doğrulanma ihtimali 
        taşıdığı (Haberî) kesinleşmiştir. Yalnızca Haberî önermeler SMT'de SAT/UNSAT alabilir.
        """
        res = self.analyze_pragmatics(tokens, dependencies)
        return res["is_valid"]

    # -------------------------------------------------------------------------
    # FAZ 14 - PRAGMATİK VE NAHİV SAĞLIK BARİYERİ (CROSS-LAYER HEALTH BARRIER)
    # -------------------------------------------------------------------------

    def enforce_pragmatic_syntax_consistency(self, pragmatics_meta: Dict[str, Any], isolated_phases: Dict[str, List[Any]]) -> None:
        """
        .. pedagojik_anlati:: Çapraz Katman Sağlık Taraması (Cross-Layer Verification)
        Nahiv (Sentaks) katmanındaki Topolojik FOL fazları ile İlm-i Ma'ânî'den (Pragmatik)
        gelen kipliklerin (Modality) birbiriyle çelişmesini engeller. Z3 motoru, 
        teolojik ve sentaktik çatışmaları aynı anda işleyemez; bu bariyer sistemin 
        tutarlılığını (Consistency) garanti altına alır.
        """
        
        # 1. Necessity vs Contingency (Tahkik vs Füzâiyye) Çatışması
        has_necessity = len(isolated_phases.get("PHASE_3_NECESSITY_SCOPE", [])) > 0
        has_dynamic_transition = len(isolated_phases.get("PHASE_5_DYNAMIC_TRANSITION", [])) > 0
        
        if has_necessity and has_dynamic_transition:
            raise ValueError(
                "[LOGIC_FAILURE_PROBABILITY: HIGH] Ontolojik Çelişki (Epistemic Collapse): "
                "'İnne' (Epistemic Necessity / Zorunluluk) ile 'Fâ-i Füzâiyye' (Dynamic Transition / Ani Geçiş) "
                "aynı Kripke uzayında eşzamanlı barınamaz. Mutlak zorunlu olan bir hakikat, "
                "anlık durum geçişine tabi tutulamaz. Z3 SMT derlemesi durduruldu."
            )
            
        # 2. İnkâr Derecesi ve Zorunluluk Uyuşmazlığı (Muktazâ el-Hâl Hard Fail)
        if pragmatics_meta.get("type") == "MAANI_VIOLATION":
            raise ValueError(
                f"[LOGIC_FAILURE_PROBABILITY: HIGH] Bağlam Zehirlenmesi (Context Poisoning): "
                f"{pragmatics_meta.get('message')} Veri akışı durduruldu."
            )
            
        # 3. Kısıtlama (Kasr) ve İşaretçi Eşitleme (Bedel) Zafiyeti
        has_kasr = "kasr_data" in pragmatics_meta
        has_bedel = len(isolated_phases.get("PHASE_2_IDENTITY_ALIAS", [])) > 0
        
        if has_kasr and has_bedel:
            pragmatics_meta["alias_warning"] = (
                "[ADAB_WARNING] Kasr (Evrensel Dışlama) ve Bedel (Pointer Aliasing) "
                "hiper-kombinasyonu tespit edildi. DiscourseRegister üzerinde kimliklerin "
                "(Identity Unification) mutlak surette eşitlendiği SMT motoruna iletilmelidir."
            )