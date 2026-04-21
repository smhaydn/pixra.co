# PIXRA — Yol Haritası
> Son güncelleme: 2026-04-21 | Yönetici: Claude Code

**Vizyon:** Türk e-ticaret markalarının ürünlerini ChatGPT, Google, Perplexity ve tüm AI motorlarında otomatik görünür ve alıntılanır hale getiren SaaS platform.

---

## Durum Paneli

| Faz | Ad | Durum | ETA |
|-----|----|-------|-----|
| 0 | Temel Altyapı | ✅ Tamamlandı | — |
| 1A | İçerik Kalitesi (SEO+GEO) | ✅ Tamamlandı | 2026-04-21 |
| 1B | AI Görünürlük Katmanı | ✅ Tamamlandı | 2026-04-21 |
| 1C | Test + Canlıya Alma | 🔄 Devam ediyor | Gün 3-4 |
| 2A | Admin + Kullanıcı Paneli | ⏳ Bekliyor | Hafta 2 |
| 2B | Pixra Web Sitesi SEO | ⏳ Bekliyor | Hafta 2 |
| 2C | Reklam Entegrasyonu (Google → Meta) | ⏳ Bekliyor | Hafta 3-4 |
| 3 | Self-hosted LLM (maliyet hesabı sonrası) | 🔬 Araştırma | Ay 2+ |

---

## FAZ 0 — Tamamlanan Altyapı ✅

Bunlar zaten yapıldı, tekrar dokunmaya gerek yok:

- [x] FastAPI backend (`backend/main.py`)
- [x] Next.js 16 + React 19 frontend
- [x] Supabase PostgreSQL (veritabanı + JSONB sütunlar)
- [x] Ticimax SOAP entegrasyonu (zeep)
- [x] Gemini 2.5 Flash vision motoru
- [x] Strategist + Writer prompt sistemi
- [x] Verifier katmanı (deterministik + LLM)
- [x] Pydantic validation (ProductAIContent, 21 alan)
- [x] Claim mapping + Information Gain skorlaması
- [x] Kumaş kompozisyon koruma kuralları
- [x] Session UI (ürün listeleme, onay akışı)
- [x] Adwords alanları Ticimax'a gönderim

---

## FAZ 1A — İçerik Kalitesi: Multi-Pass Engine 🔄

**Problem:** Tek geçişli üretim yüzeysel çıktı veriyor. AI görsel özellikleri listeliyor ama müşteriyi ikna etmiyor, semantik derinlik yok.

**Çözüm: 3-Pass Üretim**

```
Pass 1 — Strateji (yeni)    : Müşteri kim? JTBD nedir? Hangi soru cevaplanmalı?
Pass 2 — Yazım (mevcut)     : Stratejiye göre içerik üret, görüntüden kanıt topla
Pass 3 — Kalite Kontrol     : Verifier + Information Gain + banned phrase check
```

**Kategori Şablonları (zorunlu, karar benim):**

| Kategori | Birincil JTBD | Özel SEO Sinyali |
|----------|---------------|-----------------|
| ic_giyim | Günlük konfor, beden uyumu | "büyük beden", "gece konforu", "dikişsiz" |
| dis_giyim | Tarz + pratiklik | "kombin önerisi", "sezon rengi", "kalıp" |
| ayakkabi | Uzun süre rahatlık | "ortopedik taban", "gerçek deri", "numara" |
| elektronik | Sorun çözme, hız | "batarya ömrü", "uyumluluk", "kurulum" |
| aksesuar | Sosyal anlam | "hediye kutusu", "el yapımı", "evrensel" |

**Dosyalar:**
- `backend/core/prompts/strategist_writer.py` — Pass 1 strategy block eklenecek
- `backend/core/vision_engine.py` — Multi-pass orchestration

**Maliyet etkisi:** +0.02 TL/ürün (Haiku ile Pass 1), toplam ~0.33 TL/ürün

---

## FAZ 1B — AI Görünürlük Katmanı ⏳

