"""Pass 1 — Strateji Brifing Promptu.

Gemini Flash Lite ile metin-tabanlı (görselsiz) çalışır.
Maliyet: ~0.005 TL/ürün (pass 2'den 50x ucuz).

Çıktı, Pass 2 (vision/content) promptuna enjekte edilir:
- Yazar "müşteri kim, ne istiyor" sorusuna cevap alınmış şekilde başlar
- İçerik özellik listesinden değil, müşteri ihtiyacından çıkar
- Intent gap'leri önceden tespit edildiği için SSS kalitesi yükselir
"""

STRATEGY_BRIEF_PROMPT = """\
Sen bir e-ticaret dönüşüm stratejisti ve müşteri psikolojisi uzmanısın.
Türkiye e-ticaret sektöründe 10+ yıl deneyiminle ürün sayfası performansını artırıyorsun.

Aşağıdaki ürün için bir **SEO/GEO içerik brifing** hazırla.
Bu brifing, bir içerik yazarına iletilecek — yazar bu brifinge dayanarak
müşteriyi gerçekten ikna eden, yapay zekalar tarafından alıntılanan içerik üretecek.

---

## Ürün Bilgisi
Marka: {marka}
Kategori: {kategori}
Ürün adı: {urun_adi}
Mevcut açıklama: {aciklama}
Fiyat: {fiyat}

---

## Kurallar
- Boş övgü sıfatı KULLANMA ("kaliteli", "harika", "şık" vb.)
- Somut davranışsal gözlem yaz: müşteri ne arar, ne sorar, ne korkar
- Her intent_gap bir gerçek kullanıcı sorusundan gelsin (Google autocomplete / forum analizi gibi düşün)
- conversion_angle tek bir cümle, keskin: "Bu ürünü [X rakibe / Y alternatife] göre tercih ettiren şey..."
- uyarilar kısmında bu kategoride içerik yazarlarının sık yaptığı hataları listele

---

## Çıktı (yalnızca geçerli JSON):
{
  "musteri_profili": "Kısa demografik + psikografik profil. Örn: 28-42 yaş arası çalışan kadın, pratiklik öncelikli, marka değil kalite bakıyor",
  "birincil_jtbd": "Birincil işi-yapma hedefi. Örn: Uzun çalışma saatlerinde sırt ağrısı yaşamadan rahat giyinmek",
  "ikincil_jtbd": "İkincil motivasyon. Örn: Ofis ortamında şık görünmek ama eve yorulmadan gelmek",
  "intent_gaps": [
    "Müşterinin sormak isteyip cevaplanmayan soru 1",
    "Müşterinin sormak isteyip cevaplanmayan soru 2",
    "Müşterinin sormak isteyip cevaplanmayan soru 3"
  ],
  "conversion_angle": "Bu ürünü tercih ettiren tek en güçlü argüman",
  "seo_odak_keyword": "Bu sayfanın hedeflemesi gereken uzun-kuyruk anahtar kelime",
  "rakip_kiyasi": "Bu kategoride insanların genellikle karşılaştığı sorun veya daha ucuz alternatifin eksikliği",
  "uyarilar": [
    "Bu kategoride içerik yazarları sık şunu yapar: ...",
    "Kaçınılacak anlatım tuzağı: ..."
  ]
}
"""


def build_strategy_brief_prompt(
    marka: str,
    kategori: str,
    urun_adi: str,
    aciklama: str,
    fiyat: str,
) -> str:
    return STRATEGY_BRIEF_PROMPT.format(
        marka=marka or "Bilinmiyor",
        kategori=kategori or "Genel",
        urun_adi=urun_adi or "(ürün adı yok)",
        aciklama=(aciklama or "(açıklama yok)")[:800],
        fiyat=fiyat or "belirtilmemiş",
    )
