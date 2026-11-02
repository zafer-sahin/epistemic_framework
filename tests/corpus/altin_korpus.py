"""
.. felsefe_notu:: Sarf ve Nahiv Altın Korpusu
    Bu korpus, motorun klasik sarf ve nahiv bilgisini ölçer. Beklentiler motora göre değil, medrese
    müfredatının temel metinlerine göre yazılmıştır:

    - Emsile: Emsile-i Muhtelife (bir kökün türevleri) ve Emsile-i Muttaride (sîgalar); örnek kök n-s-r.
    - Binâ (Binâü'l-Ef'âl): illetli fiil sınıfları ve mezîd bâblar.
    - İzhâr ve Avâmil (Birgivî): i'râb ve âmil-ma'mûl ilişkileri.
    - el-İnsâf (İbnü'l-Enbârî): Basra ile Kûfe arasındaki ihtilaflar (fiilden önce gelen isim).

    Transliterasyon motorun bugünkü girdi kuralını izler: Türkçe harfler; sâlim kalıplarda uzun ünlü
    yazılmaz ("nasirun" = nâsırun), illetli fiillerde çift harfle yazılır ("qaala", "ramaa"); hemze ve
    ayn kesme işaretiyle (') yazılır; harf-i ta'rif "el_" ya da "al_" önekidir.

    Bugün motorun yanlış çözdüğü örnekler `bilinen_eksik` alanında, aşağıdaki kodlardan biriyle
    işaretlidir; bu örneklerin testleri beklenen hata (expectedFailure) sayılır. Bir eksik giderildiğinde
    test "beklenmeyen başarı" verir; işaret o zaman kaldırılır. Beklentiler, bir örnek düşüyor diye
    motora uydurulmaz.
"""

BILINEN_EKSIKLER = {
    "P2-1": "Tokenizer, kelimenin ilk hecesini ön ek (wa-, fa-, bi-, li-, ka-, la-) sanıp koparıyor.",
    "P2-2": "İlletli köklerde vav/ye ve ibdâl/idğâm yanlış geri kuruluyor.",
    "P2-3": "İ'râb, sayı ve cins sonek sırasından ve varsayılan 'müzekker' değerinden yanlış çıkıyor.",
    "KALIP": "Sîga ya da bâb kalıp grafında yok; kelime isim sayılıyor ya da başka bir kalıba düşüyor.",
    "KOK": "Masdar ve türemiş isimlerde kök yerine gövde döndürülüyor.",
    "CEM": "Cem'-i mükesserde kök kalıbın harfini içeriyor; sayı, uyum kuralı yüzünden müfred görünüyor.",
    "TRANSLIT": "Uzun ünlü yazılmadığı için fe'ile ile fâ'ile kalıpları ayrılamıyor.",
    "NAHIV-FAIL": "Fiilden önce gelen isim fâil sayılıyor; Basra'ya göre mübtedadır, fâil gizli zamirdir.",
    "NAHIV-MUBTEDA": "Mübteda belirliliğe göre değil sıraya göre seçiliyor.",
    "NAHIV-MANKUS": "İsm-i mankûsun tenvinli hâli ('nâmin') mecrûr sanılıp izafet kuruluyor.",
    "NAHIV-KANE": "Kâne ve kardeşlerinin ameli modellenmiyor.",
    "NAHIV-SILA": "İsm-i mevsûl ile sıla cümlesi arasındaki bağ kurulmuyor.",
}

