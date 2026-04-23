# PIXRA — Yol Haritası
> Son güncelleme: 2026-04-23 | Yönetici: Claude Code

**Vizyon:** Türk e-ticaret markalarının ürünlerini ChatGPT, Google, Perplexity ve tüm AI motorlarında otomatik görünür ve alıntılanır hale getiren SaaS platform.

---

## Durum Paneli

| Faz | Ad | Durum | Tamamlandı |
|-----|----|-------|------------|
| 0 | Temel Altyapı | ✅ Tamamlandı | 2026-04-21 |
| 1 | Frontend + Admin Panel | ✅ Tamamlandı | 2026-04-22 |
| 2 | Design System v3 (Warm Amber) | ✅ Tamamlandı | 2026-04-22 |
| 3 | Sektör RAG Sistemi — Sprint 1 (Altyapı) | ✅ Tamamlandı | 2026-04-23 |
| 4 | Vercel Auto-Deploy | ✅ Tamamlandı | 2026-04-23 |
| 5 | Sektör RAG — Sprint 2 (Otomatik Tarama) | ⏳ Sırada | — |
| 6 | İçerik Kalitesi İyileştirmesi (Multi-Pass) | ⏳ Sırada | — |
| 7 | AI Görünürlük Katmanı (llms.txt, Alt-text) | ⏳ Sırada | — |
| 8 | Reklam Entegrasyonu (Google → Meta) | ⏳ Bekliyor | — |
| 9 | Pixra Web Sitesi SEO + Landing Page | ⏳ Bekliyor | — |

---

## ✅ FAZ 0 — Temel Altyapı (Tamamlandı)

- [x] FastAPI backend (`backend/main.py`)
- [x] Next.js 16 + React 19 frontend
- [x] Supabase PostgreSQL (veritabanı + JSONB)
- [x] Ticimax SOAP entegrasyonu (zeep)
- [x] Gemini 2.5 Flash vision motoru
- [x] Strategist + Writer prompt sistemi
- [x] Verifier katmanı (deterministik + LLM)
- [x] Pydantic validation (ProductAIContent, 21 alan)
- [x] Claim mapping + Information Gain skorlaması
- [x] Session UI (ürün listeleme, onay akışı)
- [x] Adwords alanları Ticimax'a gönderim

---

## ✅ FAZ 1 — Frontend + Admin Panel (Tamamlandı)

