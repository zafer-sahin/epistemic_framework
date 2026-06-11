from typing import List, Optional, Literal, Dict
from pydantic import BaseModel
from enum import IntEnum
from core.exceptions import ContextPoisoningError

class DenialLevel(IntEnum):
    """
    .. mantik_kurali:: Muktazâ el-Hâl ve Muhatabın Epistemik Halleri
    İlm-i Ma'ânî'ye göre sözün kıymeti, kelimelerin sözlük anlamında değil, muhatabın (Sâil'in) 
    hakikate karşı takındığı psikolojik ve epistemik tavra (Muktazâ el-Hâl) uygunluğundadır.
    Bu ontolojik hiyerarşi, deterministik SMT motorunun Kripke uzayındaki hesaplamalarına 
    geçmeden önce uygulayacağı retorik filtrelerin (Tevkîd katsayısı) eşik değerlerini belirler.
    """
    KHALI_AL_ZIHN = 0  # Zihin boş, nötr durum. Tevkîd (pekiştirme) israftır ve retorik olarak yasaktır.
    MUTAREDDIT = 1     # Şüphe durumu (Men' saldırısı). Muhatabın şüphesini gidermek için Tevkîd kullanımı caiz/önerilendir (Hasan).
    MUNKIR = 2         # Kesin inkar durumu (Nakz saldırısı). Hakikatin savunulması için Tevkîd zorunludur (Vâcib).

class EntityMention(BaseModel):
    """
    .. felsefe_notu:: Lafzın Ontolojik Mühürlenmesi (Instantiation)
    Bir kelime (lafız), sadece dizgisel (string) bir değişken değil;
    Sâil veya Mucîb tarafından belirli bir usûl uzayında (Namespace) iddia edilmiş bir varlık yansımasıdır 
    (A'yân-ı Sâbite'nin cümledeki tezahürü).
    Varlıkların HPSG (Cinsiyet ve Sayı) kısıtlarıyla mühürlenmesi, mantıksal argümantasyonda (Kıyas) 
    oluşabilecek terim kaymalarını ve safsataları engeller.
    """
    word: str
    ontologic_id: str
    timestamp: int
    agent: Literal["Mujib", "Sail", "Base"]
    sealed_namespace: str  
    gender: Optional[str] = None
    number: Optional[str] = None
    is_virtual: bool = False  # [FAZ 1.4] DRT (Discourse Representation Theory) Varoluşsal Düğüm Bayrağı

