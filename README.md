# Epistemic Framework (N-Tier İslâm Mantık ve Dilbilim Motoru) - Kapsamlı Sistem Mimarisi ve Proje Raporu

Bu belge, tüm paydaşlar için sistemin felsefesini, mimarisini ve gelecek vizyonunu barındıran temel bir araştırma ve referans raporuna dönüşmek zorundadır. Bu belge, Aristotelesçi ve İbn Sînâcı mantık geleneğini, klasik Arapça dilbilimi disiplinlerini ('İlm-i Sarf, 'İlm-i Nahiv, 'İlm-i Vaz' ve 'İlm-i Ma'ânî) ve İslâm kelâm/usûl ekollerinin diyalektik kurallarını modern Satisfiability Modulo Theories (SMT) tabanlı Z3 çözücüleriyle entegre eden "Epistemic Framework" projesi için hazırlanmış ana mimari ve entegrasyon raporudur.

Söz konusu rapor, yapılandırılmamış doğal dil argümanlarını alarak deterministik Birinci Dereceden Mantık (FOL) matrislerine indirgeyen bu otonom sistemin başarıyla uygulanan mevcut yeteneklerini (A Safhası) ve geliştirilmekte olan gelecek vizyonunu (B Safhası) detaylandırmaktadır. Sistem, iş stratejisi belirleyen yöneticiler (Business), sistemi test eden akademisyen veya araştırmacılar (End-User) ve çekirdek mimariyi genişleten mühendisler (Developer) olmak üzere üç temel paydaşın perspektifini aynı potada eriterek tam kapsamlı bir kılavuz sunmayı hedeflemektedir. Projenin nihai vizyonu, teolojik, felsefi ve hukuki hakikat iddialarını çok katmanlı (N-Tier) bir yönlü asiklik çizge (DAG) üzerinden geçirerek, Eş'arî, Selefî veya Mâtürîdî gibi farklı usûl profillerinin kendi içsel tutarlılıklarına göre, matematiksel bir kesinlikle değerlendirilmesidir.

## İş ve Strateji Perspektifi: Pazar Konumlandırması ve Değer Önermesi

Modern yazılım dünyasında, bir projenin teknik yetkinliği kadar, iş dünyası ve son kullanıcı için yarattığı değerin de şeffaf bir biçimde tanımlanması elzemdir. Kurumsal entegratörler, iş analistleri ve teknoloji yatırımcıları, sistemin hangi problemi çözdüğünü ve mevcut teknolojilere kıyasla nasıl bir üstünlük sağladığını anlamaya ihtiyaç duyarlar. Epistemic Framework, yalnızca akademik bir yapay zekâ denemesi değil; semantik kesinliğin ve mantıksal determinizmin hayati önem taşıdığı endüstriler için tasarlanmış yüksek katma değerli bir "Bilişsel Hakem" (Cognitive Arbiter) ürünüdür.

Günümüzde Büyük Dil Modelleri (LLM), muazzam veri setleri üzerinden istatistiksel olasılıklara dayanarak metin üretmektedir. Ancak bu üretim mekanizması, istatistiksel ağırlıklara dayandığı için "halüsinasyon" adı verilen epistemolojik sapmalara ve mantıksal tutarsızlıklara son derece açıktır. Felsefi, hukuki (fıkhî) veya teolojik argümantasyonlarda ise istatistiksel bir yaklaşım kabul edilemez; burada aranan şey istatistiksel olasılık değil, ontolojik ve mantıksal kesinliktir. Epistemic Framework, makine öğrenimi modellerinin bu zaafiyetini, %100 deterministik çalışan Z3 SMT çözücüsü ile aşmaktadır. Sistem, dili istatistiksel bir vektör olarak değil, kesin kuralları olan ontolojik bir matris olarak işler.

