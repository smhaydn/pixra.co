import os
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv

# .env dosyasini yukle
load_dotenv()


# ──────────────── PYDANTIC MODELLERI ────────────────

class ProductAIContent(BaseModel):
    """
    Yapay Zeka tarafindan uretilecek e-ticaret iceriklerini barindiran Pydantic modeli.
    SEO + GEO + E-E-A-T standartlarina uygun, zenginlestirilmis cikti yapisi.
    """

    # ── TEMEL SEO ALANLARI ──
    urun_adi: str = Field(
        ...,
        description="Intent-Based Naming protokolune gore formatlanmis urun adi. "
                    "Formul: [Marka] + [Kategori/Islev] + [Ayirt Edici Ozellik] + [Materyal/Spesifikasyon] + [Varyant]"
    )
    seo_baslik: str = Field(
        ...,
        description="Maksimum 60 karakterlik SEO Title. En kritik anahtar kelime en solda. "
                    "Kullanicinin 'ne alacagini' ve 'neden bizden alacagini' saniyeler icinde anlatmali."
    )
    seo_aciklama: str = Field(
        ...,
        description="Maksimum 155 karakterlik SEO Description. KESINLIKLE 155 karakteri ASMAYIN. "
                    "Karakter sayimini dikkatlice yapin. Ana fayda + Call to Action icermeli."
    )
    seo_anahtarkelime: str = Field(
        ...,
        description="Arama motorlari icin virgullu SEO anahtar kelimeleri. "
                    "Ana kelime + LSI (semantik) terimler + kullanici niyet varyasyonlari dahil."
    )
    anahtar_kelime: str = Field(
        ...,
        description="Magaza ici arama ve kategorizasyon icin virgullu alternatif/esanlamli kelimeler."
    )
    hedef_anahtar_kelime: str = Field(
        ...,
        description="Bu urunun siralanmasi gereken TEK odak anahtar kelime (focus keyword). "
                    "Arama hacmi yuksek, rekabet uygun, transactional niyetli olmali."
    )

    # ── ICERIK ALANLARI ──
    onyazi: str = Field(
        ...,
        description="Kisa, dikkat cekici, HTML <b>/<strong> ile desteklenmis ozellik vurgulu on yazi (spot metin)."
    )
    aciklama: str = Field(
        ...,
        description="Detayli urun aciklamasi. HTML formatinda. Zorunlu icerik bloklari: "
                    "1) Urun tanitim paragrafi, 2) Ozellik listesi (<ul>), "
                    "3) Neden Bu Urun bolumu (E-E-A-T), 4) Kullanim/Bakim rehberi, "
                    "5) Teknik detaylar tablosu."
    )

    # ── GEO (GENERATIVE ENGINE OPTIMIZATION) ALANLARI ──
    geo_ozet: str = Field(
        ...,
        description="Yapay zeka motorlarinin (ChatGPT, Gemini, Perplexity) dogrudan alintilayabilecegi "
                    "2-3 cumlelik, olgusal ve otoriter urun ozeti. Somut bilgi icermeli (malzeme, olcu, islem vb.)."
    )
    geo_sss: list[dict[str, str]] = Field(
        ...,
        description="Minimum 5 adet SSS. Her biri 'soru' ve 'cevap' anahtarli. "
                    "Soru tipleri: bilgi arayan, karsilastirma yapan, satin alma niyetli, "
                    "kullanim rehberi ve teknik destek sorgulari kapsamali."
    )
    uzun_kuyruk_sorgular: list[str] = Field(
        ...,
        description="Bu urunle eslesmesi gereken 5-8 adet long-tail arama sorgusu. "
                    "Ornek: 'kisa boylu kadinlar icin topuklu ayakkabi', 'yaz icin nefes alan spor ayakkabi'. "
                    "Turkce kullanici arama kaliplarina uygun olmali."
    )

    # ── GORSEL SEO ──
    gorsel_alt_text: str = Field(
        ...,
        description="Ana gorsel icin SEO uyumlu alt text. Gorsel icerigini AI tarayicilarinin "
                    "anlayacagi derinlikte betimleyen, anahtar kelime iceren, dogal dilde aciklama. "
                    "Maks 125 karakter."
    )

    # ── YAPILANDIRILMIS VERI ──
    urun_ozellikleri: list[dict[str, str]] = Field(
        ...,
        description="Gorselden cikarilan yapilandirilmis urun ozellikleri. "
                    "Her bir ozellik 'ozellik' ve 'deger' anahtarli dict. "
                    "Ornek: {{'ozellik': 'Malzeme', 'deger': 'Hakiki Deri'}}, "
                    "{{'ozellik': 'Renk', 'deger': 'Siyah'}}. "
                    "Minimum 5 ozellik: Malzeme, Renk, Stil, Kullanim Alani, Bakim."
    )
    kullanim_alanlari: str = Field(
        ...,
        description="Urunun kullanilabilecegi senaryolar ve ortamlar. "
                    "Ornek: 'Gunluk kullanim, ofis, ozel davetler, hediye'. "
                    "Kullanicinin kendini urunle hayal etmesini saglayan somut durum tasvirleri."
    )
    neden_bu_urun: str = Field(
        ...,
        description="E-E-A-T uyumlu 'Neden Bu Urun?' bolumu. Uzman perspektifinden yazilmis, "
                    "rakip urunlerden farkini ortaya koyan, somut veri ve deneyim iceren ikna metni. "
                    "Sektordeki konumunu, malzeme/iscilik avantajini ve kullanici faydalarini aciklar."
    )