# ---------------------------------------------------------------------------------------------
# İMLÂ: Bitişik harflerin ayrılması (tokenizer)
# ---------------------------------------------------------------------------------------------
TOKENIZER = [
    # Kelimenin kendi harfiyle başlayan kelimeler bölünmemeli.
    {"girdi": "kataba", "beklenen": ["kataba"], "kaynak": "Emsile: k-t-b, mâzî", "bilinen_eksik": "P2-1"},
    {"girdi": "kalamun", "beklenen": ["kalamun"], "kaynak": "kelâm: k-l-m", "bilinen_eksik": "P2-1"},
    {"girdi": "wacibun", "beklenen": ["wacibun"], "kaynak": "vâcib: w-c-b", "bilinen_eksik": "P2-1"},
    {"girdi": "wahidun", "beklenen": ["wahidun"], "kaynak": "vâhid: w-h-d", "bilinen_eksik": "P2-1"},
    {"girdi": "kaimun", "beklenen": ["kaimun"], "kaynak": "kâim: q-w-m, ism-i fâil", "bilinen_eksik": "P2-1"},
    {"girdi": "lisanun", "beklenen": ["lisanun"], "kaynak": "lisân: l-s-n", "bilinen_eksik": "P2-1"},
    {"girdi": "bintun", "beklenen": ["bintun"], "kaynak": "bint: b-n-y", "bilinen_eksik": "P2-1"},
    {"girdi": "lahmun", "beklenen": ["lahmun"], "kaynak": "lahm: l-h-m", "bilinen_eksik": "P2-1"},
    {"girdi": "fasala", "beklenen": ["fasala"], "kaynak": "Binâ: f-s-l, mâzî", "bilinen_eksik": "P2-1"},
    {"girdi": "wa'ada", "beklenen": ["wa'ada"], "kaynak": "Binâ: misâl w-'-d", "bilinen_eksik": "P2-1"},
    # Bitişik yazılan harf-i cer, atıf ve lâm ayrılmalı.
    {"girdi": "waqaala", "beklenen": ["wa", "qaala"], "kaynak": "vâv-ı âtıfe"},
    {"girdi": "bizeydin", "beklenen": ["bi", "zeydin"], "kaynak": "Avâmil: harf-i cer bâ"},
    {"girdi": "lizeydin", "beklenen": ["li", "zeydin"], "kaynak": "Avâmil: harf-i cer lâm"},
    {"girdi": "fanasara", "beklenen": ["fa", "nasara"], "kaynak": "fâ-i âtıfe"},
    {"girdi": "wakataba", "beklenen": ["wa", "kataba"], "kaynak": "vâv-ı âtıfe + k-t-b", "bilinen_eksik": "P2-1"},
    {"girdi": "lazeydun", "beklenen": ["le", "zeydun"], "kaynak": "lâm-ı ibtidâ (tevkîd)",
     "not": "Bitişik lâm, nefy edatı 'lâ' ile karışmasın diye 'le' olarak ayrılır (P0-6)."},
    {"girdi": "laysa", "beklenen": ["laysa"], "kaynak": "leyse: nefy fiili"},
]