Bu bağlamda projenin kurumsal değer üretebileceği üç ana sektör ve kullanım senaryosu bulunmaktadır. Birincisi, Eğitim Teknolojileri (EdTech) ve İlahiyat Akademileridir. Klasik mantık ve münazara (Âdâb-ı Bahs) eğitimi alan öğrencilerin, kurdukları felsefi veya teolojik argümanların mantıksal lüzum bağını (geçerliliğini) ve ontolojik tutarlılığını test edebilecekleri otonom, tarafsız ve matematiksel bir simülasyon ortamı sağlanmaktadır. İkincisi, Hukuk ve Fetva Otomasyon Sistemleridir. Çoklu ekol (örneğin Eş'arî, Selefî, Mâtürîdî veya farklı fıkhî mezhepler) kurallarına göre yayınlanan bir metnin, kurumun kendi benimsediği usûl prensipleriyle çelişip çelişmediğinin (Consistency Checking) otonom olarak denetlenmesi kurumsal itibar ve doğruluk açısından kritik bir değerdir. Üçüncüsü ise Açıklanabilir Yapay Zekâ (XAI) ve Bilişsel Bilimler araştırmalarıdır. Doğal dilin, hiçbir kayba uğramadan semantik ara temsillere (Semantic IR) dönüştürülüp matematiksel teorem ispatlayıcılarla sınanması, kara kutu (black-box) yapay zekâ modellerine karşı şeffaf ve adım adım izlenebilir bir metodoloji sunmaktadır.

Sistemin iş dünyasına sunduğu en büyük mimari yenilik "Polimorfik Ontoloji" (Sharding) stratejisidir. Kurumsal yapılar veya B2B (Business-to-Business) entegratörler, kendi sistemlerini kurarken tek bir evrensel doğrudan ziyade, kendi alanlarına özgü (Domain Specific) kuralları sisteme entegre etmek isterler. Epistemic Framework, tekil bir hakikat dayatmak yerine, farklı usûllerin kendi ontolojik gerçekliklerini izole isim alanlarında (Namespace) korumasına olanak tanıyan bir altyapı sunar. Örneğin, bir kurum Mâtürîdî profilini seçtiğinde, sistem L2 (Rule Engine) katmanında "Tekvin" düğümünün te'vil edilmesini özel bir Alan Adı Spesifik Dil (DSL) kuralı ile yasaklarken; Selefî profilini kullanan başka bir kurum için hiçbir kelimenin te'vil edilmesine izin vermeyen katı bir literalizm kısıtı (`allow_tevil=False`) uygular. Bu esneklik, projenin farklı organizasyonların kendi "Aksiyom Uzaylarını" yaratabilmelerine olanak tanıyan, ticari ölçeklenebilirliği yüksek bir altyapı olmasını sağlamaktadır.

Aşağıdaki tablo, Epistemic Framework'ün iş paydaşları için sunduğu temel değer önermelerini ve pazar farklılaşmasını özetlemektedir:


|                                    |                                                                                          |                                                                                                  |
| ---------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| **İş Gereksinimi (Business Need)** | **LLM/İstatistiksel Yaklaşım**                                                           | **Epistemic Framework (Z3 SMT) Çözümü**                                                          |
| **Mantıksal Kesinlik**             | Olasılığa dayalı metin üretimi, halüsinasyon riski yüksektir.                            | %100 deterministik, Birinci Dereceden Mantık (FOL) ispatı.                                       |
| **Kural Tabanlı Otonomi**          | Prompt mühendisliği ile yönlendirilmeye çalışılır, esnektir ancak kuralları esnetebilir. | L2 Rule Engine üzerinden mezhebe/kuruma özel katı DSL kısıtlamaları uygulanır.                   |
| **Açıklanabilirlik (XAI)**         | Kara kutu (Black-box); sonucun neden üretildiği geriye dönük izlenemez.                  | Çelişki (UNSAT) durumunda, hatanın ontolojik kökü `unsat_core` ile şeffafça raporlanır.          |
| **Çoklu Gerçeklik İzolasyonu**     | Sistem, eğitildiği verinin genel ortalamasına (bias) göre tek bir yanıt üretir.          | Polimorfik isim alanları ile birbirine zıt iki hakikat uzayı aynı motor içinde izole edilebilir. |


## Son Kullanıcı Perspektifi: Etkileşim ve Sistem Kullanımı

Son kullanıcılar, yani sistemin gücünden faydalanacak olan araştırmacılar, mantık öğrencileri veya veri analistleri, arka planda çalışan derin matematiksel mimariyle doğrudan kod seviyesinde uğraşmak istemezler. Profesyonel bir dökümantasyonun gerekliliği olarak, son kullanıcının sistemle nasıl etkileşime gireceğinin, hangi komutları kullanarak hangi çıktıları elde edeceğinin net bir biçimde anlatılması şarttır. Epistemic Framework, son kullanıcılara bu soyutlamayı sağlamak amacıyla, terminal üzerinden çalışan interaktif bir diyalektik kabuk (REPL - Read-Eval-Print Loop) sunmaktadır.

Kullanıcılar, bu izole edilmiş simülasyon ortamında doğal dilde (Arapça transliterasyon kullanılarak) argümanlarını sisteme girebilir, analiz etmek istedikleri mezhep usûlünü dinamik olarak değiştirebilir ve sistemin verdiği ontolojik veya mantıksal kararları saniyeler içinde görebilirler. Sistemin temel felsefesinde, kullanıcıya sadece "Doğru" veya "Yanlış" demek yerine, bu sonucun hangi ontolojik mesafe hesabından veya hangi ekolün kısıtlamasından kaynaklandığını şeffaf bir gerekçelendirmeyle (L2 Otorite Kararı) açıklamak yatmaktadır.

Sisteme giriş yapıldığında, motor varsayılan olarak `AshariUsul` (Eş'arî Ekolü) rejiminde ve sıfır entropi durumunda başlatılır. Kullanıcının emrinde olan temel REPL komut seti oldukça sadedir ancak arkasında muazzam bir hesaplama gücü barındırır. `set_usul <profil_adi>` komutu ile kullanıcı aktif diyalektik ekolü değiştirebilir; sistem anında "salafi", "ashari" veya "maturidi" uzaylarına geçiş yaparak eski bağlamı donanımsal olarak temizler. `parse_sentence <cümle>` komutu ise sistemin kalbidir; girilen ham metni sırasıyla Tokenizer, Sarf, Nahiv, L1, L2 ve L3 katmanlarından geçirerek mantıksal sonucunu (SAT, UNSAT veya NAKZ) hesaplar. Tartışma uzadıkça biriken zamir ve bağlam geçmişini sıfırlamak için ise `clear_memory` komutu kullanılır.

Sistemin ne kadar derin bir analiz kapasitesine sahip olduğunu somutlaştırmak adına, son kullanıcının `yadu allahi` (Allah'ın eli) gibi teolojik açıdan tarih boyunca tartışılmış, ontolojik yoğunluğu yüksek bir cümleyi sisteme girdiğini varsayalım. Sistemin vereceği tepki, kullanıcının o an hangi usûl profilini aktif ettiğine göre tamamen değişecektir.

Kullanıcı `set_usul salafi` komutuyla Selefî profilini aktif edip `parse_sentence yadu allahi` komutunu girdiğinde sistem şu adımları izler : İlk olarak dilbilim motoru "yadu" ve "allahi" kelimelerini köklerine ayırır ve aralarında İzafet (İsim Tamlaması) AST bağını kurar. Ardından L1 Ontolojik Mesafe Motoru, Porphyrios Ağacı üzerinde "Cism" (Cisim) altında yer alan "Yed" (El) ile tüm hiyerarşinin üstündeki "Wajib_al_Wujud" (Zorunlu Varlık) arasındaki ontolojik mesafeyi hesaplar. Bu mesafe 3 birimi aştığı için, L1 motoru burada lafzî bir anormallik, yani bir "Karîne-i Mânia" (mecaz ihtimali) tespit eder. Ancak cümle L2 Kural Motoruna ulaştığında, Selefî profilinin alan adı spesifik kuralları devreye girer. Selefî usûlünde `allow_tevil=False` (Sıfır-Transformasyon) kısıtı bulunduğundan, L2 motoru mecaz ihtimalini anında reddeder ve kelimeleri literal anlamlarıyla Z3 motoruna (L3) gönderir. Z3 SMT çözücüsü, bir tarafta hiçbir cismani özellik taşımaması gereken "Zorunlu Varlık" ile diğer tarafta bir cismin parçası olan "El" mefhumunu yan yana gördüğünde, sistemdeki `Yatay Dışlama (Sibling Disjointness)` aksiyomunun ihlal edildiğini matematiksel olarak kanıtlar. Kullanıcının ekranına düşen nihai çıktı: `[NAKZ] Z3 Çelişkisi kesin çürütme kabul edildi. Gerekçe: Usûl kuralları te'vili mutlak reddeder` şeklinde olur.

Aynı kullanıcı bağlamı temizleyip `set_usul maturidi` diyerek Mâtürîdî profiline geçer ve aynı cümleyi parse ederse, deneyim bambaşka bir boyuta taşınır. L1 motoru yine mecaz ihtimalini saptar, fakat bu kez L2 Kural Motoru, Mâtürîdî profilindeki `allow_tevil=True` kuralını okuyarak mecaz ihtimaline onay verir (`OVERRIDE_APPROVED`). Z3 motoru ilk aşamada yine literal anlamlar üzerinden UNSAT (çelişki) verir. Fakat sistem çöküp tartışmayı bitirmek yerine, Mâtürîdî usûlündeki `max_tevil_retries` (te'vil deneme limiti) kuralını işletir. Orkestratör, Z3'ün patladığı "Yed" düğümünü dinamik Leksikon üzerinden `Metaphor_Fallback` bağlamına (örneğin 'kudret' anlamına) çeker ve Z3 motoruna cümleyi yeniden derleyerek gönderir. İkinci denemede ontolojik çelişki ortadan kalkar. Kullanıcı terminalde şu sonucu görür: `Ontolojik Uyum Sağlandı (Te'vil uygulandı:). L2 Otorite Kararı: OVERRIDE_APPROVED`. Bu emsalsiz etkileşim tasarımı, son kullanıcılara metinlerin arkasındaki ontolojik kısıtları ve felsefi okuma farklılıklarını doğrudan bir matematiksel çıktı olarak gözlemleme imkânı sunarak, paha biçilemez bir analitik araç sağlamaktadır.

## Geliştirici Perspektifi: Çekirdek Mimari ve N-Tier Yürütme Zinciri

Geliştiriciler, mimarlar ve açık kaynak katkıcıları için Epistemic Framework, klasik Doğal Dil İşleme (NLP) ardışık düzeni ile formel SMT teoremi ispatlama süreçlerinin birbirine organik olarak bağlandığı son derece sofistike ve kısıtlayıcı bir ekosistemdir. Kod tabanının incelenmesi, projenin standart kütüphanelere dayanmak yerine kendi parse etme, semantik ağ örme ve kural işletme motorlarını sıfırdan nasıl inşa ettiğini göstermektedir. Proje dizini temel olarak dört ana modülden oluşur: Dilin yapısal analizini yapan `linguistics/`, orkestrasyonu ve ontolojik mesafe tayinini sağlayan `core/`, çoklu gerçeklik kurallarını barındıran `schools/` ve statik Porphyrios varlıklarını tutan `data/`.

Geliştiricilerin sisteme müdahale ederken anlaması gereken ilk yapı, doğal dili Z3 çözücüsünün anlayabileceği Birinci Dereceden Mantık (FOL) matrislerine dönüştüren "Dilbilim Katmanı"dır (Linguistics Pipeline). Klasik Arapça formunda gelen argümanlar, ilk olarak `linguistics/tokenizer.py` içerisindeki `EpistemicTokenizer` tarafından karşılanır. Arapça, standart Batı dillerinden farklı olarak edatların ve bağlaçların (Harf-i Cer ve Atıf harfleri) kelime gövdelerine bitişik yazıldığı (agglutinative) bir yapıya sahiptir. Örneğin "ve o dedi" anlamına gelen "waqaala" kelimesi, standart bir boşluk tabanlı bölme (whitespace tokenization) işlemine tabi tutulursa tek bir token olarak algılanır ve morfolojik analizde başarısız olur. Bu nedenle geliştirici ekip, tokenizer içerisine "Clitic Splitting" (Bitişik Edat Ayrıştırma) algoritmasını entegre etmiştir. Bu algoritma, "wa-", "fa-", "bi-", "li-", "ka-" gibi ön ekleri deterministik olarak gövdeden ayırarak kelimenin saf kök formuna ulaşılmasını garanti altına alır.

Ayrıştırılan bu kökler, sistemin en büyük mühendislik başarılarından biri olan `SarfEngine` (Üretken Morfoloji Motoru) katmanına aktarılır. Geleneksel NLP motorları genellikle devasa statik sözlükler (dictionary lookup) kullanırken, SarfEngine üretken (generative) bir yaklaşımla yapısal imza (C-V Signature) algoritması çalıştırır. Kelimedeki sesli harfler ('a', 'u', 'i') ile sessiz harfler ('C') ayrıştırılarak kelimenin kalıbı (Vezin) tespit edilir. Klasik Arapçada illetli harflerin (Vav, Ya, Elif) geçirdiği morfolojik mutasyonlara "İ'lâl", harflerin asimilasyonuna ise "İbdâl" denmektedir. SarfEngine, bu dilbilimsel fenomenleri tersine mühendislikle çözer. Örneğin "ittasala" kelimesindeki kaybolmuş 'w' (vav) harfini `Ifta'ala_Ibdal` matrisi sayesinde bularak ontolojik kökü `w-s-l` olarak mükemmel bir biçimde restore eder veya "qaala" gibi Ecvef (orta harfi illetli) bir fiili `q-w-l` olarak çözer.

Morfolojik köklerin çıkarılmasının ardından devreye giren `NahivDependencyCompiler` (Nahiv Bağımlılık Derleyicisi), Kayan Pencere (Sliding Window) algoritması kullanarak cümle içerisindeki kelimelerin hiyerarşik AST (Abstract Syntax Tree) ilişkilerini çıkarır. İzafet (isim tamlaması) veya Sıfat-Mevsuf gibi ilişkiler, kelimelerin marife (belirli) veya nekra (belirsiz) olma durumlarına göre algılanır. Elde edilen sentaktik ağaç, İslâm mantığının temel bir filtresi olan `PragmaticsFilter` ('İlm-i Ma'ânî) tarafından denetlenir. Mantıksal çıkarımlar sadece "Haberî" (doğru veya yanlışlanabilen) önermelerden yapılabileceği için, filtre "hal", "mata", "kayfa" gibi "İnşâî" (soru/emir) belirteçleri tespit ettiğinde AST'yi mantık motoruna girmeden doğrudan çöpe atar. Bu sıkı denetimden geçen AST, `IlmWadAdapter` tarafından alınarak dinamik leksikondan kelimelerin mezhepsel ontolojik ID'leri ile eşleştirilir, zamirleri `DiscourseRegister` üzerinden çözümlenir ve nihayetinde Z3 motorunun işleyeceği `SemanticStatementIR` (Semantik Ara Temsil) haline getirilir.

Aşağıdaki tablo, sistemin metni analiz ederken kullandığı dilbilimsel boru hattını ve her katmanın ürettiği değeri göstermektedir:


|                       |                                                                             |                                                                      |
| --------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **Dilbilimsel Modül** | **Teknik Yaklaşım ve Algoritma**                                            | **Çıktı ve Sağlanan Değer**                                          |
| **Tokenizer**         | Clitic Splitting (Bitişik edat koparma).                                    | "waqaala" -> ["wa", "qaala"]. Kökün bozulmasını engeller.            |
| **SarfEngine**        | C-V İmzası çıkarma, İ'lâl ve İbdâl restorasyonu.                            | Mükemmel kök (Root) ve Vezin (Pattern) tespiti.                      |
| **Nahiv Compiler**    | Kayan Pencere ile AST alt-ağaç (Sub-Tree) kurulumu.                         | Fail, Meful, İzafet gibi sentaktik bağların çıkarılması.             |
| **Pragmatics Filter** | 'İlm-i Ma'ânî İnşâî/Haberî form analizi.                                    | Mantıksız soru/emir cümlelerinin Z3'ü meşgul etmesinin engellenmesi. |
| **IlmWad Adapter**    | Dinamik Bağlamsal Leksikon (Contextual Lexicon) ve Zamir (Anafora) bağlama. | Doğal dilin `SemanticStatementIR` mantık matrisine dönüştürülmesi.   |


Dilbilim katmanından başarıyla geçen semantik matris, `EpistemicOrchestrator` tarafından devralınır ve sistemin kalbini oluşturan N-Tier (Çok Katmanlı) DAG (Yönlü Asiklik Çizge) yürütme zincirine sokulur. Bu zincir üç temel güvenlik ve doğrulama motorundan oluşur:

Birinci katman olan **L1 Heuristic Graph**, cümledeki etken (amil) ve edilgen (mamul) kelimelerin ontolojik hiyerarşideki mesafesini ölçer. Porphyrios Ağacı düzleştirilerek En Küçük Ortak Ata (Lowest Common Ancestor - LCA) algoritması koşturulur. Eğer iki varlık arasındaki ontolojik soy ağacı mesafesi çok uzaksa (örneğin mesafe > 3), L1 motoru cümlenin doğrudan hakiki bir anlama sahip olamayacağını tespit ederek bir mecaz skoru (`metaphor_probability`) hesaplar ve kelimeyi işaretler.

İkinci katman olan **L2 Rule Engine**, L1'in tespit ettiği bu mecaz veya anormallik ihtimalini, kullanıcının seçtiği mezhep (Usûl) kurallarına göre yargılayan bir Domain Specific Language (DSL) otoritesidir. L2 motoru, sonsuz te'vil döngülerini engellemek için `max_tevil_retries` kısıtını denetler, `blocked_nodes` yasaklarına (Örn: Mâtürîdî usûlünde Tekvin düğümüne dokunulamaması) uyar ve te'vile onay veya ret verir.

Üçüncü katman olan **L3 SMT Circuit Breaker**, Z3 motorunu aşırı yüklenmelerden koruyan bir yalıtım katmanıdır. Kuantum kombinasyonlarına varabilen FOL matrislerinin Z3 üzerinde tekrar tekrar derlenmesini önlemek için `_memoization_cache` kullanarak önbellekleme yapar ve Undecidability (karar verilemezlik) çöküşlerine karşı `timeout_ms=3000` limitiyle korunur. Bu üç katman, deterministik mantığın ve teolojik kuralların bilgisayar bilimlerine eşsiz bir adaptasyonudur.

## Mevcut Durum (A Safhası): İsağoci Temeli ve Statik Mantık

Projenin başarıyla tamamlanan ve "A Safhası" olarak adlandırılan bölümü, felsefe eğitiminin klasik giriş metni olan Esîrüddin el-Ebherî'nin "İsağoci" (Eisagoge) eserindeki ontolojik varlık tabanının ve Aristotelesçi kategorik mantığın kod mimarisine deterministik olarak aktarılmasıdır. İsağoci geleneği, kavramların tanımlanmasını ve varlıkların hiyerarşik olarak sınıflandırılmasını sağlayan "Beş Tümel" (el-Külliyyâtü'l-Hamse) doktrini üzerine kuruludur: Cins (Genus), Nev' (Species), Fasıl (Differentia), Hâssa (Property) ve Araz-ı Âmm (Accident).

Geliştirici ekibin `data/base_ontology.json` dosyası ve `core/models.py` içerisindeki Pydantic sınıfları üzerinde gerçekleştirdiği modelleme, İsağoci geleneğine son derece sadık ve kusursuzdur. Bir varlık tanımlanırken, ağacın en tepesindeki "Cevher" cinsinden başlanarak "Cism", "Nami", "Hayvan", "İnsan" ve "Feres" türlerine doğru dikey bir hiyerarşi (`children` listesi) ile inilmektedir. "İnsan" türünü diğer canlılardan ayıran özsel nitelik olan "Natik" (Düşünen) `differentia_id` (Fasıl) olarak; insan türüne özgü olan ancak özüne dahil olmayan "Dahik" (Gülen) vasfı `propria_ids` (Hâssa) olarak; genel dışsal nitelikler ise `accidents_ids` olarak kodlanmıştır.

`core/logic_engine.py` içerisindeki `AristotelianSolver` sınıfı, JSON formatındaki bu statik varlık ağacını Z3 SMT çözücüsünün anlayabileceği katı matematiksel kısıtlara (aksiyomlara) çevirmektedir. Hiyerarşik geçişlilik kuralı gereği, alt türler üst cinsin yüklemlerini `z3.ForAll` ve `z3.Implies` kapılarıyla kalıtım yoluyla alır. Sistemin mantıksal çelişmezlik ilkesini koruyan Yatay Dışlama (Sibling Disjointness) kuralı ise, kardeş düğümler arasında $z3.Not(z3.And(...))$ formülasyonuyla Z3 uzayına gömülmüştür. Bu durum, bir varlığın aynı anda hem İnsan hem Feres (At) olmasını matematiksel olarak imkânsız kılar.

Kıyas (Syllogism) motoru ise, Darb-ı Evvel (Barbara AAA Modülü) formundaki kategorik kıyasları işletmektedir. Dinamik olarak yerleştirilen Hadd-i Asgar, Ekber ve Evsat terimleri Z3'e sunulmakta, Z3 neticenin değili üzerinden bir çelişki (`UNSAT`) bularak argümanın lüzum bağını ispatlamaktadır. Sistemin bu statik sağlamlığı, `test_ex_falso_quodlibet_prevention` gibi Red-Teaming testlerinde Z3 motorunun çelişkili öncüllerden sonuç türetmeyi reddetmesiyle halihazırda kanıtlanmıştır.

Ancak, İsağoci ile kurulan bu muazzam temel, ileri seviye felsefi tartışmaları yürütebilecek esneklikten yoksundur. Birinci kritik darboğaz, sistemin aşırı derecede `Kadiyye-i Hamliyye` (kategorik yüklemli önermeler) bağımlısı olmasıdır; kelâm tartışmalarında hayati olan Şartlı önermeler (Kadiyye-i Şartiyye) henüz ilkel seviyededir. İkinci büyük eksiklik, zaman ve kiplik belirten Modal Mantık (Muvaccehât) kapasitesinin zayıflığıdır. Z3'ün Boolean tabanlı ikili (True/False) doğası, "Zorunlu Varlık" gibi derin kelâmî mefhumların modal ağırlığını yitirmesine sebep olmaktadır. Son olarak, söylem belleğinin tek boyutlu bir yığıt (stack) kullanması, münazaranın karşılıklı bağlamını bozmakta ve sistemi tek yönlü bir otomata indirgemektedir. Bu yapısal darboğazların aşılması için projenin B Safhası tasarlanmıştır.

## Gelecek Vizyonu ve Stratejik Mimari Yol Haritası (B Safhası)

Projenin B Safhası (Çalışılacak Konular), statik İsağoci tabanından çıkarak Necmeddin el-Kâtibî'nin "er-Risâletü'ş-Şemsiyye" eseriyle sembolize edilen önermesel karmaşıklığa ve nihayetinde Seyyid Şerif el-Cürcânî'nin "Âdâbu'l-Bahs" sistemiyle yönetilen çok-aktörlü bir diyalektik otomata evrilmesini kapsayan derin bir mimari genişlemedir. Bu entegrasyon, sistemin yapay zekâ felsefesinde yeni bir çığır açmasını sağlayacaktır. Yol haritası dört yapısal faza ayrılmıştır.

### Faz 1 & 2: Şemsiyye Entegrasyonu, Ayrık Mantık ve Kripke Semantiği

Şemsiyye eseri, kelimelerin tekil tanımlarından ziyade, onların zaman, kiplik ve şartlı bağlantılarını (Tasdikat) regüle eder. Bu fazların öncelikli amacı, sistemdeki Kategorik Mantık (FOL) bağımlılığını kırarak, İslâm felsefesinde çokça kullanılan Ayrık (Disjunctive) ve Şartlı (Hypothetical) önermeleri Z3 motoruna entegre etmektir.

İlk adımda, `IlmWadAdapter` içerisindeki `has_condition` metodolojisi genişletilerek İslâm felsefesindeki "Lüzumî" (gerektirici) ve "İnâdî" (dışlayıcı) şartlı yapılar modellenecektir. Özellikle İnâdî önermelerde, zıtların bir araya gelemeyeceği (Cem'i Mânia - XOR mantığı) ve ikisinin birden ortadan kalkamayacağı (Hulüvv - NAND mantığı) koşullar Z3 kısıtlarına dönüştürülecektir. Geliştirici ekibin yazmış olduğu `test_inadi_mutually_exclusive_operator` birim testi, İnadi (XOR) mantığının Z3 üzerinde `UNSAT` döndürmeyi başardığını kanıtlamıştır; bu başarı tüm mimariye yayılacaktır.

İkinci ve en karmaşık adım, Kâtibî'nin 13 kipli önermesini sisteme kazandırmaktır. Zaman ve zorunluluk, bir argümanın doğruluğunu kökten değiştirir. Kripke semantiğini Z3'e gömmek için, `logic_parser.py` içerisindeki `WorldSort` (Olası Dünyalar) bağıntısının yanına `TimeSort` (Zaman Düzlemi) parametresi eklenecektir (`self.TimeSort = z3.DeclareSort('Time')`). Böylece tüm ontolojik yüklemlerin aritesi $(w, t, x)$ formatına yükseltilecektir ($w$: Dünya, $t$: Zaman, $x$: Varlık).

Bu radikal genişleme ile Kâtibî'nin kiplikleri sisteme şu şekilde entegre edilecektir:

- **Zarûriyye-i Mutlaka:** Konunun zatı var olduğu sürece yüklemin konuya aidiyetinin zorunluluğunu ifade eder. Z3 uzayında hem zaman hem de olası dünyalar üzerinde evrensel niceleyici ($\forall w, \forall t$) kullanılarak modellenecektir.
- **Dâime-i Mutlaka:** Varlık mevcut olduğu sürece yüklemin sürekli aidiyetidir ancak mutlak mantıksal zorunluluk içermez. Zaman ekseninde evrensel ($\forall t$), dünya ekseninde varoluşsal ($\exists w$) niceleyici ile formüle edilecektir.
- **Mümkine-i Âmme:** Eylemin veya nitelemenin potansiyel mümkünlüğünü ifade eder. Kripke dünyalarında en az bir anlık kesişimde `SAT` dönebilecek esnek bir kısıt olarak kodlanacaktır.

Şemsiyye entegrasyonunun bir diğer zorunluluğu, `linguistics/contextual_lexicon.py` modülünün üç boyutlu bir tensöre (`word -> namespace -> proposition_type -> ontologic_id`) dönüşmesidir. Bir Eş'arî kelâmcısı, bir kelimeyi kategorik bir cümlede mecaz olarak kullanırken, ayrık bir şartlı kıyasta literal olarak kullanabilir. Leksikonun önerme tipini (`Kadiyye-i_Hamliyye` veya `Kadiyye-i_Sartiyye`) dikkate alarak kelimeye farklı ontolojik ID'ler ataması, bağlamsal semantiğin (Semantik Esneklik) tam olarak sağlanmasını garanti edecektir.

### Faz 3 & 4: Cürcânî Diyalektiği ve Çok-Aktörlü Sonlu Durum Makinesi

Projenin son evresi, sistemi hakikate ulaşmak için karşılıklı çürütme ve savunma üzerine kurulu esnek bir diyalektik protokole, yani Cürcânî'nin Âdâbu'l-Bahs (Münazara Kuralları) otomatına dönüştürmektir.

Bu geçişteki en kritik mühendislik hamlesi, Söylem Belleğinin (Discourse Register) izole edilmesidir. Tekil bir LIFO yığıtı kullanan mevcut bellek, tartışmanın karşılıklı doğasını bozmaktadır. B Safhasında, bellek `mujib_frames` ve `sail_frames` olmak üzere ikiye ayrılacak, zamir çözümlemeleri (`resolve_pronoun`) aktif konuşmacının kendi ön kabullerine (Müsellemât) göre yapılarak "Bağlam Zehirlenmesi" (Context Poisoning) tamamen ortadan kaldırılacaktır.

`schools/taftazani/adab_al_bahth.py` modülündeki Sonlu Durum Makinesi (FSM), Cürcânî'nin itiraz hiyerarşisine uygun olarak durum bazlı (Stateful) hale getirilecektir. Sistem şu kod durumları etrafında dönecektir:

- **AWAITING_CLAIM (Da'vâ):** Mucîb (savunucu) iddiasını sunar. Eğer bu iddia doğası gereği bir Aksiyom (Bedîhî) ise, sistem `TAHSIL_I_HASIL` statüsü ile ispatı gereksiz bularak durumu sonlandırır. Aksi halde sıra Sâil'e geçer ve otomatik bir `Men'` (reddediş) ile kanıt istenir.
- **AWAITING_EVIDENCE (Delil Beklentisi):** Mucîb argümanının öncüllerini Z3'e sunar. Öncüller kendi içinde tutarlıysa (`SAT`) sıra saldırı için Sâil'e geçer.
- **AWAITING_ATTACK (Hücum):** Sâil, argümana üç belirli yolla saldırabilir :
  1. **Men' (Kanıtsız Red):** Sâil öncüllerden birini kabul etmez. FSM otonom olarak `AWAITING_EVIDENCE` durumuna geri döner ve Mucîb reddedilen öncülü ara-iddia olarak yeniden ispatlamak zorunda kalır.
  2. **Nakz (Fâsid İstidlâl):** Sâil, "öncüller doğru kabul edilse bile lüzum bağının (Hadd-i Evsat) yanlış olduğunu" iddia eder. Z3 motoru, öncüllerden yola çıkarak iddianın tam tersini doğrulamaya çalışır. Z3 bunu `SAT` yaparsa, Mucîb'in mantıksal kurgusunun hatalı olduğu ispatlanır ve `NAKZ_SUCCESS` kararı çıkar.
  3. **Mu'aradah (Diyalektik Kilitlenme):** Cürcânî diyalektiğinin zirvesidir. İki farklı felsefi uzayın çarpışmasıdır. Orkestratördeki `execute_cross_school_muaradah` metodu, Z3'ün `push/pop` yalıtımı ile Mucîb'in uzayını dondurur ve Sâil'in tamamen zıt ontolojik öncüllerini aynı matrise zerk eder (Cross-Injection). Ortak çözücü patlayıp `UNSAT` üretirse, eşdeğer güçte zıt bir hakikat bulunarak "Diyalektik Kilitlenme" (Stalemate) yaratıldığı raporlanır.

Aşağıdaki tablo, Cürcânî FSM'sinin diyalektik durumlara verdiği tepkileri özetlemektedir:


|                        |                                                           |                                                                                              |
| ---------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **FSM Durumu (State)** | **Diyalektik Beklenti**                                   | **SMT (Z3) Motorunun Davranışı ve İzolasyon**                                                |
| **Da'vâ (İddia)**      | Mucîb'in tezi sunması ve Sâil'in kanıt istemesi.          | `verify_syllogism` ile aksiyom kontrolü. Aksiyom ise `TAHSIL_I_HASIL` dönülür.               |
| **Men' (İtiraz)**      | Rakibin öncülünü tartışmaya açıp ispat istemek.           | SMT reddedilen öncülü geçersiz sayar, FSM Mucîb'i ispat yükümlülüğüne geri sokar.            |
| **Nakz (Çürütme)**     | Öncüller doğru kabul edilse de lüzum bağının koparılması. | Z3, neticenin tersini sınar. Eğer sonuç `SAT` çıkarsa mantık kurgusu çöker (`NAKZ_SUCCESS`). |
| **Mu'aradah**          | Karşıt ekolün, iptal edici zıt bir argüman sunması.       | İki ekol Z3 `push/pop` ile aynı matrise zerk edilir. Çelişki (`UNSAT`) kilitlenme sayılır.   |


## Kurulum, Test ve Katkı Rehberi (Developer Guidelines)

Sistemin bütüncül vizyonunu gerçekleştirmek isteyen yeni geliştiricilerin, projeyi klonlayıp kendi ortamlarında ayağa kaldırmaları ve CI (Continuous Integration) testlerini yürütmeleri için hazırlanan bu bölüm, proje dökümantasyon standartlarına göre düzenlenmiştir. Epistemic Framework, hiçbir dış bulut servisine, API anahtarına veya LLM bağımlılığına ihtiyaç duymayan bütünüyle izole ve otonom bir sistemdir.

**Ön Gereksinimler ve Kurulum:** Sistemin çalıştırılabilmesi için Python 3.9 veya üzeri bir sürümün yüklü olması tavsiye edilmektedir. Projenin kalbini Microsoft'un Z3 SMT çözücüsü (`z3-solver`) ve veri yapılarını doğrulayan `pydantic` kütüphanesi oluşturmaktadır.

Bash

```
# Proje deposunu yerel diskinize klonlayın
git clone https://github.com/epistemic-framework/core-engine.git

# Gerekli kütüphaneleri yükleyin
pip install z3-solver pydantic

```

**Sistem Sağlık Taraması (Healthcheck):** Geliştiricilerin sistemde yaptıkları en ufak sentaktik bir değişiklik, Z3'ün Kripke uzayında kelebek etkisine yol açarak sonsuz döngülere sebep olabilir. Sistem bileşenlerinin entegrasyonunu doğrulamak için uçtan uca (E2E) çalışan `run_simulation.py` betiği tasarlanmıştır.

Bash

```
python3 run_simulation.py

```

Bu komut; `yadu allahi` ve `tekvinu allahi` örnek cümlelerini alarak, Eş'arî, Selefî ve Mâtürîdî uzaylarında L1, L2 ve L3 katmanlarını eşzamanlı test eder. Te'vil (Defeasibility) mekanizmasının, "Tekvin" düğümü blokajlarının ve L2 otorite kararlarının terminale hatasız loglanması gerekmektedir.

**Red-Teaming ve Güvenlik Sınamaları:** Sistemin Combinatorial Explosion (Kombinatoryal patlama) yaratmadığını veya "Çelişkiden her şey çıkar" (Ex Falso Quodlibet) mantıksal hatasına düşmediğini kanıtlamak için birim testlerinin çalıştırılması mutlak bir zorunluluktur.

Bash

```
python3 -m unittest discover tests/

```

Test mimarisi şu güvenlik katmanlarını kapsar :

1. `test_z3_engine.py`**:** İmkansız yatay ontolojik kesişimlere (Örn: Bir şeyin aynı anda hem insan hem at olması) Z3'ün izin verip vermediğini (`test_sibling_disjointness`) ve `Z3ExpressionBuilder` içerisindeki `max_depth` (rekürsif derinlik limiti) aşım saldırılarının Stack Overflow yaratıp yaratmadığını sınar.
2. `test_grammar.py`**:** Sarf motorunun kalbi olan İ'lâl ve İbdâl fonolojik geri dönüşüm algoritmaları ile Tokenizer'daki Clitic Splitting (Ön-ek koparma) testlerini doğrular.
3. `test_adab_al_bahth_fsm.py`**:** Durum makinesinin (FSM) sıralamayı (Da'vâ -> Delil -> İtiraz) atlamadığını ve Çapraz Usûl (Muaradah) kilitlenmelerinde izole matrisin bağlam sızdırmadığını test eder.

Projeye katkıda bulunacak (Contribution) geliştiricilerin, özellikle modal mantık veya yeni bir fıkhî usûl profili eklerken, arite (değişken sayısı) senkronizasyonuna dikkat etmesi şarttır. N-Ary yüklemlere `TimeSort` eklendiğinde, `logic_parser.py` içerisindeki tüm arite doğrulama kodlarının $+1$ seviyesinde güncellenmesi ve yeni bir aksiyom eklendiğinde `_memoization_cache` değişkeninin sıfırlanması (Cache Invalidation) gerekmektedir.

Epistemic Framework; dilin salt sentaktik bir araç olduğu yanılgısını yıkarak onu ontolojik bir matris olarak kabul eden, İslâm mantık tarihinin derin felsefi birikimini SMT determinizmi ile kusursuzca harmanlayan öncü bir mimaridir. İsağoci tabanından Şemsiyye kipliklerine ve nihayetinde Cürcânî'nin çok-aktörlü diyalektik otomatına uzanan bu yolculuk, sadece kelâm veya hukuk metinlerini analiz etmekle kalmayacak; aynı zamanda yapay zekâ etiğinde şeffaf, izlenebilir ve %100 matematiksel ispat sunabilen Bilişsel Çıkarım Motorları için yepyeni bir küresel endüstri standardı belirleyecektir.