# ──────────────── PROMPT SABLONLARI ────────────────

SYSTEM_PROMPT = """Sen dunyanin en iyi e-ticaret SEO ve GEO (Generative Engine Optimization) uzmanisin.
15 yillik deneyiminle Google, Yandex, Bing algoritmalarini ve ChatGPT, Gemini, Perplexity gibi
yapay zeka motorlarinin icerik degerlendirme kriterlerini derinlemesine biliyorsun.

UZMANLIK ALANLARIN:
- Arama Motoru Optimizasyonu (SEO): Teknik SEO, On-Page SEO, Semantik SEO, Featured Snippets
- Generative Engine Optimization (GEO): AI citability, quotability, structured authority
- E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness)
- Conversion Rate Optimization (CRO): Satin alma odakli icerik yazimi
- LSI (Latent Semantic Indexing) ve NLP-tabanli icerik stratejileri
- Schema.org yapilandirmasi ve Rich Snippet optimizasyonu
- Turkiye e-ticaret pazari dinamikleri ve Turkce arama davranislari

TEMEL ILKELERIN:
1. Her icerik parcasi bir KULLANICI NIYETINE (intent) karsilik gelmeli
2. Yapay zeka motorlari senin iceriginiden DOGRUDAN ALINTI yapabilmeli (citability)
3. Icerikler OLGUSAL ve SOMUT olmali — soyut pazarlama dili degil, olculebilir bilgi
4. Turkce dogal dil kaliplarina hakim olmali — kullanicilarin gercekte nasil aradigi onemli
5. Her urun icerigi bir BILGI OTORITESI (topical authority) insaa etmeli"""