# ---------------------------------------------------------------------------------------------
# SARF: Tek kelimenin çözümlemesi
# Alanlar: kok, tur (Fiil/Ism), cati (Active/Passive), kalip, zamir (müstetir zamir), rol (Agent/Patient),
# irab, sayi (Mufred/Tesniye/Cemi), cins (Muzekker/Muennes), gayri_munsarif.
# ---------------------------------------------------------------------------------------------
SARF = [
    # Emsile-i Muhtelife: n-s-r (nasara - yansuru)
    {"girdi": "nasara", "beklenen": {"kok": "nsr", "tur": "Fiil", "cati": "Active", "kalip": "Fa'ala", "zamir": "Huve"},
     "kaynak": "Emsile-i Muhtelife: mâzî-i ma'lûm"},
    {"girdi": "yansuru", "beklenen": {"kok": "nsr", "tur": "Fiil", "cati": "Active", "kalip": "Yaf'ulu", "zamir": "Huve"},
     "kaynak": "Emsile-i Muhtelife: muzâri'-i ma'lûm"},
    {"girdi": "nasran", "beklenen": {"kok": "nsr", "tur": "Ism", "irab": "Mansub"},
     "kaynak": "Emsile-i Muhtelife: masdar", "bilinen_eksik": "KOK"},
    {"girdi": "mansaran", "beklenen": {"kok": "nsr", "tur": "Ism", "irab": "Mansub"},
     "kaynak": "Emsile-i Muhtelife: masdar-ı mîmî", "bilinen_eksik": "KOK"},
    {"girdi": "nasirun", "beklenen": {"kok": "nsr", "tur": "Ism", "kalip": "Fâ'ilun", "rol": "Agent", "irab": "Marfu"},
     "kaynak": "Emsile-i Muhtelife: ism-i fâil (fe-huve nâsırun)"},
    {"girdi": "mansurun", "beklenen": {"kok": "nsr", "tur": "Ism", "kalip": "Maf'ûlun", "rol": "Patient", "irab": "Marfu"},
     "kaynak": "Emsile-i Muhtelife: ism-i mef'ûl (ve zâke mansûrun)"},
    {"girdi": "yansur", "beklenen": {"kok": "nsr", "tur": "Fiil"},
     "kaynak": "Emsile-i Muhtelife: lem yansur (muzâri'-i meczûm)", "bilinen_eksik": "KALIP"},
    {"girdi": "yansura", "beklenen": {"kok": "nsr", "tur": "Fiil"},
     "kaynak": "Emsile-i Muhtelife: len yansura (muzâri'-i mansûb)", "bilinen_eksik": "KALIP"},
    {"girdi": "unsur", "beklenen": {"kok": "nsr", "tur": "Fiil"},
     "kaynak": "Emsile-i Muhtelife: emr-i hâzır", "bilinen_eksik": "KALIP"},
    {"girdi": "nusira", "beklenen": {"kok": "nsr", "tur": "Fiil", "cati": "Passive", "kalip": "Fu'ila"},
     "kaynak": "Emsile-i Muhtelife: mâzî-i meçhul"},
    {"girdi": "yunsaru", "beklenen": {"kok": "nsr", "tur": "Fiil", "cati": "Passive", "kalip": "Yuf'alu"},
     "kaynak": "Emsile-i Muhtelife: muzâri'-i meçhul"},
    {"girdi": "minsarun", "beklenen": {"kok": "nsr", "tur": "Ism"},
     "kaynak": "Emsile-i Muhtelife: ism-i âlet", "bilinen_eksik": "KOK"},

    # Emsile-i Muttaride: mâzî ve muzâri' sîgaları
    {"girdi": "nasarat", "beklenen": {"kok": "nsr", "tur": "Fiil", "kalip": "Fa'alat", "zamir": "Hiye"},
     "kaynak": "Emsile-i Muttaride: müfrede-i müennese-i gâibe"},
    {"girdi": "nasaru", "beklenen": {"kok": "nsr", "tur": "Fiil"},
     "kaynak": "Emsile-i Muttaride: cem'-i müzekker-i gâib (nasarû)", "bilinen_eksik": "KALIP"},
    {"girdi": "nasartu", "beklenen": {"kok": "nsr", "tur": "Fiil"},
     "kaynak": "Emsile-i Muttaride: vâhid-i mütekellim", "bilinen_eksik": "KALIP"},
    {"girdi": "tansuru", "beklenen": {"kok": "nsr", "tur": "Fiil"},
     "kaynak": "Emsile-i Muttaride: muzâri', müfred-i müzekker-i muhâtab", "bilinen_eksik": "KALIP"},

    # Binâ: illetli fiil sınıfları (mâzî)
    {"girdi": "'akala", "beklenen": {"kok": "'kl", "tur": "Fiil"}, "kaynak": "Binâ: mehmûzü'l-fâ"},
    {"girdi": "madda", "beklenen": {"kok": "mdd", "tur": "Fiil"}, "kaynak": "Binâ: mudâaf", "bilinen_eksik": "KALIP"},
    {"girdi": "wa'ada", "beklenen": {"kok": "w'd", "tur": "Fiil"}, "kaynak": "Binâ: misâl-i vâvî"},
    {"girdi": "qaala", "beklenen": {"kok": "qwl", "tur": "Fiil", "kalip": "Fa'ala_Ecvef"}, "kaynak": "Binâ: ecvef-i vâvî"},
    {"girdi": "baa'a", "beklenen": {"kok": "by'", "tur": "Fiil"}, "kaynak": "Binâ: ecvef-i yâî", "bilinen_eksik": "P2-2"},
    {"girdi": "da'aa", "beklenen": {"kok": "d'w", "tur": "Fiil"}, "kaynak": "Binâ: nâkıs-ı vâvî"},
    {"girdi": "ramaa", "beklenen": {"kok": "rmy", "tur": "Fiil"}, "kaynak": "Binâ: nâkıs-ı yâî", "bilinen_eksik": "P2-2"},
    {"girdi": "waqaa", "beklenen": {"kok": "wqy", "tur": "Fiil"}, "kaynak": "Binâ: lefîf-i mefrûk", "bilinen_eksik": "P2-2"},
    {"girdi": "tawaa", "beklenen": {"kok": "twy", "tur": "Fiil"}, "kaynak": "Binâ: lefîf-i makrûn", "bilinen_eksik": "KALIP"},

    # Binâ: mezîd bâblar (mâzî)
    {"girdi": "akrama", "beklenen": {"kok": "krm", "tur": "Fiil"}, "kaynak": "Binâ: if'âl", "bilinen_eksik": "KALIP"},
    {"girdi": "kallama", "beklenen": {"kok": "klm", "tur": "Fiil"}, "kaynak": "Binâ: tef'îl", "bilinen_eksik": "KALIP"},
    {"girdi": "qaatala", "beklenen": {"kok": "qtl", "tur": "Fiil"}, "kaynak": "Binâ: mufâ'ale", "bilinen_eksik": "KALIP"},
    {"girdi": "inkasara", "beklenen": {"kok": "ksr", "tur": "Fiil"}, "kaynak": "Binâ: infi'âl", "bilinen_eksik": "KALIP"},
    {"girdi": "iktasaba", "beklenen": {"kok": "ksb", "tur": "Fiil"}, "kaynak": "Binâ: ifti'âl"},
    {"girdi": "ittasala", "beklenen": {"kok": "wsl", "tur": "Fiil"}, "kaynak": "Binâ: ifti'âl, misâlde ibdâl"},
    {"girdi": "ittaba'a", "beklenen": {"kok": "tb'", "tur": "Fiil"}, "kaynak": "Binâ: ifti'âl, idğâm", "bilinen_eksik": "P2-2"},
    {"girdi": "ihmarra", "beklenen": {"kok": "hmr", "tur": "Fiil"}, "kaynak": "Binâ: if'ilâl", "bilinen_eksik": "KALIP"},
    {"girdi": "istagfara", "beklenen": {"kok": "gfr", "tur": "Fiil"}, "kaynak": "Binâ: istif'âl", "bilinen_eksik": "KALIP"},
    {"girdi": "taqaatala", "beklenen": {"kok": "qtl", "tur": "Fiil"}, "kaynak": "Binâ: tefâ'ul", "bilinen_eksik": "KALIP"},

    # İzhâr: isimde i'râb, sayı ve cins
    {"girdi": "zeydun", "beklenen": {"irab": "Marfu", "sayi": "Mufred", "cins": "Muzekker"}, "kaynak": "İzhâr: ref' (damme)"},
    {"girdi": "zeyden", "beklenen": {"irab": "Mansub"}, "kaynak": "İzhâr: nasb (fetha)"},
    {"girdi": "zeydin", "beklenen": {"irab": "Majrur"}, "kaynak": "İzhâr: cerr (kesra)"},
    {"girdi": "fatimatu", "beklenen": {"irab": "Marfu", "sayi": "Mufred", "cins": "Muennes", "gayri_munsarif": True},
     "kaynak": "İzhâr: gayr-i munsarif (alemiyet ve te'nîs)", "bilinen_eksik": "P2-3"},
    {"girdi": "fatimate", "beklenen": {"irab": "Mansub_or_Majrur", "sayi": "Mufred", "cins": "Muennes", "gayri_munsarif": True},
     "kaynak": "İzhâr: gayr-i munsarifin cerri fetha ile", "bilinen_eksik": "P2-3"},
    {"girdi": "ahmedu", "beklenen": {"irab": "Marfu", "sayi": "Mufred", "cins": "Muzekker", "gayri_munsarif": True},
     "kaynak": "İzhâr: gayr-i munsarif (alemiyet ve vezn-i fiil)"},
    {"girdi": "ahmede", "beklenen": {"irab": "Mansub_or_Majrur", "gayri_munsarif": True},
     "kaynak": "İzhâr: gayr-i munsarifin cerri fetha ile"},
    {"girdi": "al_muslimune", "beklenen": {"irab": "Marfu", "sayi": "Cemi", "cins": "Muzekker"},
     "kaynak": "İzhâr: cem'-i müzekker-i sâlim, ref' vâv ile (-ûne)", "bilinen_eksik": "P2-3"},
    {"girdi": "al_muslimine", "beklenen": {"irab": "Mansub_or_Majrur", "sayi": "Cemi"},
     "kaynak": "İzhâr: cem'-i müzekker-i sâlim, nasb ve cerr yâ ile (-îne)", "bilinen_eksik": "P2-3"},
    {"girdi": "al_muslimuna", "beklenen": {"irab": "Marfu", "sayi": "Cemi"},
     "kaynak": "İzhâr: cem'-i müzekker-i sâlim (-ûna yazımı)"},
    {"girdi": "al_muslimina", "beklenen": {"irab": "Mansub_or_Majrur", "sayi": "Cemi"},
     "kaynak": "İzhâr: cem'-i müzekker-i sâlim (-îna yazımı)"},
    {"girdi": "muslimani", "beklenen": {"irab": "Marfu", "sayi": "Tesniye"}, "kaynak": "İzhâr: tesniye, ref' elif ile"},
    {"girdi": "muslimayni", "beklenen": {"irab": "Mansub_or_Majrur", "sayi": "Tesniye"}, "kaynak": "İzhâr: tesniye, nasb ve cerr yâ ile"},
    {"girdi": "muslimatun", "beklenen": {"irab": "Marfu", "sayi": "Cemi", "cins": "Muennes"}, "kaynak": "İzhâr: cem'-i müennes-i sâlim"},
    {"girdi": "kalimatun", "beklenen": {"sayi": "Mufred", "cins": "Muennes", "rol": None},
     "kaynak": "kelime: fe'ile kalıbı, ism-i fâil değil", "bilinen_eksik": "TRANSLIT"},
    {"girdi": "katibatun", "beklenen": {"kok": "ktb", "rol": "Agent", "sayi": "Mufred", "cins": "Muennes"},
     "kaynak": "kâtibe: fâ'ile kalıbı, ism-i fâil"},
    {"girdi": "mesacidu", "beklenen": {"kok": "scd", "sayi": "Cemi", "gayri_munsarif": True},
     "kaynak": "cem'-i mükesser (mefâ'il, sîga-i müntehe'l-cumû')",
     "not": "Akılsız çoğula müfred-müennes uyum yapılır; kelimenin kendisi yine cem'dir.", "bilinen_eksik": "CEM"},
    {"girdi": "kutubun", "beklenen": {"kok": "ktb", "sayi": "Cemi"}, "kaynak": "cem'-i mükesser (fu'ul)", "bilinen_eksik": "CEM"},
    {"girdi": "ricalun", "beklenen": {"kok": "rcl", "sayi": "Cemi", "cins": "Muzekker"}, "kaynak": "cem'-i mükesser (fi'âl)"},
]