- [x] Sidebar navigasyon (Dashboard, SEO & İçerik, Reklamlar, Analitik, Krediler, Ayarlar)
- [x] AppShell layout (sabit sidebar 240px + TopBar)
- [x] TopBar (firma etiketi, kredi hap, kullanıcı menüsü)
- [x] Dark mode toggle (ay/güneş ikonu, localStorage'a kaydeder)
- [x] Admin Panel (`/admin`) — müşteri yönetimi, impersonation
- [x] Dashboard (`/`) — stats kartları, firma kartı, son analizler
- [x] SEO sayfası (`/seo`) — ürün analizi başlatma, session takibi
- [x] Krediler sayfası (`/credits`)
- [x] Ayarlar sayfası (`/settings`)
- [x] Onboarding akışı (`/onboarding`) — firma kaydı, sektör seçimi
- [x] Supabase Auth entegrasyonu (login, şifre sıfırlama)
- [x] Impersonation sistemi (admin başka kullanıcı olarak giriş)
- [x] Gemini API key pool (round-robin, admin panelinden yönetim)

---

## ✅ FAZ 2 — Design System v3 (Tamamlandı)

**Eski tema:** Koyu mor/indigo (`:root` dark-by-default)  
**Yeni tema:** Warm Light (krem) + Espresso Dark (kahverengi koyu)  
**Font:** Plus Jakarta Sans  
**Brand renk:** Amber `#B45309` / `#D97706`

- [x] `globals.css` — CSS token sistemi (surface, border, brand, semantic, typography, spacing, radius, shadow, motion)
- [x] `[data-theme="dark"]` — espresso koyu tema
- [x] Tüm UI bileşenleri CSS değişkeni kullanıyor (Button, Badge, Card, Progress, Input, Modal, Toast)
- [x] Sidebar warm amber active state
- [x] Yeni Pixra logo SVG'leri (`brand-mark-gradient.svg`, `logo-full.svg`)
- [x] Dark mode toggle → `document.documentElement.dataset.theme` + `localStorage`
- [x] Vercel deploy (pixra.co) + GitHub auto-deploy bağlantısı

---

## ✅ FAZ 3 — Sektör RAG Sistemi Sprint 1 (Tamamlandı)

**Problem:** Tüm firmalar için tek tip prompt → yüzeysel, jenerik çıktılar.  
**Çözüm:** Firma sektörüne göre özelleşmiş AI bilgi tabanı → prompt'a enjekte edilir.

### Veritabanı (Supabase)
- [x] `sectors` tablosu — 16 başlangıç sektörü (kadın iç giyim, elektronik, mobilya vb.)
- [x] `sector_intelligence` tablosu — sektöre özel keywords, faq, competitor, seasonal verisi (JSONB)
- [x] `sector_data_type` enum: `keywords | faq | schema | competitor | seasonal`
- [x] `sector_source` enum: `admin | auto_crawl | user_feedback`
- [x] `organizations` tablosuna `sector_id`, `sub_sector`, `hedef_kitle` eklendi
- [x] RLS politikaları, indexler, auto-update trigger

### Backend
- [x] `_load_sector_intelligence(organization_id)` — Supabase'den sektör verisini çeker
- [x] `vision_engine.py` → `_build_runtime_prompt()` — sektör bloğunu prompt'a enjekte eder
- [x] `AnalyzeRequest` modeline `organization_id` eklendi
- [x] Sektör verisi yoksa genel prompt kullanılır (graceful fallback)

### Frontend
- [x] Onboarding Step 0 — sektör seçim grid'i (pill-style radio)
- [x] Ayarlar sayfası — sektör dropdown
- [x] Admin Panel — `SectorManager` bileşeni (sektör seç, veri ekle/sil, JSON şablonları)
- [x] Yeni analiz başlatma → `organization_id` API'ye gönderilir

---

## ⏳ FAZ 4 — Sektör RAG Sprint 2: Otomatik Tarama (Sırada)

**Hedef:** Admin manuel veri girmek yerine, sistem sektöre ait web sayfalarını tarayarak `sector_intelligence` tablosunu otomatik doldursun.

### Yapılacaklar
- [ ] `POST /api/admin/sector/crawl` endpoint
- [ ] Web scraping pipeline (httpx + BeautifulSoup veya Firecrawl)
- [ ] Kaynak URL listesi per sektör (büyük e-ticaret siteleri, blog, forum)
- [ ] Extracted veriyi `sector_intelligence`'a kaydetme (auto_crawl source)
- [ ] Quality score otomatik hesaplama
- [ ] Admin panelden "Taramayı Başlat" butonu

**Teknik dosyalar:**
- `backend/core/sector_crawler.py` (yeni)
- `backend/main.py` → yeni endpoint
- `frontend/src/app/admin/admin-client.tsx` → crawl butonu

---

## ⏳ FAZ 5 — İçerik Kalitesi İyileştirmesi (Sırada)

**Problem:** Mevcut tek geçişli üretim yüzeysel çıktı veriyor. Başlık/açıklama jenerik, GEO içerikleri zayıf.

### A — Multi-Pass Üretim (3 geçiş)

```
Pass 1 — Strateji   : Müşteri kim? JTBD nedir? Hangi soru cevaplanmalı?
Pass 2 — Yazım      : Stratejiye göre içerik üret, görüntüden kanıt topla
Pass 3 — Kalite     : Verifier + Information Gain + banned phrase check
```

### B — Kategori Bazlı Şablonlar

| Kategori | Birincil JTBD | Özel SEO Sinyali |
|----------|---------------|-----------------|
| ic_giyim | Günlük konfor, beden uyumu | "büyük beden", "gece konforu", "dikişsiz" |
| dis_giyim | Tarz + pratiklik | "kombin önerisi", "sezon rengi", "kalıp" |
| ayakkabi | Uzun süre rahatlık | "ortopedik taban", "gerçek deri", "numara" |
| elektronik | Sorun çözme, hız | "batarya ömrü", "uyumluluk", "kurulum" |
| aksesuar | Sosyal anlam | "hediye kutusu", "el yapımı", "evrensel" |

### C — Prompt Mühendisliği İyileştirmeleri
- Chain-of-thought reasoning
- E-E-A-T sinyalleri (deneyim, uzmanlık, güven)
- Semantik zenginlik kontrolü
- 2026 GEO standartları (AI motorları için FAQ blokları)

**Teknik dosyalar:**
- `backend/core/prompts/strategist_writer.py`
- `backend/core/vision_engine.py`

---

## ⏳ FAZ 6 — Sektör RAG Sprint 3: Öğrenme Döngüsü (Sırada)

**Hedef:** Kullanıcı onayladığı çıktılardan sistem kendi kendine öğrensin.

- [ ] Onaylanan çıktılardan keyword/pattern extraction
- [ ] `sector_intelligence` tablosuna `user_feedback` source ile kayıt
- [ ] Kalite skoru güncelleme mekanizması
- [ ] "Bu içerik işe yaramadı" geri bildirim butonu

---

## ⏳ FAZ 7 — AI Görünürlük Katmanı (Bekliyor)

### 1. llms.txt Generator
**Ne yapar:** Her mağaza için `/llms.txt` üretir. ChatGPT, Perplexity, Gemini bu dosyayı okur.

```
# {Mağaza Adı} — Ürün Kataloğu
> Platform: Pixra | Güncelleme: {tarih}
Kategoriler: {kategori listesi}
## Öne Çıkan Ürünler
{top 10 ürün: ad + SEO açıklama}
```

**Endpoint:** `GET /api/llms-txt/{firma_id}`

### 2. Image Alt-Text Pipeline
**Ne yapar:** Gemini Vision ile ürün görsellerine semantik alt-text yazar.
- Önce: `alt="urun_001.jpg"`
- Sonra: `alt="Krem nervürlü pamuklu crop top, düz kesim, fırfırlı yaka"`

**Not:** Ticimax'ta alt-text için farklı bir endpoint gerekiyor — araştırılacak.

### 3. Schema.org Zenginleştirme
- `FAQPage` bloğu (geo_sss'den otomatik)
- `dateModified` (E-E-A-T sinyali)
- `AggregateRating` (Ticimax'tan varsa)

---

## ⏳ FAZ 8 — Reklam Entegrasyonu (Bekliyor)

**Sıra:** Google Ads → Meta Ads → YouTube → Pinterest → TikTok

### Google Ads
- Ürün verilerinden otomatik Responsive Search Ad
- Başlık (15 varyant) + açıklama (4 varyant)
- Google Ads API v18

### Meta Ads
- Ürün görseli + AI başlık → otomatik carousel reklam
- Meta Marketing API

---

## ⏳ FAZ 9 — Pixra Web Sitesi SEO (Bekliyor)

pixra.co'nun kendisi de iyi SEO'ya sahip olmalı.

**Hedef kelimeler:** "Ticimax SEO otomasyonu", "e-ticaret AI içerik üretimi", "ChatGPT'de ürün görünürlüğü"

- [ ] Landing page (değer önerisi + demo)
- [ ] Blog (kategori bazlı SEO rehberleri)
- [ ] Pixra'nın kendi llms.txt'i
- [ ] Schema.org: Organization + SoftwareApplication

---

## Teknik Kararlar

| # | Karar | Tarih |
|---|-------|-------|
| 1 | Vercel = frontend hosting (pixra.co) | 2026-04-21 |
| 2 | Railway = backend hosting ($5/ay) | 2026-04-21 |
| 3 | Supabase = veritabanı | 2026-04-21 |
| 4 | Gemini 2.5 Flash = içerik motoru | 2026-04-21 |
| 5 | Multi-pass üretim (3 geçiş) | 2026-04-21 |
| 6 | Google Ads önce, Meta sonra | 2026-04-21 |
| 7 | Sektör bazlı RAG sistemi (Sprint yaklaşımı) | 2026-04-23 |
| 8 | Warm amber design system v3 | 2026-04-22 |
| 9 | GitHub → Vercel auto-deploy | 2026-04-23 |

---

## Aktif Sorunlar / Notlar

- `middleware` → `proxy` deprecation uyarısı var (Next.js 16) — kritik değil, ileride düzeltilecek
- Sektör RAG verisi henüz boş — Sprint 2 (crawler) tamamlanana kadar Admin'den manuel girilmeli
- Alt-text için Ticimax'ın ürün resim güncelleme endpoint'i araştırılacak

---

## Kapsam Dışı (şimdilik)

- Pinterest, TikTok entegrasyonu → Faz 8 sonrası
- Mobil uygulama → gündemde değil
- Çoklu dil desteği (EN/DE) → Faz 9 sonrası
- White-label lisanslama → değerlendir
- Self-hosted LLM → API maliyeti > sunucu maliyeti olduğunda değerlendir (önce Groq API dene)