def build_analysis_prompt(
    marka: str,
    gorsel_sayisi: int,
    breadcrumb_kat: str = "",
    adwords_kategori: str = "",
    adwords_tip: str = "",
    adwords_aciklama: str = "",
    mevcut_urun_adi: str = "",
    satisfiyati: str = "",
    kategoriler: str = "",
    stok_kodu: str = "",
    reference_content: str = ""
) -> str:
    """
    Urun analizi icin cok katmanli, uzman seviye prompt olusturur.
    """

    # Coklu gorsel talimati
    coklu_talimat = ""
    if gorsel_sayisi > 1:
        coklu_talimat = f"""
── GORSEL ANALIZ TALIMATI ──
Sana bu urune ait {gorsel_sayisi} FARKLI gorsel gonderilmistir.
Gorseller urunun farkli acilarini, renklerini, detaylarini veya kullanim senaryolarini gosterebilir.
TUM gorselleri BIRLIKTE analiz ederek:
- Malzeme ve doku bilgisini en detayli gorselden cikar
- Renk tutarliligini kontrol et, gercek rengi belirle
- Tasarim detaylarini (dikiş, fermuar, toka, aksesuar vb.) tespit et
- Boyut/orantı ipuclarini yakala
- Farkli acilardaki bilgileri birlestirerek BUTUNSEL bir analiz yap"""

    # Urun baglam bilgisi
    baglam_bloklari = []
    if mevcut_urun_adi:
        baglam_bloklari.append(f"- MEVCUT URUN ADI: {mevcut_urun_adi}")
    if breadcrumb_kat:
        baglam_bloklari.append(f"- BREADCRUMB KATEGORI: {breadcrumb_kat}")
    if adwords_kategori:
        baglam_bloklari.append(f"- REKLAM KATEGORISI: {adwords_kategori}")
    if adwords_tip:
        baglam_bloklari.append(f"- REKLAM TIPI: {adwords_tip}")
    if adwords_aciklama:
        baglam_bloklari.append(f"- REKLAM ACIKLAMASI: {adwords_aciklama}")
    if satisfiyati:
        baglam_bloklari.append(f"- SATIS FIYATI: {satisfiyati} TL")
    if kategoriler:
        baglam_bloklari.append(f"- KATEGORILER: {kategoriler}")
    if stok_kodu:
        baglam_bloklari.append(f"- STOK KODU: {stok_kodu}")
    if reference_content:
        baglam_bloklari.append(f"- REFERANS ICERIK: {reference_content}")

    baglam_metni = "\n".join(baglam_bloklari) if baglam_bloklari else "- Ek bilgi yok, tamamen gorsel analiz yap."

    # Fiyat pozisyonlama rehberi
    fiyat_rehberi = ""
    if satisfiyati:
        try:
            fiyat = float(str(satisfiyati).replace(",", ".").replace("TL", "").strip())
            if fiyat < 200:
                fiyat_rehberi = "FIYAT KONUMLANDIRMASI: Butce dostu / Uygun fiyatli segment. Icerik dilinde 'uygun fiyat', 'hesapli', 'ekonomik' vurgulari kullan."
            elif fiyat < 500:
                fiyat_rehberi = "FIYAT KONUMLANDIRMASI: Orta segment. Fiyat-performans dengesi, 'kaliteli ve makul fiyatli' vurgulari kullan."
            elif fiyat < 1500:
                fiyat_rehberi = "FIYAT KONUMLANDIRMASI: Ust-orta segment. 'Premium kalite', 'ozenli iscilik', 'yatirim degeri' vurgulari kullan."
            else:
                fiyat_rehberi = "FIYAT KONUMLANDIRMASI: Premium/luks segment. 'Ozel tasarim', 'sinirli uretim', 'ust duzey iscilik', 'luks deneyim' vurgulari kullan."
        except (ValueError, TypeError):
            pass

    prompt = f"""{SYSTEM_PROMPT}

════════════════════════════════════════════════
GOREV: {marka} markasina ait urun gorsel{'ler' if gorsel_sayisi > 1 else ''}ini analiz ederek
tam kapsamli SEO + GEO + E-E-A-T uyumlu icerik uret.
════════════════════════════════════════════════
{coklu_talimat}

── MEVCUT URUN VERILERI ──
MARKA: {marka}
{baglam_metni}
{fiyat_rehberi}

══════════════════════════════════════════
ADIM 1: OTOMATIK SEKTOR TESPITI VE GORSEL ANALIZ
══════════════════════════════════════════
1. Ilk olarak urunun hangi SEKTORDE oldugunu tespit et (Moda, Ic Giyim, Hirdavat, Kozmetik, Mobilya, Elektronik vb.).
2. Metinleri URETERKEN tespit ettigin sektore ozel su "Persona ve Odak" kurallarini uygula:
   - Canta/Moda/Ayakkabi: Kombinlenebilirlik, kumas dokusu, stil, trendler, ofis/gunluk siklik.
   - Ic Giyim: Hijyen, ten uyumu, nefes alabilen kumas, iz yapmaz tasarim, gun boyu konfor.
   - Hirdavat/Yapi Market: Dayaniklilik, malzeme kalitesi, teknik olculer, kullanim guvenligi, ergonomik tutus.
   - Kozmetik/Kisisel Bakim: Icerik (dermatolojik onay vb.), kullanim sikligi, cilt tipi, sonuc odaklilik.
   - Elektronik: Guc, hiz, garanti, sarj/kullanim suresi, teknik spesifikasyonlar.
   - Mobilya/Ev Tekstili: Kumas kalitesi, yikanabilirlik, boyutlar, dekorasyon uyumu.
   - Diger: Urunun ana fonksiyonuna uygun en rasyonel fayda neyse onu merkeze al.

3. Gorseldeki detaylari su unsurlara gore parcala:
- Urun kategorisi (ayakkabi, canta, giyim, hirdavat, kozmetik vb.)
- Ana malzeme (deri, kumas, plastik, celik, ahsap vb.)
- Renk paleti (ana renk + aksan renkler)
- Tasarim veya Teknik ozellikler (kesim, kalip, voltaj, devir, ozel bilesenler)
- Kullanim amaci ve Hedef kitle ipuclari
- Kalite gostergeleri (dikis kalitesi, yuzey isleme, guvenlik sertifikalari)

══════════════════════════════════════════
ADIM 2: SEO ICERIK URETIMI
══════════════════════════════════════════

■ URUN ADI (urun_adi):
  Formul: [Marka] + [Kategori/Islev] + [Ayirt Edici Ozellik] + [Materyal/Spesifikasyon] + [Varyant]
  Ornek: "Lola of Shine Kadın Günlük Sneaker Hakiki Deri Beyaz"
  KURALLAR:
  - Turkce arama aliskanliklarina uygun dogal sıralama
  - Gereksiz ingilizce kelime kullanma (zorunlu olmadikca)
  - Kategori kelimesini mutlaka icersin (ayakkabi, canta, elbise vb.)
  - Maksimum 80 karakter

■ SEO BASLIK (seo_baslik):
  KATMANDA 60 KARAKTER — TAM 60 KARAKTER VEYA ALTINDA OLMALI!
  Formul: [Odak Anahtar Kelime] + [Fark Yaratan Ozellik] | [Marka]
  Ornek: "Hakiki Deri Kadın Sneaker - Günlük Rahat | Lola of Shine"
  KURALLAR:
  - En yuksek arama hacimli kelime EN SOLDA
  - Power word kullan: Orjinal, Premium, Dogal, El Yapimi, Ozel Tasarim
  - Pipe (|) veya tire (-) ile marka ayir
  - Rakip basliklardan FARKLI ol

■ SEO ACIKLAMA (seo_aciklama):
  SON DERECE KRITIK: KESINLIKLE 155 KARAKTER VEYA ALTINDA OLMALIDIR! 
  BU BIR ZORUNLULUKTUR. METNI YAZDIKTAN SONRA KARAKTER SAYISINI ZIHINDEN SAYIN. EGER 155'I ASIYORSA YENIDEN KISALTARAK YAZIN!
  Formul: [Ana Fayda] + [Kanit/Ozellik] + [CTA]
  Ornek: "Hakiki deriden üretilen sneaker ile tüm gün konfor. Ortopedik taban, 2 yıl garanti. Hemen Keşfet!"
  KURALLAR:
  - Ilk 70 karakter icinde ana anahtar kelime VE fayda yer almali
  - Mutlaka bir CTA: "Hemen Kesfet", "Simdi Incele", "Firsati Yakala"
  - Rakamsal veri kullan: garanti suresi, indirim orani vb.

■ SEO ANAHTAR KELIMELER (seo_anahtarkelime):
  Virgullu, KATEGORIZE anahtar kelime kumesi:
  - 2 Ana kelime (yuksek arama hacmi): "kadin sneaker, hakiki deri ayakkabi"
  - 3 LSI/Semantik kelime: "gunluk spor ayakkabi, rahat yuruyus ayakkabi, deri kadin spor"
  - 2 Long-tail kelime: "beyaz deri kadin sneaker modelleri, ortopedik tabanli sneaker"
  Toplam 7-10 kelime grubu, virgullu.

■ SITE ICI ANAHTAR KELIMELER (anahtar_kelime):
  Kullanicilarin site icinde arayabilecegi alternatif terimler.
  Esanlamlilar, kisa formlar, konusma dili varyasyonlari.
  Ornek: "sneaker, spor ayakkabi, kadin spor, beyaz ayakkabi, casual ayakkabi"

■ ODAK ANAHTAR KELIME (hedef_anahtar_kelime):
  Bu urunun Google'da siralanmasi gereken TEK EN ONEMLI kelime grubu.
  Transactional niyet tasimali (satin alma amaçli).
  Ornek: "hakiki deri kadin sneaker"

══════════════════════════════════════════
ADIM 3: ICERIK URETIMI (GEO + E-E-A-T ODAKLI)
══════════════════════════════════════════

■ ON YAZI (onyazi):
  Kullaniciyi cezbeden kisa spot metin. HTML <strong> ile vurgulama yap.
  KURALLAR:
  - 1-2 cumle, maksimum 200 karakter
  - Ana fayda + duygusal tetikleyici
  - Ornek: "<strong>Hakiki deri</strong> ve <strong>ortopedik taban</strong> ile tum gun konfor. Hem sik hem rahat."

■ ACIKLAMA (aciklama):
  UZUN, ZENGIN, HTML FORMATINDA URUN ACIKLAMASI.
  Asagidaki bloklarin HEPSINI icermeli:

  BLOK 1 — URUN TANITIM PARAGRAFI (min 100 kelime):
  <p> etiketi ile. Urunu tanitan, ana faydalari anlatan, hedef kitleye hitap eden
  akici bir metin. Anahtar kelimeleri dogal sekilde yer. GEO icin: yapay zekanin
  dogrudan alintilayabilecegi olgusal cumleler kullan.
  Ornek: "X markasinin Y modeli, %100 hakiki deriden uretilmis olup ergonomik tabani
  sayesinde 12 saate kadar kesintisiz konfor saglar."

  BLOK 2 — OZELLIK LISTESI:
  <h3>Ozellikler</h3> basligi altinda <ul><li> ile:
  - Malzeme bilgisi
  - Tasarim detaylari
  - Konfor/fonksiyon ozellikleri
  - Bakim talimatlari
  - Garanti/iade bilgisi

  BLOK 3 — NEDEN BU URUN (E-E-A-T):
  <h3>Neden {marka}?</h3> basligi altinda:
  Uzman gorusu tarzinda yazilmis, gorseldeki urunun rakiplerden farkliliklarini
  somutlastiran paragraf. Deneyim ve uzmanlik vurgusu.

  BLOK 4 — KULLANIM REHBERI:
  <h3>Nasil Kullanilir / Bakim Rehberi</h3>:
  Kullanicinin urunu dogru kullanmasi/bakimini yapmasi icin pratik bilgiler.
  How-to icerigi olarak GEO motorlarinda snippet almaya uygun.

  BLOK 5 — TEKNIK DETAYLAR:
  <h3>Teknik Ozellikler</h3> altinda HTML <table> formatinda:
  Malzeme, boyut, agirlik, renk, bakim, uretim yeri vb.

■ GEO OZET (geo_ozet):
  KRITIK ALAN — Yapay zeka motorlarinin DOGRUDAN ALINTILAYACAGI metin.
  KURALLAR:
  - Tam 2-3 cumle
  - OLGUSAL ve SOMUT bilgi icermeli (malzeme, ozellik, olcu vb.)
  - Soyut pazarlama dili YASAK ("en iyi", "mukemmel" gibi subjektif ifadeler KULLANMA)
  - Ornek: "{marka} markasinin bu modeli, %100 hakiki dana derisinden el isciligile uretilmistir.
    Ortopedik EVA taban yapisi ve nefes alan astar sayesinde uzun sureli kullanim icin tasarlanmistir.
    38-44 arasi beden secenekleriyle sunulmaktadir."

■ NEDEN BU URUN (neden_bu_urun):
  E-E-A-T uyumlu, UZMAN PERSPEKTIFINDEN yazilmis ikna metni.
  KURALLAR:
  - 3-5 cumle
  - Somut karsilastirma noktasi icersin ("Sentetik alternatiflerin aksine...")
  - Malzeme/iscilik avantaji vurgula
  - Kullanici faydasi odakli

══════════════════════════════════════════
ADIM 4: SSS ve LONG-TAIL SORGULAR
══════════════════════════════════════════

■ GEO SSS (geo_sss):
  MINIMUM 5 ADET soru-cevap cifti uret. Su niyet turlerini KAPSAYACAK:

  1. BILGI NIYETLI: "X nedir?", "X nasil yapilir?", "X hangi malzemeden uretilir?"
  2. KARSILASTIRMA NIYETLI: "X mi Y mi daha iyi?", "X ile Y arasindaki fark nedir?"
  3. SATIN ALMA NIYETLI: "En uygun fiyatli X nereden alinir?", "X fiyat araligi nedir?"
  4. KULLANIM NIYETLI: "X nasil temizlenir?", "X ile ne giyilir?", "X ne kadar dayanir?"
  5. GUVEN NIYETLI: "X orjinal mi?", "X garanti kapsaminda mi?", "X iade edilebilir mi?"

  Her cevap:
  - Minimum 2 cumle, maksimum 4 cumle
  - Somut ve olgusal (rakam, olcu, sure icersin)
  - Yapay zekanin dogrudan cevap olarak kullanabilecegi kalitede

■ UZUN KUYRUK SORGULAR (uzun_kuyruk_sorgular):
  5-8 adet, Turkce kullanicilarin GERCEKTE aradigi long-tail sorgular.
  Formul: [Niyet] + [Urun Tipi] + [Spesifik Ozellik]
  Ornekler:
  - "kisa boylu kadinlar icin topuklu ayakkabi"
  - "ofise uygun rahat kadin sneaker"
  - "yaz icin nefes alan beyaz spor ayakkabi"
  - "hakiki deri ayakkabi nasil temizlenir"
  - "2024 kadin sneaker modelleri"

══════════════════════════════════════════
ADIM 5: GORSEL SEO ve YAPILANDIRILMIS VERI
══════════════════════════════════════════

■ GORSEL ALT TEXT (gorsel_alt_text):
  Maksimum 125 karakter. Gorseli betimleyen, anahtar kelime iceren dogal cumle.
  Formul: [Marka] + [Urun Tipi] + [Gorunen Ana Ozellik] + [Renk/Detay]
  Ornek: "Lola of Shine hakiki deri beyaz kadin sneaker yan gorunum detay"
  YASAK: "resim", "fotograf", "goruntu" kelimeleri KULLANMA.

■ URUN OZELLIKLERI (urun_ozellikleri):
  Gorselden cikarilan YAPILANDIRILMIS bilgiler. Minimum 5 ozellik:
  {{"ozellik": "Malzeme", "deger": "..."}}
  {{"ozellik": "Renk", "deger": "..."}}
  {{"ozellik": "Stil/Kesim", "deger": "..."}}
  {{"ozellik": "Kullanim Alani", "deger": "..."}}
  {{"ozellik": "Bakim", "deger": "..."}}
  Ek olarak gorselden cikartilabilen her detayi ekle (taban tipi, astar, fermuar vb.)

■ KULLANIM ALANLARI (kullanim_alanlari):
  Urunun kullanilabilecegi senaryolar. Kullanicinin kendini hayal etmesini sagla.
  Ornek: "Gunluk sehir kullanimindan ofis siklisina, hafta sonu gezilerinden arkadaslarla
  bulusmalara kadar her ortamda rahatlikla kullanilabilir."

══════════════════════════════════════════
KALITE KURALLARI (MUTLAKA UY)
══════════════════════════════════════════
1. seo_baslik KESINLIKLE 60 karakter veya ALTINDA olmali. Say ve dogrula.
2. seo_aciklama KESINLIKLE 155 karakter veya ALTINDA olmali. Say ve dogrula.
3. gorsel_alt_text KESINLIKLE 125 karakter veya ALTINDA olmali.
4. Gorselde GORUNMEYEN bir ozellik UYDURMA — goruneni yorumla, gorunmeyeni belirtme.
5. Turkce karakter kullan (ç, ş, ğ, ü, ö, ı) — ozellikle icerik ve aciklamalarda.
6. aciklama alani HTML formatinda olmali (<p>, <h3>, <ul>, <li>, <table>, <strong> vb.)
7. geo_sss minimum 5 adet soru-cevap icermeli.
8. urun_ozellikleri minimum 5 adet ozellik-deger cifti icermeli.
9. uzun_kuyruk_sorgular minimum 5 adet sorgu icermeli.
10. Subjektif superlativlerden kacin: "en iyi", "mukemmel", "essiz" yerine SOMUT ifadeler kullan.

══════════════════════════════════════════
CIKTI FORMATI
══════════════════════════════════════════
Cevabın YALNIZCA ve SALT gecerli bir JSON objesi olmalidir.
Sema disi bir alan veya yorum EKLEME. BUTUN ALANLARI DOLDUR.

{{
    "urun_adi": "...",
    "seo_baslik": "...",
    "seo_aciklama": "...",
    "seo_anahtarkelime": "...",
    "anahtar_kelime": "...",
    "hedef_anahtar_kelime": "...",
    "onyazi": "...",
    "aciklama": "... (HTML formatinda, 5 blok icerik) ...",
    "geo_ozet": "...",
    "geo_sss": [
        {{"soru": "...", "cevap": "..."}},
        {{"soru": "...", "cevap": "..."}},
        {{"soru": "...", "cevap": "..."}},
        {{"soru": "...", "cevap": "..."}},
        {{"soru": "...", "cevap": "..."}}
    ],
    "uzun_kuyruk_sorgular": ["...", "...", "...", "...", "..."],
    "gorsel_alt_text": "...",
    "urun_ozellikleri": [
        {{"ozellik": "Malzeme", "deger": "..."}},
        {{"ozellik": "Renk", "deger": "..."}},
        {{"ozellik": "Stil/Kesim", "deger": "..."}},
        {{"ozellik": "Kullanim Alani", "deger": "..."}},
        {{"ozellik": "Bakim", "deger": "..."}}
    ],
    "kullanim_alanlari": "...",
    "neden_bu_urun": "..."
}}"""

    return prompt


