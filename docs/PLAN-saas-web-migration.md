# PLAN: Pixra SaaS Web Migration

> **Son güncelleme:** 2026-04-22
> **Durum:** Canlıda — pixra.co (Vercel) + Railway backend

---

## 1. Proje Özeti

Pixra e-ticaret yapay zekasını, çok oyunculu (multi-tenant) bir SaaS formatına taşıyacağız.
- **Mevcut Durum:** ✅ Web SaaS olarak canlıda
- **Stack:** Next.js (Vercel) + FastAPI (Railway) + Supabase + Gemini Vision
- **Hedef:** Ticimax kullanan Türk e-ticaret firmalarına sektör bazlı otomatik SEO/GEO içerik üretimi

---

## 2. Mimari (Tamamlandı ✅)

### Frontend
- Next.js + Tailwind CSS — Vercel'de canlı
- Supabase Auth (email/şifre)
- Kullanıcı: Login → Dashboard → Analiz → Onayla → Ticimax'e Gönder

### Backend (Railway)
- FastAPI — `pixraco-production.up.railway.app`
- Gemini Vision (2-pass: strategy brief + writer)
- Verifier ajan (hallucination kontrolü)
- Ticimax SOAP entegrasyonu (zeep)

### Database
- Supabase PostgreSQL
- RLS ile multi-tenant izolasyon
- Admin key pool (Gemini API anahtarları)

---

## 3. Veritabanı Şeması (Mevcut)

### `organizations`
- id, user_id, company_name, domain_url, ws_kodu, sector_id (YENİ →)

### `ai_sessions`
- id, organization_id, status, total_products, processed_products, job_name, created_at, completed_at, error_message

### `ai_results`
- id, session_id, stok_kodu, urun_adi, status
- ai_urun_adi, ai_seo_baslik, ai_seo_aciklama, ai_aciklama, ai_onyazi
- ai_anahtar_kelime, ai_seo_anahtar_kelime, ai_geo_sss, ai_schema_jsonld
- ai_adwords_aciklama, ai_adwords_kategori, ai_adwords_tip
- ai_ozelalan_1..5, ai_gorsel_alt_tags (JSONB)
- ai_claim_map, ai_information_gain, ai_uyarilar
- original_* alanlar, verifier_report, cost_tl

### `credits`
- user_id, balance

### `gemini_keys` (Admin yönetimli)
- api_key, aktif, created_at

---

## 4. Tamamlanan İşler ✅

### Temel Sistem
- [x] Supabase Auth + RLS kurulumu
- [x] Multi-tenant firma yönetimi
- [x] Analiz session sistemi (polling ile ilerleme)
- [x] Kredi sistemi
- [x] Admin paneli (kullanıcı, kredi, session yönetimi)
- [x] Admin Gemini key pool (birden fazla key, yük dağılımı)

### AI Motoru
- [x] Gemini Vision 2-pass (strategy brief + strategist/writer)
- [x] Verifier ajan (hallucination denetimi + otomatik patch)
- [x] Pydantic JSON output validation
- [x] ozelalan null/validation hatası düzeltildi
- [x] Marka adı ürün adına eklenmemesi (prompt fix)
- [x] Analiz süresi ve maliyet takibi

