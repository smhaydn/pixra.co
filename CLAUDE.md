# Pixra — Claude Code Kılavuzu

> Bu dosya her konuşmada otomatik yüklenir. Kısa ve öz tut — token bütçesi kritik.

---

## Proje Nedir?

**Pixra** — Ticimax altyapısındaki e-ticaret firmalarına AI destekli SEO/GEO içerik üretimi sunan çok kiracılı (multi-tenant) SaaS platformu.

**Stack:**
- Frontend: Next.js 16 + React 19 + styled-jsx + Tailwind v4 → **Vercel** (pixra.co)
- Backend: FastAPI (Python) + Gemini 2.5 Flash Vision → **Railway**
- DB / Auth: Supabase (PostgreSQL + Row Level Security)
- E-ticaret entegrasyon: Ticimax SOAP API (zeep)

---

## Dosya Haritası (nerede ne var)

### Frontend — `frontend/src/`
```
app/
  page.tsx               → Dashboard (ana sayfa, server component)
  dashboard.tsx          → Dashboard içeriği (client component)
  layout.tsx             → Root layout, font yükleme, globals.css import
  globals.css            → TÜM CSS token'ları (renk, tipografi, spacing, animasyon)
  seo/
    page.tsx             → SEO oturum listesi
    seo-client.tsx       → SEO oturum UI
    new/                 → Yeni analiz başlatma
    session/[id]/        → Analiz detay + onay ekranı
  admin/
    page.tsx             → Admin panel (server)
    admin-client.tsx     → Admin UI (müşteri yönetimi + SectorManager)
  onboarding/            → Firma kaydı + sektör seçimi
  settings/              → Firma ayarları + sektör güncelleme
  credits/               → Kredi paketi satın alma
  auth/ login/ ...       → Supabase auth sayfaları

components/
  shell/
    AppShell.tsx         → Sayfa iskelet (Sidebar + TopBar + içerik)
    Sidebar.tsx          → Sol navigasyon (sabit 240px)
    TopBar.tsx           → Üst bar (firma etiketi, dark mode, kredi, kullanıcı menüsü)
    ImpersonateBanner.tsx→ Admin impersonation uyarı şeridi
  ui/
    Button.tsx Badge.tsx Card.tsx Progress.tsx
    Input.tsx Modal.tsx Toast.tsx EmptyState.tsx
    index.ts             → Toplu export
```

### Backend — `backend/`
```
main.py                  → FastAPI app, tüm endpoint'ler, AnalyzeRequest modeli
core/
  vision_engine.py       → Gemini Vision çağrısı, prompt build, sector injection
  ticimax_api.py         → Ticimax SOAP client (ürün çekme + yazma)
  verifier.py            → Çıktı doğrulama (deterministik + LLM)
  supabase_sync.py       → Supabase'e sonuç kaydetme
  helpers.py             → Yardımcı fonksiyonlar, retry
  prompts/
    strategist_writer.py → Ana SEO/GEO prompt şablonu
    strategy_brief.py    → Pass 1 strateji prompt'u
    verifier.py          → Verifier prompt'u
```

### Supabase Tabloları (kritikler)
| Tablo | Ne İçin |
|-------|---------|
| `organizations` | Firma kaydı, `sector_id`, `hedef_kitle` |
| `credits` | Kullanıcı başına kredi bakiyesi |
| `analysis_sessions` | Analiz oturumları |
| `analysis_products` | Ürün başına sonuçlar (JSONB) |
| `sectors` | 16 sektör tanımı |
| `sector_intelligence` | Sektöre özel keywords/faq/competitor (JSONB) |
| `gemini_api_keys` | API key pool (round-robin) |
| `profiles` | Kullanıcı rolü (customer / agency / admin) |

---

## Deploy Workflow

```bash
# Değişiklik yap → commit → push → Vercel otomatik deploy eder (~2-3 dk)
git add frontend/src/... backend/...
git commit -m "feat: açıklama"
git push
# ↑ Bu kadar. Vercel GitHub hook'u ile otomatik tetiklenir.

# Acil / test deploy gerekirse:
cd frontend && vercel deploy --prod
```