# ---------------------------------------------------------------------------------------------
# NAHİV: Cümlede âmil-ma'mûl ilişkileri (tokenizer + sarf + nahiv)
# icermeli/icermemeli: (âmil, ma'mûl, ilişki) üçlüleri. Motorda henüz olmayan yapılar için ilişki
# adları mevcut adlandırmayı izler (inne -> Amel_Inne_Ism; kâne -> Amel_Kane_Ism).
# ---------------------------------------------------------------------------------------------
NAHIV = [
    {"girdi": "nasara zeydun amran",
     "icermeli": [("nasara", "zeydun", "Fail"), ("nasara", "amran", "Meful")],
     "kaynak": "Avâmil: fiil fâilini ref', mef'ûlünü nasb eder"},
    {"girdi": "nusira zeydun",
     "icermeli": [("nusira", "zeydun", "Naib_Fail")],
     "kaynak": "Avâmil: meçhul fiil nâib-i fâilini ref' eder"},
    {"girdi": "zeydun nasirun",
     "icermeli": [("Rabita_Virtual", "zeydun", "Rabita_Subject"), ("nasirun", "zeydun", "Rabita_Predication")],
     "kaynak": "İzhâr: mübteda ve haber merfûdur"},
    {"girdi": "nasirun zeydun",
     "icermeli": [("nasirun", "zeydun", "Rabita_Predication")],
     "kaynak": "Muğni'l-Lebîb: marife mübteda, nekre haber; haberin takdîmi câizdir", "bilinen_eksik": "NAHIV-MUBTEDA"},
    {"girdi": "zeydun nasara amran",
     "icermeli": [("Rabita_Virtual", "zeydun", "Rabita_Subject"), ("nasara", "amran", "Meful")],
     "icermemeli": [("nasara", "zeydun", "Fail")],
     "kaynak": "el-İnsâf: Basra'ya göre fâil fiilden önce gelmez; Zeyd mübteda, fâil gizli zamirdir",
     "bilinen_eksik": "NAHIV-FAIL"},
    {"girdi": "kitabu zeydin",
     "icermeli": [("kitabu", "zeydin", "Mudaf_MudafIlayh")],
     "kaynak": "İzhâr: muzâfun ileyh mecrûrdur"},
    {"girdi": "inna zeydan nasirun",
     "icermeli": [("inna", "zeydan", "Amel_Inne_Ism"), ("inna", "nasirun", "Amel_Inne_Haber")],
     "kaynak": "Avâmil: inne ismini nasb, haberini ref' eder"},
    {"girdi": "inna zeydan namin",
     "icermeli": [("inna", "namin", "Amel_Inne_Haber")],
     "icermemeli": [("zeydan", "namin", "Mudaf_MudafIlayh")],
     "kaynak": "İzhâr: ism-i mankûs ('nâmin') merfû ve mecrûrda takdîrî i'râb alır; tenvinli isim muzâf olmaz",
     "bilinen_eksik": "NAHIV-MANKUS"},
    {"girdi": "kana zeydun nasiran",
     "icermeli": [("kana", "zeydun", "Amel_Kane_Ism"), ("kana", "nasiran", "Amel_Kane_Haber")],
     "kaynak": "Avâmil: kâne ismini ref', haberini nasb eder", "bilinen_eksik": "NAHIV-KANE"},
    {"girdi": "zeydun fi el_beyti",
     "icermeli": [("fi", "el_beyti", "Harf_Mecrur"), ("Kainun_Virtual", "fi", "Muteallak_Mekan")],
     "kaynak": "Muğni'l-Lebîb: şibh-i cümle haberin müteallakı mahzûftur (kâinun)"},
    {"girdi": "ellezi nasara zeydun",
     "icermeli": [("ellezi", "nasara", "Rel_Sila"), ("nasara", "zeydun", "Fail")],
     "kaynak": "İzhâr: ism-i mevsûl ve sılası", "bilinen_eksik": "NAHIV-SILA"},
    {"girdi": "zeydun la yansuru",
     "icermeli": [("yansuru", "la", "Nefy_Modifier")],
     "kaynak": "lâ-yı nâfiye muzâri'i olumsuzlar (P0-6)"},
    {"girdi": "lam yansur zeydun",
     "icermeli": [("yansur", "lam", "Nefy_Modifier"), ("yansur", "zeydun", "Fail")],
     "kaynak": "Avâmil: lem muzâri'i cezm eder", "bilinen_eksik": "KALIP"},
    {"girdi": "lan yansura zeydun",
     "icermeli": [("yansura", "lan", "Nefy_Modifier"), ("yansura", "zeydun", "Fail")],
     "kaynak": "Avâmil: len muzâri'i nasb eder", "bilinen_eksik": "KALIP"},
]