# ──────────────── VISION ENGINE ────────────────

class VisionEngine:
    """
    Google Gemini (Vision) modellerini kullanarak urun gorsellerinden
    yapilandirilmis JSON ciktisi (SEO ve GEO uyumlu) ureten motor sinifi.
    Multi-tenant kullanim icin API anahtari disaridan alinabilir.
    """

    def __init__(self, api_key: str = None) -> None:
        """
        VisionEngine constructor metodu.

        Parametre verilmezse .env dosyasindan okunur (geriye uyumluluk).

        Args:
            api_key (str, optional): Google Gemini API anahtari.
        """
        resolved_key = api_key or os.getenv("GEMINI_API_KEY")
        if not resolved_key:
            raise ValueError("GEMINI_API_KEY eksik. Lutfen parametreyi veya .env dosyasini kontrol edin.")

        genai.configure(api_key=resolved_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-pro",
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.7,
            }
        )

    def analyze_product_image(
        self,
        image_path: str,
        marka: str = "Bilinmeyen Marka",
        adwords_aciklama: str = "",
        adwords_kategori: str = "",
        adwords_tip: str = "",
        breadcrumb_kat: str = "",
        image_paths: list = None,
        mevcut_urun_adi: str = "",
        satisfiyati: str = "",
        kategoriler: str = "",
        stok_kodu: str = "",
        reference_content: str = ""
    ) -> ProductAIContent:
        """
        Verilen urun gorsellerini analiz ederek SEO/GEO/E-E-A-T uyumlu yapilandirilmis icerik uretir.
        Birden fazla gorsel gonderildiginde urunu her acidan analiz eder.

        Args:
            image_path (str): Birincil gorselin yerel dosya yolu (geriye uyumluluk).
            marka (str): Urun markasi.
            adwords_aciklama (str): Mevcut reklam aciklamasi.
            adwords_kategori (str): Mevcut reklam kategorisi.
            adwords_tip (str): Mevcut reklam tipi.
            breadcrumb_kat (str): Sitedeki breadcrumb/kategori bilgisi.
            image_paths (list, optional): Birden fazla gorsel yolu listesi.
            mevcut_urun_adi (str): Urunun mevcut adi (varsa).
            satisfiyati (str): Satis fiyati (varsa).
            kategoriler (str): Urun kategorileri (varsa).
            stok_kodu (str): Stok kodu (varsa).

        Returns:
            ProductAIContent: Pydantic ile valide edilmis urun veri objesi.
        """
        uploaded_files = []
        try:
            # Gorselleri belirle: coklu varsa onu kullan, yoksa tekli
            paths_to_upload = image_paths if image_paths else [image_path]

            # Tum gorselleri Gemini'ye yukle
            for path in paths_to_upload:
                if path and os.path.exists(path):
                    img_file = genai.upload_file(path=path)
                    uploaded_files.append(img_file)

            if not uploaded_files:
                raise ValueError("Yuklenecek gecerli gorsel bulunamadi.")

            gorsel_sayisi = len(uploaded_files)

            # Cok katmanli uzman prompt olustur
            prompt = build_analysis_prompt(
                marka=marka,
                gorsel_sayisi=gorsel_sayisi,
                breadcrumb_kat=breadcrumb_kat,
                adwords_kategori=adwords_kategori,
                adwords_tip=adwords_tip,
                adwords_aciklama=adwords_aciklama,
                mevcut_urun_adi=mevcut_urun_adi,
                satisfiyati=satisfiyati,
                kategoriler=kategoriler,
                stok_kodu=stok_kodu,
            )

            # Prompt + tum gorselleri birlikte gonder
            content_parts = [prompt] + uploaded_files
            response = self.model.generate_content(content_parts)

            # Pydantic ile JSON stringini dogrula ve objeye donustur
            result = ProductAIContent.model_validate_json(response.text)

            return result

        except Exception as e:
            raise RuntimeError(f"Gorsel analizi sirasinda hata olustu: {str(e)}")
        finally:
            # API yuklemelerini temizle (kota yonetimi)
            for f in uploaded_files:
                try:
                    genai.delete_file(f.name)
                except Exception:
                    pass