Bu özellikler Pixra'yı rakiplerinden ayıran asıl değer önerisini oluşturuyor.

### 1. llms.txt Generator (Gün 2)
**Ne yapar:** Her mağaza için `/llms.txt` dosyası üretir. ChatGPT, Perplexity, Gemini bu dosyayı okur ve mağazayı "güvenilir kaynak" olarak tanır.

**İçerik:**
```
# {Mağaza Adı} — Ürün Kataloğu
> Platform: Pixra | Güncelleme: {tarih}
Kategoriler: {kategori listesi}
Ürün sayısı: {sayı}
Uzman alan: {marka_tanimi}

## Öne Çıkan Ürünler
{top 10 ürün: ad + SEO açıklama}
```

**Endpoint:** `GET /api/llms-txt/{firma_id}` → mağaza sahibi indirip Ticimax root'a upload eder

### 2. Image Alt-Text Pipeline (Gün 2)
**Ne yapar:** Gemini Vision ile her ürün görseline otomatik, semantik açıklamalı alt-text yazar.

**Örnek:**
- Önce: `alt="urun_gorseli_001.jpg"`
- Sonra: `alt="Krem rengi nervürlü pamuklu crop top, düz kesim, fırfırlı yaka detaylı"`

**Entegrasyon:** `vision_engine.py` → `generate_alt_text()` → Ticimax resim metadata güncelleme

### 3. Schema.org Zenginleştirme (Gün 3)
**Ne yapar:** Mevcut schema.org JSON-LD'ye eksik sinyaller ekler.