**⚠️ Backend (Railway) ayrı:** Railway deploy için Railway dashboard'dan manuel trigger veya Railway CLI.

---

## Kod Yazma Kuralları

### Her zaman geçerli
- Dosya değiştirmeden önce `Read` ile oku — asla tahmin etme
- `styled-jsx` kullan, Tailwind utility class **kullanma** (renk, spacing için)
- CSS token: `var(--brand-primary)`, `var(--surface-2)` vb. — hardcode hex/renk ismi yasak
- TypeScript strict — `any` kullanma, tip tanımla
- `console.log` bırakma — production'da kalır
- API anahtarı asla koda gömme → `.env.local` / `.env`

### Frontend kalıpları
- Server component → veri çekme (Supabase server client)
- Client component (`'use client'`) → etkileşim, state, useEffect
- Yeni UI bileşeni eklemeden önce `components/ui/` içine bak, mevcut varsa kullan
- Renk/spacing için `globals.css` token'larını kullan

### Backend kalıpları
- Yeni endpoint → `main.py`'ye ekle, Pydantic model tanımla
- Supabase sorguları → `supabase_sync.py` veya direkt `httpx` (REST)
- Gemini çağrısı → `vision_engine.py` üzerinden
- Her dış çağrı try/except ile sar

---

## Token Tasarrufu Kuralları

1. **Büyük dosyaları kısmen oku:** `Read(offset=100, limit=50)` — tüm dosyayı okuma
2. **Arama için Grep kullan:** Sembol/fonksiyon bulmak için `grep` değil `Grep` tool
3. **Glob ile dosya bul:** `find` yerine `Glob("**/pattern")`
4. **Bağımlılık kontrolü:** Import değişikliği öncesi `Grep` ile nerelerde kullanıldığına bak
5. **Tek seferlik okuma:** Aynı dosyayı iki kez okuma — Edit tool zaten son hali takip eder
6. **Agent ile araştır:** Geniş kapsamlı araştırma gereken durumlarda `Agent` tool kullan

---

## Sık Yapılan Hatalar (yapma)

- `admin-client.tsx`'te `.finally()` kullanma → `PromiseLike` desteklemiyor, `.then(ok, err)` kullan
- `styled-jsx` içinde Tailwind `dark:` prefix çalışmaz — `[data-theme="dark"] .class` kullan
- Supabase migration'da `CREATE TYPE IF NOT EXISTS` yok → `DO $$ BEGIN ... EXCEPTION WHEN duplicate_object THEN NULL; END $$;` kullan
- `vercel deploy` frontend root'undan çalıştır (`cd frontend && vercel deploy --prod`)

---

## .agent Klasörü

Detaylı rehberler için ihtiyaç halinde oku (token harcamadan önce karar ver):

| Dosya | Ne Zaman Oku |
|-------|-------------|
| `.agent/ARCHITECTURE.md` | Sistem mimarisini anlamak, veri akışını görmek için |
| `.agent/SCOPE-ticimax-seo-saas.md` | Kapsam kararı vermek, ne yapıp yapmayacağına karar vermek için |
| `.agent/agents/backend-dev.md` | Backend endpoint/DB tasarımı yapacaksan |
| `.agent/agents/frontend-dev.md` | Yeni sayfa/bileşen tasarımı yapacaksan |
| `.agent/agents/designer.md` | UI/UX kararı vereceksen |
| `.agent/rules/code-quality.md` | Büyük refactor öncesi |
| `.agent/skills/architecture-review/SKILL.md` | Yeni servis veya büyük mimari değişiklik öncesi |

---

## Aktif Kararlar (değiştirme)

| Karar | Sebep |
|-------|-------|
| styled-jsx, Tailwind utility yok | CSS token sistemi tutarlılığı |
| `[data-theme="dark"]` ile dark mode | SSR uyumlu, localStorage persist |
| Supabase REST (httpx), ORM yok | Backend bağımlılığı azalt |
| Gemini 2.5 Flash, Claude değil | Vision + maliyet (0.10 TL/ürün hedefi) |
| Railway backend, Vercel frontend | Ayrı scale, ayrı fiyat |
