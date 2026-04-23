# Pixra — Sistem Mimarisi
> Son güncelleme: 2026-04-23

---

## Genel Bakış

```
Kullanıcı (browser)
     │
     ▼
┌─────────────────────────────────┐
│   Next.js 16 — Vercel (pixra.co)│
│   React 19 + styled-jsx         │
│   Supabase Auth (SSR)           │
└────────────┬────────────────────┘
             │ REST (fetch)
             ▼
┌─────────────────────────────────┐
│   FastAPI — Railway             │
│   Python 3.13                   │
│   Gemini 2.5 Flash Vision       │
│   Ticimax SOAP (zeep)           │
└────────┬────────────────────────┘
         │                  │
         ▼                  ▼
  Supabase PostgreSQL   Ticimax WS API
  (DB + Auth + RLS)    (SOAP/XML)
```

---

## Kullanıcı Rolleri

| Rol | Ne Yapabilir |
|-----|-------------|
| `admin` | Tüm firmalar, impersonation, SectorManager, Gemini key pool |
| `agency` | Kendi altındaki firmaları yönetir |
| `customer` | Tek firma, kendi analizleri |

Rol `profiles` tablosundan okunur. `getEffectiveUser()` fonksiyonu role + impersonation durumunu çözer.

---

## Kritik Veri Akışı: Ürün Analizi

```
1. Kullanıcı /seo/new → "Analiz Başlat" tıklar
          │
          ▼
2. Frontend: POST /api/analyze/start
   Body: { firm_id, organization_id, product_ids[], ... }
          │
          ▼
3. FastAPI main.py → _run_analysis() (arka planda Task)
   a. organization_id varsa → _load_sector_intelligence()
      └── Supabase: organizations → sectors → sector_intelligence
   b. Ticimax'tan ürün verisi çek (ticimax_api.py)
   c. vision_engine.analyze_product_image() çağır
      └── _build_runtime_prompt(sector_intelligence=...)
          ├── base_prompt (genel SEO/GEO kuralları)
          ├── sektor_block (sektöre özel keywords/faq/competitor)
          └── strategy_block + runtime_block
   d. Gemini Vision API → JSON çıktı
   e. verifier.py → deterministik + LLM doğrulama
   f. supabase_sync.py → analysis_products tablosuna kaydet
          │
          ▼
4. Frontend: GET /api/analyze/status/{session_id} (polling)
   → Tamamlanan ürünleri göster
          │
          ▼
5. Kullanıcı onaylar → POST /api/update/ticimax
   → Ticimax SOAP: UpdateProduct (SEO başlık, açıklama, adwords alanları)
```

---

## Kritik Veri Akışı: Sektör RAG

```
Admin Panel → SectorManager
  ├── Sektör seç (sectors tablosu)
  ├── Veri tipi seç (keywords/faq/competitor/seasonal)
  ├── JSON gir → sector_intelligence tablosuna kaydet
  └── quality_score (0-10) belirle

Firma Onboarding / Ayarlar
  └── organization.sector_id → organizations tablosuna kaydet

Analiz sırasında:
  organization_id → sector_id → sector_intelligence rows
  → En yüksek quality_score'lu 50 kayıt
  → Prompt'a enjekte
```

---

## Frontend Sayfa Akışı

```
/login
  └─ başarılı → /onboarding (ilk giriş) veya / (dashboard)

/onboarding
  └─ Step 0: Sektör seç + firma adı
  └─ Step 1: Ticimax WS kodu gir
  └─ Step 2: Test bağlantısı → /

/ (Dashboard)
  ├─ Stats: krediler, toplam analiz, aktif işlem
  ├─ Firma kartı
  └─ Son analizler

/seo
  ├─ Mevcut oturumlar listesi
  └─ "Yeni Analiz" → /seo/new

/seo/new
  └─ Ürünleri seç → analiz başlat → /seo/session/[id]

/seo/session/[id]
  └─ Gerçek zamanlı durum (polling)
  └─ Ürün onay/red ekranı
  └─ Ticimax'a gönder

/admin (admin rolü zorunlu)
  ├─ Tüm müşteriler + impersonation
  ├─ SectorManager
  └─ Gemini key pool yönetimi

/settings
  └─ Firma adı, domain, Ticimax WS kodu, sektör

/credits
  └─ Kredi bakiyesi + paket satın alma
```

---

## Supabase Şeması (özet)

```sql
profiles          (id, user_id, role)
organizations     (id, user_id, company_name, domain_url, ws_kodu,
                   sector_id → sectors, sub_sector, hedef_kitle)
credits           (id, user_id, balance)
analysis_sessions (id, org_id, status, job_name, ...)
analysis_products (id, session_id, product_id, ai_content JSONB,
                   status, information_gain, ...)
sectors           (id, slug, display_name, parent_id, aktif)
sector_intelligence (id, sector_id, data_type ENUM, content JSONB,
                     source ENUM, quality_score, version)
gemini_api_keys   (id, key_hash, usage_count, is_active)
```

**RLS:** Her tablo `user_id` veya `org_id` üzerinden izole. Admin tümünü görür.

---

## Ortam Değişkenleri

### Frontend (`frontend/.env.local`)
```
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
NEXT_PUBLIC_API_URL          → Railway backend URL
```

### Backend (`backend/.env`)
```
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY    → RLS bypass (backend işlemleri için)
GEMINI_API_KEY               → Fallback (DB'deki key pool önce denenir)
```

---

## Bilinen Kısıtlamalar

| Kısıt | Detay |
|-------|-------|
| Ticimax alt-text | Ürün resim metadata güncelleme endpoint'i belirsiz — araştırılacak |
| Ticimax `PromiseLike` | `.finally()` çalışmaz → `.then(ok, err)` kullan |
| styled-jsx dark mode | `dark:` prefix çalışmaz → `[data-theme="dark"] .class` kullan |
| `CREATE TYPE IF NOT EXISTS` | PostgreSQL desteklemiyor → DO $$ EXCEPTION pattern |
| Next.js `middleware` | `proxy` olarak yeniden adlandırılacak (deprecation uyarısı var) |

---

## Performans Notları

- Şu an ürün başına ~44 saniye (seri işlem)
- Hedef: paralel işlem ile 500 ürün < 3 saat
- Gemini API key pool (round-robin) → rate limit aşmayı önler
- Backend Railway'de tek instance — scale gerekince Railway plan yükselt