**Eklenecekler:**
- `dateModified` (E-E-A-T sinyali)
- `brand.founder` + `brand.foundingDate`
- `FAQPage` bloğu (geo_sss'den otomatik)
- `AggregateRating` (Ticimax'tan varsa)

---

## FAZ 1C — Test + Canlıya Alma ⏳

**Test hesabı:** Lola of Shine (lolaofshine.com) — Ticimax, gerçek ürünler

**Test listesi:**
- [ ] 5 ürün multi-pass üretimi → kalite karşılaştırması
- [ ] llms.txt üretimi + doğrulama
- [ ] Alt-text üretimi + Ticimax'a yazma
- [ ] Schema.org validasyonu (Google Rich Results Test)

**Deploy:**
- Frontend → Vercel (pixra.co) — **zorunlu, karar benim ✓**
- Backend → Railway ($5/ay) — **zorunlu, karar benim ✓**
- DB → Supabase (mevcut) — **zorunlu, karar benim ✓**

---

## FAZ 2A — Admin + Kullanıcı Paneli ⏳

### Admin Dashboard (Pixra iç ekibi için)
- Tüm mağazaları görüntüle (firma listesi, durum, son aktivite)
- Ürün üretim istatistikleri (kaç ürün, başarı oranı, maliyet)
- Verifier hata raporları (hangi hatalar kaç kez çıkıyor)
- Manuel override (belirli ürünü elle düzelt)

### Kullanıcı Paneli (Ticimax mağaza sahipleri için)
- Ürünlerinin "AI görünürlük skoru" (1-100)
- ChatGPT/Google/Perplexity'de kaç kez alıntılandı (tahmini)
- SEO performansı timeline
- İçerik onay/red ekranı (mevcut session UI baz alınacak)
- llms.txt indir / yenile butonu

**Teknik:** Mevcut Next.js sayfaları genişletilecek (`/admin`, `/dashboard`, `/analytics`)

---

## FAZ 2B — Pixra Web Sitesi SEO ⏳

pixra.co'nun kendisi de iyi SEO'ya sahip olmalı.

**Hedef kelimeler:**
- "Ticimax SEO otomasyonu"
- "e-ticaret AI içerik üretimi"
- "ChatGPT'de ürün görünürlüğü"
- "GEO optimization Türkiye"

**Yapılacaklar:**
- Landing page (değer önerisi + demo)
- Blog (kategori bazlı SEO rehberleri)
- Pixra'nın kendi llms.txt'i
- Schema.org: Organization + SoftwareApplication

---

## FAZ 2C — Reklam Entegrasyonu ⏳

**Sıra:** Google → Meta → YouTube → Pinterest → TikTok

### Google Ads (İlk)
- Ürün verilerinden otomatik Responsive Search Ad üretimi
- AI: başlık (15 varyant) + açıklama (4 varyant) optimizasyonu
- Performance Max kampanya önerisi
- Entegrasyon: Google Ads API v18

### Meta Ads (İkinci)
- Ürün görseli + AI başlık → otomatik carousel reklam
- Hedef kitle önerisi (kategori bazlı lookalike)
- Entegrasyon: Meta Marketing API

### Sonraki platformlar (3. aşama)
YouTube (Video Ad Script), Pinterest (Product Pin), TikTok (Spark Ad)

---

## FAZ 3 — Self-Hosted LLM Araştırması 🔬

**Karar kriteri:** API maliyeti > sunucu maliyeti olduğunda geçiş mantıklı.

| Seçenek | Model | RAM | Aylık Maliyet | Kalite |
|---------|-------|-----|---------------|--------|
| Gemini API (şimdiki) | Flash 2.5 | — | ~175 TL/500 ürün | Orta |
| RunPod (kiralık GPU) | Llama 3.3 70B | 40GB | ~$30-50/ay | Orta-İyi |
| Hetzner (dedicated) | Mistral 7B fine-tune | 16GB | ~$20/ay | Düşük-Orta |
| Groq API | Llama 70B | — | ~$15/ay | İyi |

**Tavsiye:** Önce Groq API deneyelim (hazır API, Llama 70B, ucuz). Server kiralamayı 2. ay değerlendir.

**Fine-tuning veri seti:** Pixra'nın ürettiği yüksek kaliteli çıktılar (information_gain > 8.0) → eğitim verisi.

---

## Token Bütçesi ve Model Seçimi

**Kural:** Doğru iş için doğru model. Opus'u sadece gerçekten gerektiğinde kullan.

| Görev | Model | Neden |
|-------|-------|-------|
| Mimari karar, brainstorm | Opus 4.7 | Karmaşık muhakeme |
| Kod yazma, debug, refactor | **Sonnet 4.6** | En iyi maliyet/kalite |
| Verifier, basit kontroller | **Haiku 4.5** | Ucuz, hızlı |
| İçerik üretimi (ürün) | Gemini 2.5 Flash | Vision + maliyet |

**Haftalık 5 saat limiti nasıl kullanılır:**
- Oturum başı: `/model sonnet` → kodlama için
- Mimari tartışma varsa: `/model opus`
- Basit task (file edit, grep): Sonnet yeterli

**$20 → $100 ne zaman:** Günlük aktif geliştirme 5 saatten fazlaysa veya faz 2'ye geçince.

---

## Aktif Kararlar

| # | Karar | Kim verdi | Tarih |
|---|-------|-----------|-------|
| 1 | Vercel = frontend hosting | Claude (zorunlu) | 2026-04-21 |
| 2 | Railway = backend hosting ($5/ay) | Claude (zorunlu) | 2026-04-21 |
| 3 | Supabase = veritabanı (mevcut) | Kullanıcı + Claude | 2026-04-21 |
| 4 | Gemini 2.5 Flash = içerik motoru | Claude (zorunlu) | 2026-04-21 |
| 5 | Multi-pass üretim (3 geçiş) | Claude (zorunlu) | 2026-04-21 |
| 6 | Google Ads önce, Meta sonra | Claude (zorunlu) | 2026-04-21 |
| 7 | Self-hosted LLM = bekle, önce Groq dene | Claude (zorunlu) | 2026-04-21 |

---

## Kapsam Dışı (şimdilik)

- Pinterest, TikTok entegrasyonu → Faz 2C sonrası
- Mobil uygulama → hiç gündemde değil
- Çoklu dil desteği (EN/DE) → Faz 3 sonrası
- White-label lisanslama → değerlendir