### Ticimax SOAP Entegrasyonu
- [x] zeep client, HistoryPlugin ile SOAP XML loglama
- [x] WSDL doğrulaması (xsd2 schema analizi)
- [x] SaveUrun flag bug düzeltildi (dinamik filtre kaldırıldı, tüm flagler çalışıyor)
- [x] UrunKartiAyar flag isimleri WSDL ile doğrulandı
- [x] StokKodu WSDL uyumsuzluğu düzeltildi
- [x] Ticimax'e gönderim: UrunAdi, Aciklama, SeoBaslik, SeoAciklama, SeoAnahtarKelime, OnYazi, AdwordsAciklama, AdwordsKategori, AdwordsTip — hepsi çalışıyor ✅
- [x] Görsel alt tag üretimi (Gemini ile, Supabase'e kaydediliyor)
- [x] Görsellere dokunulmuyor (SaveUrun ile görsel güncelleme duplikasyona yol açıyor — devre dışı)

### Frontend
- [x] Session silme (kullanıcı + admin)
- [x] Analiz süresi gösterimi
- [x] Ticimax gönderim onay akışı (3 aşamalı)
- [x] Hata logları admin panelinde görünüyor

---

## 5. Kalan Küçük İşler ⚠️

- [ ] SEO Title 60 karakter limitini Ticimax panelinde doğrula (şu an 203 gösteriyor — muhtemelen Ticimax'in kendi sayma farkı)
- [ ] Strategy brief Pass 1 "atlandı" sorunu (JSON parse hatası — kalite etkiler, kritik değil)
- [ ] Alt tag Ticimax'e gönderimi — SaveUrun dışı bir Ticimax API endpoint araştırılacak
- [ ] llm.txt otomatik üretimi (Sektör RAG ile birlikte gelecek)

---

## 6. SONRAKİ BÜYÜK ADIM: Sektör Bazlı RAG Sistemi 🚀

### Problem
Ticimax'te 50.000+ aktif e-ticaret sitesi var. %90'ı SEO alanlarını boş bırakıyor ya da kopyalıyor. Pixra bu boşluğu dolduruyor — ama şu an sektör körü çalışıyor. İç giyim firması ile elektronik firması için aynı prompt kullanılıyor.

### Vizyon
Her firma kayıt sırasında sektörünü seçer. Sistem o sektör için önceden hazırlanmış 5 katmanlı bir intelligence veritabanından beslenir. AI analizde bu verileri kullanır. Başarılı çıktılar sistemi geri besler — zamanla kendi kendine öğrenen bir yapı.

---

### Mimari

#### Yeni Tablolar (Supabase)

**`sectors` tablosu**
```
id, slug (kadin-ic-giyim | elektronik | mobilya | ...)
display_name, parent_sector_id, aktif
```

**`sector_intelligence` tablosu**
```
id, sector_id
data_type: ENUM(keywords | faq | schema | competitor | seasonal)
content: JSONB          ← asıl bilgi
source: ENUM(admin | auto_crawl | user_feedback)
quality_score: 0-10
updated_at, version
```

#### `organizations` tablosuna eklenir
```
sector_id (FK → sectors)
sub_sector: text (daha spesifik tanım)
hedef_kitle: text
```

---

### 5 Katman — İçerik Yapısı

| Katman | İçerik | Kaynak |
|---|---|---|
| `keywords` | Anahtar kelime kümeleri, arama niyeti (informational/transactional), zorluk skoru | Web crawl + manuel |
| `faq` | Alıcıların sorduğu 20-30 gerçek soru + ideal cevap yapısı | Forum/yorum scraping |
| `schema` | Hangi schema.org markup bu sektörde çalışıyor, örnek yapılar | Rakip analiz |
| `competitor` | Top 5-10 rakibin SEO yaklaşımı, title yapısı, description kalıpları | Otomatik crawl |
| `seasonal` | Hangi ay hangi kelimeler zirve yapıyor, kampanya dönemleri | Google Trends scraping |

---

### Veri Toplama Pipeline

Admin dashboard'dan tetiklenir, background task olarak çalışır:

```
/api/admin/sector/crawl  →  BackgroundTask
1. Google TR'de "{sektör} satın al / fiyat / yorumlar" → top 20 URL
2. Her URL: title, meta desc, h1-h3, FAQ schema, OG tags çek
3. Gemini analiz: keyword clusters, FAQ patterns, schema kalıpları çıkar
4. sector_intelligence tablosuna yaz (source=auto_crawl)
5. quality_score ata (0-10)
```

Dışarıdan API gerekmez — direkt web crawl yeterli.

---

### Prompt Injection

Mevcut `_build_runtime_prompt()` fonksiyonuna sektör bloğu eklenir:

```python
## SEKTÖR İSTİHBARAT VERİSİ — {sector_display_name}

### Bu Sektörde Çalışan Anahtar Kelimeler
{keywords_json}

### Alıcıların Gerçek Soruları (FAQ Kalıpları)
{faq_json}

### Rakip SEO Kalıpları (Top 5 site analizi)
{competitor_patterns}

### Mevsimsel Öncelik ({current_month})
{seasonal_current}
```

---

### Öğrenme Döngüsü

```
Kullanıcı analiz onayladı (decisions = 'approved')
        ↓
Firma'nın sector_id'si alınır
        ↓
Onaylanan çıktıdan pattern extraction:
  - Hangi kelimeler kullanıldı?
  - FAQ yapısı nasıldı?
  - Information gain skoru kaçtı?
  - Verifier kaç uyarı verdi?
        ↓
sector_intelligence güncelle (source=user_feedback)
quality_score artar → yüksek kaliteli patterns önceliklenir
```

---

### llm.txt Otomatik Üretimi

Her firma için `/{domain}/llm.txt` otomatik üretilir:

```
# {firma_adi} — {sektör_adi}
Marka: {company_name}
Uzmanlık: {sector_intelligence.keywords top 5}
Kategoriler: {analiz edilmiş ürünlerin kategorileri}
Öne Çıkan Ürünler: {onaylı çıktıların SEO başlıkları}
İletişim: {domain_url}
```

Perplexity, ChatGPT, Claude gibi AI'lar firmayı araştırırken bu dosyayı görür → citation probability artar.

---

### Sprint Planı

#### Sprint 1 — Altyapı (1 hafta)
- [ ] `sectors` ve `sector_intelligence` tabloları Supabase'e ekle
- [ ] `organizations` tablosuna `sector_id` kolonu ekle
- [ ] Firma kayıt/düzenleme formuna sektör seçimi ekle (zorunlu, 2 kademeli)
- [ ] Admin panelinden manuel sektör verisi girişi (basit CRUD)
- [ ] `analyze_product_image()` fonksiyonuna `sector_intelligence` parametresi ekle
- [ ] Prompt'a sektör injection bloğu ekle

#### Sprint 2 — Otomatik Crawl (1-2 hafta)
- [ ] `/api/admin/sector/crawl` endpoint (BackgroundTask)
- [ ] Web scraping pipeline (requests + BeautifulSoup)
- [ ] Gemini ile içerik analizi + structured extraction
- [ ] Quality score sistemi
- [ ] Admin panelinde crawl tetikleme + durum gösterimi

#### Sprint 3 — Öğrenme Döngüsü + llm.txt (2 hafta)
- [ ] Onaylı çıktılardan feedback extraction
- [ ] `sector_intelligence` güncelleme mekanizması
- [ ] `/api/llm-txt/{organization_id}` endpoint
- [ ] Frontend'de "llm.txt indir/görüntüle" butonu
- [ ] Sektörler arası kalite karşılaştırma (admin dashboard)

---

## 7. Teknik Borç / Bilinen Sınırlamalar

| Konu | Durum | Not |
|---|---|---|
| Alt tag Ticimax'e gönderim | Beklemede | SaveUrun görseli bozuyor; ayrı API araştırılacak |
| Strategy brief Pass 1 skip | Düşük öncelik | JSON parse sorunu, kaliteyi etkiler |
| ozelalan_1..5 gönderimi | Hazır ama test edilmedi | WSDL'de OzelAlan1Guncelle var |
| Varyasyon güncellemesi | Kapsam dışı | Şimdilik sadece ana ürün alanları |

---

## 8. Yayın Bilgileri

| Bileşen | URL | Platform |
|---|---|---|
| Frontend | pixra.co | Vercel |
| Backend | pixraco-production.up.railway.app | Railway |
| Database | zukqlkeecpgcqitlbgma.supabase.co | Supabase |