class DiscourseRegister:
    """
    .. pedagojik_anlati:: Âdâb-ı Bahs, Kuvve-i Hâfıza ve Diyalektik Matris
    Bu sınıf, bir yazılım "Stack" (Yığıt) veri yapısı olmanın çok ötesinde, İbn Sînâcı 
    'Kuvve-i Hâfıza'nın ve Seyyid Şerif el-Cürcânî'nin 'Tahrîr-i Niza' (Tartışma Noktasının Yalıtımı) 
    prensibinin koda dökülmüş halidir.
    Sâil (İtiraz Eden) ve Mucîb (İddia Sahibi) aynı zihinsel sahneyi (Discourse) paylaşsalar da, 
    birbirlerinin ontolojik önkabullerini (Namespace) çalamazlar veya onlara dayanarak kendi 
    kıyaslarını kuramazlar.
    [FAZ 4.1 GÜNCELLEMESİ]: Sistem, tekil LIFO yığıtından arındırılarak iki farklı zihnin izole 
    edildiği (Sâil ve Mucîb matrisleri), varlıkların "Ortak Kabul" (Müsellemât/Base) seviyesinde 
    senkronize edildiği fiziksel olarak bölünmüş (Bipartite) bir Discourse Representation Theory 
    (DRT) matrisine yükseltilmiştir.
    """
    def __init__(self):
        # Yığıt (Stack) mimarisi: Kripke uzayında aktör izolasyonu
        # index 0 her zaman Global (Kök) bağlamı, yani evrensel hakikatleri ve Müsellemât'ı temsil eder.
        self.scopes: Dict[Literal["Mujib", "Sail"], List[List[EntityMention]]] = {
            "Mujib": [[]],
            "Sail": [[]]
        }
        self.clock: int = 0
        
        # .. felsefe_notu:: Arazların Cevhere Tabi Olması (HPSG Matrisi)
        # Zamirler kendi başlarına var olamazlar; ancak işaret ettikleri cevherin 
        # cinsiyet (Müzekker/Müennes) ve sayı (Müfred/Cemi/Tesniye) kısıtlarına uyarak varlık kazanırlar.
        self.pronouns = {
            "huve": {"gender": "Muzekker", "number": "Mufred"},
            "hiye": {"gender": "Muennes", "number": "Mufred"},
            "huma": {"gender": None, "number": "Tesniye"},  # Tesniye (İkil) zımnen her iki cinsiyeti de kapsar.
            "hum": {"gender": "Muzekker", "number": "Cemi"},
            "hunne": {"gender": "Muennes", "number": "Cemi"}
        }
        
        # Münazaranın kurucusu ve iddia sahibi kural gereği Mucîb'dir (Savunucu).
        self.active_agent: Literal["Mujib", "Sail"] = "Mujib" 
        
        # Epistemik başlangıç durumu: Zihinler tabula rasa (Khali al-Zihn) kabul edilir.
        self.epistemic_state: Dict[Literal["Mujib", "Sail"], DenialLevel] = {
            "Mujib": DenialLevel.KHALI_AL_ZIHN,
            "Sail": DenialLevel.KHALI_AL_ZIHN
        }

    def set_agent(self, agent: Literal["Mujib", "Sail"]) -> None:
        """
        .. mantik_kurali:: Diyalektik Nöbet Değişimi
        Tartışma (Mu'aradah) esnasında aktif zihnin sahibini belirler. SMT motoru bu andan itibaren 
        bu aktörün usûl kurallarına göre işlem yapacaktır.
        """
        self.active_agent = agent

    def update_epistemic_state(self, agent: Literal["Mujib", "Sail"], level: DenialLevel) -> None:
        """
        .. mantik_kurali:: Epistemik Geri Dönüşsüzlük (Entropy of Denial)
        Diyalektikte inkar derecesi, mantıksal bir delil (Bürhan) sunulup şüphe giderilmedikçe 
        kendi kendine geriye düşemez. Muhatap 'Munkir' olduysa, tevkîd zorunluluğu kalıcılaşır.
        """
        if level < self.epistemic_state[agent]:
            return
        self.epistemic_state[agent] = level

    def get_opponent_epistemic_state(self) -> DenialLevel:
        """
        Cümlenin retorik inşası (Muktazâ el-Hâl) için rakibin zihinsel inkar durumunu sorgular.
        """
        opponent = "Sail" if self.active_agent == "Mujib" else "Mujib"
        return self.epistemic_state[opponent]

    def set_opponent_epistemic_state(self, level: DenialLevel) -> None:
        """
        [E2E RED-TEAMING YAMASI]
        Test ortamlarında rakibin epistemik durumunu doğrudan manüple etmek (Zehirlenme Senaryosu) 
        için kullanılır. Sadece test senaryolarında çağrılmalıdır.
        """
        opponent = "Sail" if self.active_agent == "Mujib" else "Mujib"
        self.epistemic_state[opponent] = level

    def push_scope(self) -> None:
        """
        .. felsefe_notu:: Kripke Uzayında Varsayımsal Dünyalar (Possible Worlds)
        Z3.push() tetiklendiğinde veya yeni bir diyalektik argüman açıldığında (Kadiyye-i Şartiyye), 
        mutlak gerçeklikten (Frame 0) yalıtılmış yeni bir varsayımsal alt-dünya yaratılır.
        Bu yaratım sadece aktif aktörün yığıtında gerçekleşir.
        """
        self.scopes[self.active_agent].append([])

    def pop_scope(self) -> None:
        """
        .. felsefe_notu:: Dünyaların İmhası
        Z3.pop() tetiklendiğinde veya varsayımsal iddia çürütüldüğünde (Nakz), o bağlam içinde 
        yaratılmış tüm ontolojik yüklemeler imha edilir ve varlık hiyerarşisi bir önceki duruma rücu eder.
        """
        if len(self.scopes[self.active_agent]) > 1:
            self.scopes[self.active_agent].pop()
        else:
            raise RuntimeError(f"[BELLEK HATASI] {self.active_agent} için Global söylem çerçevesi (Frame 0 - Müsellemât) imha edilemez. Stack underflow.")

    def add_mention(self, word: str, ontologic_id: str, active_namespace: str, gender: Optional[str] = None, number: Optional[str] = None, is_virtual: bool = False) -> None:
        """
        Müsellemât uzayındaki kavramları her iki aktörün de kök zihnine atar; 
        hususi iddiaları ise yalnızca iddia sahibinin yığıtına mühürler.
        """
        mention_agent: Literal["Mujib", "Sail", "Base"] = "Base" if active_namespace == "Base" else self.active_agent

        mention = EntityMention(
            word=word, 
            ontologic_id=ontologic_id, 
            timestamp=self.clock,
            agent=mention_agent,
            sealed_namespace=active_namespace,
            gender=gender,
            number=number,
            is_virtual=is_virtual
        )
        
        if active_namespace == "Base":
            # Müsellemât (Ortak Kabuller) her iki zihnin de kök (Frame 0) uzayına zerk edilir.
            self.scopes["Mujib"][0].append(mention)
            self.scopes["Sail"][0].append(mention)
        else:
            # Hususi iddialar sadece iddia edenin aktif dünyasına (Kripke Scope) yazılır.
            self.scopes[self.active_agent][-1].append(mention)
            
        self.clock += 1

    def mint_virtual_entity(self, pronoun: str, active_namespace: str) -> str:
        """
        .. pedagojik_anlati:: Müstatir Zamirin Ontolojik İnşası (DRT Existential Minting)
        İlm-i Sarf tarafından tespit edilen fiil içi gizli (müstatir) zamirler, 
        Discourse Representation Theory (DRT) bağlamında "failsiz eylem olmaz" aksiyomu gereği, 
        yığıta varoluşsal bir değişken (z3.Exists) olarak zerk edilir. 
        Böylece sonraki munfasıl (açık) zamirler, bu hayali faili meşru bir merci (Antecedent) olarak görebilir.
        """
        pronoun_lower = pronoun.lower()
        if pronoun_lower not in self.pronouns:
            raise ValueError(f"[DRT HATASI] Bilinmeyen müstatir zamir tipi: {pronoun}")
            
        target_gender = self.pronouns[pronoun_lower]["gender"]
        target_number = self.pronouns[pronoun_lower]["number"]
        
        # Z3 için eşsiz (unique) varoluşsal kimlik üretimi
        virtual_id = f"Virtual_{pronoun_lower.capitalize()}_{self.clock}"
        
        self.add_mention(
            word=f"[{pronoun_lower}]", 
            ontologic_id=virtual_id, 
            active_namespace=active_namespace,
            gender=target_gender,
            number=target_number,
            is_virtual=True
        )
        return virtual_id

    def _verify_context_sealing(self, pronoun: str, resolved_mention: EntityMention, enforcement_namespace: Optional[str]) -> Literal["VALID", "PHANTOM"]:
        """
        .. mantik_kurali:: Mu'aradah İzolasyonu ve Ontolojik Zehirlenme
        Aktörlerin Kripke yığıtları fiziksel olarak bölündüğü için, bir aktörün diğer aktörün hususi varlığını 
        yanlışlıkla çözümlemesi (Phantom bypass) riski ontolojik olarak ortadan kaldırılmıştır.
        Ancak, sistem bileşenlerinden gelen kasti bir dayatma (Enforcement) varsa, 
        bu bir "Bağlam Zehirlenmesi" (Context Poisoning) teşebbüsü kabul edilerek mantıksal işlem durdurulur.
        """
        if resolved_mention.sealed_namespace == "Base":
            return "VALID"
            
        # Fiziksel izolasyon ihlal edilip kasten başka uzayın varlığı dayatılıyorsa:
        if enforcement_namespace and resolved_mention.sealed_namespace != enforcement_namespace:
            raise ContextPoisoningError(
                f"LOGIC_FAILURE_PROBABILITY: HIGH - Context Poisoning (Bağlam Zehirlenmesi) Tespit Edildi! "
                f"'{pronoun}' zamiri, '{enforcement_namespace}' uzayından işlem yapan {self.active_agent} tarafından, "
                f"'{resolved_mention.sealed_namespace}' uzayında ({resolved_mention.agent} tarafından) mühürlenmiş "
                f"'{resolved_mention.word}' varlığına bağlanmaya çalışıyor. Mu'aradah çapraz izolasyonu ihlal edildi."
            )
            
        return "VALID"

    def _check_hpsg_unification(self, resolved_mention: EntityMention, target_gender: Optional[str], target_number: Optional[str]) -> bool:
        """
        .. mantik_kurali:: Yapısal Uyum ve Özdeşlik (Unification)
        Bir zamirin işaret ettiği asıl varlık (Antecedent) ile cinsiyet (Müzekker/Müennes) 
        ve sayı (Müfred/Cemi) bakımından ontolojik uyumu (Feature Unification) denetlenir. 
        Müstatir (sanal) zamirler de bu kontrolden eksiksiz geçer. Uyum yoksa bir önceki düğüm noktasına geçilir.
        """
        if target_gender and resolved_mention.gender and target_gender != resolved_mention.gender:
            return False  # Cinsiyet uyuşmazlığı
        
        if target_number and resolved_mention.number and target_number != resolved_mention.number:
            return False  # Sayı uyuşmazlığı
            
        return True

    def resolve_pronoun(self, pronoun: str, enforcement_namespace: Optional[str] = None) -> Optional[str]:
        """
        .. pedagojik_anlati:: İrcâ-ı Zamir (Zamirin Merciine Döndürülmesi)
        Klasik felsefi metinlerdeki en büyük kriz, zamirin (Huve, Hiye) kime/neye döndüğünün (Merci) 
        belirsizliğidir.
        Bu metod, *yalnızca aktif aktörün fiziksel yığıtı* içerisinde sondan başa (LIFO - Last In First Out) ilerleyerek,
        önce HPSG yapısal doğrulaması yapar, ardından Context Sealing kontrolü uygular.
        Bulunan ilk meşru merci (gerçek veya müstatir), Z3 SMT'ye gönderilecek kesin mantıksal değişken 
        (EntitySort Variable) ataması olur.
        """
        pronoun_lower = pronoun.lower()
        if pronoun_lower not in self.pronouns:
            return None

        target_gender = self.pronouns[pronoun_lower]["gender"]
        target_number = self.pronouns[pronoun_lower]["number"]

        # Sadece diyalektik nöbeti elinde tutan aktörün matrisinde LIFO araması yapılır.
        for frame in reversed(self.scopes[self.active_agent]):
            for resolved_mention in reversed(frame):
                
                # 1. HPSG Yapısal Uyum Denetimi
                if self._check_hpsg_unification(resolved_mention, target_gender, target_number):
                    
                    # 2. Ontolojik Sızıntı (Context Poisoning) Denetimi
                    sealing_status = self._verify_context_sealing(pronoun, resolved_mention, enforcement_namespace)
                    
                    if sealing_status == "PHANTOM":
                        continue
                    
                    # İlk meşru varlık Z3 matrisi için döndürülür
                    return resolved_mention.ontologic_id
                
        raise ValueError(f"LOGIC_FAILURE_PROBABILITY: HIGH - '{pronoun}' zamiri için {self.active_agent} uzayında ontolojik kısıtları (HPSG) uyan ve erişilebilir bir referans (Antecedent) bulunamadı.")
        
    def clear_memory(self) -> None:
        """
        .. felsefe_notu:: Zihnin Sıfırlanması
        Mezhep (Usûl) profili değiştiğinde veya diyalektik oturum (Celse) sona erdiğinde, 
        tüm Kripke dünyaları ve aktörlerin epistemik durumları silinerek sistem donanımsal 
        olarak tabula rasa durumuna döndürülür.
        """
        self.scopes = {"Mujib": [[]], "Sail": [[]]}
        self.clock = 0
        self.active_agent = "Mujib"
        self.epistemic_state = {"Mujib": DenialLevel.KHALI_AL_ZIHN, "Sail": DenialLevel.KHALI_AL_ZIHN}