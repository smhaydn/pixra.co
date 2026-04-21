# UI Implementation Plan: Pixra SaaS

**Tarih:** 2026-04-18
**Kaynak:** Brainstorm kararları (3 kullanıcı tipi, kredi sistemi, sihir anı)
**Stack:** Next.js 16 App Router + Tailwind v4 + styled-jsx + Supabase

---

## Özet

Mevcut Next.js frontend'i "AI-first e-ticaret büyüme platformu" konumlandırmasına uygun, çok modüllü bir shell etrafında yeniden inşa ediyoruz. SEO/GEO bugün aktif modül, Reklamlar ve Analitik "Yakında" placeholder'ları olarak görünür olacak. Müşteri/Ajans/Admin için 3 farklı UI modu var. Sihir anı: before/after yan yana karşılaştırma ekranı.

---

## Tech Kararları

| Alan | Seçim | Gerekçe |
|---|---|---|
| Style | styled-jsx + CSS variables (mevcut) | Tutarlı, Tailwind v4 ile uyumlu |
| Routing | Next.js App Router | Mevcut kurulum |
| Auth | Supabase (mevcut) | Çalışıyor, değişmiyor |
| State | React useState + SWR (eklenecek) | Kredi bakiyesi polling için |
| Icons | Inline SVG (mevcut) | Bundle tasarrufu |
| Roller | Supabase `user_metadata.role` | `customer` / `agency` / `admin` |

---

## Bilgi Mimarisi (Sitemap)

```
/                           → Dashboard (role-aware)
/login                      → Giriş
/register                   → Kayıt (+10 kredi hook)
/onboarding                 → İlk kurulum (WS kodu rehberi)
/seo                        → SEO Modülü ana sayfası (ürün listesi)
/seo/analyze                → Yeni analiz başlatma
/seo/session/[id]           → Analiz sonuçları (before/after hero)
/seo/session/[id]/product/[sku]  → Tek ürün detayı
/ads                        → Reklamlar (Yakında)
/analytics                  → Analitik (Yakında)
/credits                    → Kredi & paketler
/settings                   → Ayarlar (firma, profil)
/admin                      → Admin operations (sadece admin)
/admin/customers            → Müşteri listesi
/admin/customers/[id]       → Müşteri detay + impersonate
/admin/system               → Sistem sağlığı
```

---

## Rol-Bazlı UI Farklılıkları

| Özellik | Customer | Agency | Admin |
|---|---|---|---|
| Üst nav firma seçici | ❌ (tek firma) | ✅ (kendi portföyü) | ✅ (herkes) |
| /admin erişimi | ❌ | ❌ | ✅ |
| Impersonate | ❌ | ✅ (kendi müşterileri) | ✅ (herkes) |
| Kredi bakiyesi | Kendi | Kendi (ajans hesabı) | Tüm müşterilerin toplamı |
| "Paket Al" CTA | ✅ aktif | ✅ aktif | ❌ gizli |

---

## Tasarım Sistemi (refinement)

Mevcut `globals.css` iyi bir temel — sadece 3 ek yapılacak:

1. **Brand palette zenginleştirme** — tek indigo yerine gradient + accent (sihir anı için)
2. **Tipografi ölçeği tanımlama** — h1/h2/h3/body/caption tokens
3. **Component catalog** — Card, Button, Input, Badge, Progress, EmptyState standart componentler

### Renk Paleti (yeni)

```
Brand Primary:   #6366f1 (indigo - kalıyor)
Brand Accent:    #a855f7 (purple - AI/magic anı için)
Brand Gradient:  linear-gradient(135deg, #6366f1, #a855f7)
Surface 0-4:     mevcut dark scale (kalıyor)
```

---

## Sayfa Bazlı Wireframe'ler

### 1. Login / Register (`/login`)
**Mevcut iyi, sadece bunlar değişecek:**
- Sağ panelde "İlk 10 analiz bizden hediye" rozet
- Register modunda trust signals (müşteri logoları, "Ticimax resmi partner" rozeti)

### 2. Onboarding (`/onboarding`) — **YENİ**
Kayıt sonrası 3 adımlı:
```
Step 1: Hoşgeldin + ne yapacağını anlatan video (30sn)
Step 2: Ticimax WS Kodu gir (sağ panelde video rehber + screenshot)
Step 3: İlk ürünleri çek → otomatik analiz başlat
```
**Kritik:** Step 2'de drop'u önlemek için "Yardım Lazım" WhatsApp butonu sağ altta sabit.

### 3. Ana Shell (Her sayfada)
```
┌──────────────────────────────────────────────────┐
│ Header: Logo | Firma Seç (sadece admin/agency) | │
│         💎 1,247 analiz kredisi | 👤 User menu   │
├──────┬───────────────────────────────────────────┤
│ Nav  │  Content Area                             │
│      │                                           │
│ 🏠 Dashboard                                     │
│ ✨ SEO & İçerik    ← aktif                       │
│ 📊 Reklamlar (Yakında)                           │
│ 📈 Analitik (Yakında)                            │
│ 💎 Krediler                                      │
│ ⚙️ Ayarlar                                       │
│                                                  │
│ [admin only]                                     │
│ 👑 Admin Panel                                   │
└──────┴───────────────────────────────────────────┘
```

### 4. Dashboard (`/`)
Rol-aware hero + stats + hızlı erişim:
- **Customer:** "Merhaba [firma]. Bu ay [X] ürün analiz ettin. [Y] kredi kaldı."
- **Agency:** Firma portföyü tablosu
- **Admin:** "[N] aktif müşteri, [M] bugünkü analiz, [Z] sistem sağlığı"

Hero altında:
- Son analizler (3 kart)
- "Yeni Analiz Başlat" CTA butonu (büyük)
- Kredi durumu mini-grafik

### 5. SEO Modülü (`/seo`)
Ürün listesi + filtre + toplu seç + analiz başlat. Tabloya alternatif kart görünüm.

### 6. **Sihir Anı: Session Sonuç Ekranı (`/seo/session/[id]`)**

```
┌─────────────────────────────────────────────────────┐
│ ← Geri    [Session Adı]        Toplam: 47 ürün      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  📊 Özet:                                           │
│  ✓ 47/47 başarılı  |  ⏱ 8 dk 34 sn  |  💎 47 kredi │
│                                                     │
├─────────────────────────────────────────────────────┤
│  [Ürün 1/47]     < prev   next >                    │
│                                                     │
│  ┌─── ÖNCEDEN ──────┐   ┌─── SONRA (AI) ─────┐     │
│  │ Başlık:          │   │ Başlık: ✨          │     │
│  │ "Çanta Siyah"    │   │ "Kadın Deri Omuz    │     │
│  │                  │   │  Çantası - Siyah"   │     │
│  │ Desc: (boş)      │   │ Desc: "Şık tasarım..│     │
│  │                  │   │  (155 char)"         │     │
│  │ Keywords: —      │   │ Keywords: çanta,..." │     │
│  └──────────────────┘   └──────────────────────┘     │
│                                                     │
│  [✓ Onayla & Gönder]  [Reddet]  [AI'dan Yeniden İste]│
├─────────────────────────────────────────────────────┤
│  Toplu işlem: [✓ Hepsini Onayla ve Ticimax'e Gönder]│
└─────────────────────────────────────────────────────┘
```

**Bu ekran pazarlamanın %80'i.** Demo videosunun kahramanı bu.

### 7. Krediler (`/credits`)
```
Mevcut bakiye: 1,247 analiz (büyük)
Geçmiş harcama grafiği (son 30 gün)

[Paketler]
┌────────────┐  ┌────────────┐  ┌────────────┐
│ Başlangıç  │  │ Pro ⭐      │  │ Ajans      │
│ 500 analiz │  │ 2,500       │  │ 10,000     │
│ 29 ₺       │  │ 119 ₺       │  │ 399 ₺      │
│ 0.06/analiz│  │ 0.048       │  │ 0.040      │
│ [Satın Al] │  │ [Satın Al] │  │ [Satın Al] │
└────────────┘  └────────────┘  └────────────┘

Not: Satın alma Phase 2 — şimdilik "İlgilendim" waitlist
```

### 8. Admin Operations (`/admin`)
- KPI kartları: toplam kullanıcı, aktif analiz, MRR (planlanan), sistem uptime
- Müşteri listesi: arama + filtre + her satırda "Impersonate" butonu
- Sistem logları (son hatalar, uyarılar)
- Manuel kredi ekleme formu (hediye veya destek)

---

## Görev Listesi

### 🔵 Aşama 1: Temel (Paralel çalışmaz)

- [ ] **T1:** Design token refinement → `globals.css` güncelle
  - Brand gradient, tipografi ölçeği, 2 accent renk
  - Bağımlılık: Yok
  - Test: Tüm sayfalar hâlâ çalışıyor
  - **[CHECKPOINT]**

- [ ] **T2:** Paylaşılan `AppShell` componenti → `src/components/AppShell.tsx`
  - Sidebar + Header + main content wrapper
  - Role-aware (user metadata'dan rol çeker)
  - Kredi bakiyesi header'da gösterilir (SWR polling)
  - Bağımlılık: T1
  - **[RISK]** (tüm sayfaları değiştirecek)

- [ ] **T3:** Component katalog → `src/components/ui/`
  - Button, Card, Badge, EmptyState, Progress, Modal, Toast
  - Mevcut inline CSS'lerden çıkar, paylaşılan yap
  - Bağımlılık: T1

### 🟡 Aşama 2: Çekirdek sayfalar (T2 bitince paralel)

- [ ] **T4:** Dashboard yenile → `src/app/page.tsx` + `dashboard.tsx`
  - Rol-aware hero
  - Son analizler kartı
  - Hızlı eylem CTA
  - Kredi durumu widget
  - Bağımlılık: T2, T3

- [ ] **T5:** SEO Modülü → `src/app/seo/page.tsx` (YENİ)
  - Ürün listesi (tablo + kart toggle)
  - Filtre/arama
  - Toplu seçim → analiz başlat
  - Bağımlılık: T2, T3
  - **[PARALLEL]** T4 ile

- [ ] **T6:** Session sonuç ekranı → `src/app/seo/session/[id]/page.tsx` (YENİ)
  - Before/After yan yana kart
  - Ürün-ürün gezinme (prev/next)
  - Onay/reddet/yeniden-iste butonları
  - Toplu onay
  - Bağımlılık: T2, T3
  - **[RISK] [CHECKPOINT]** — sihir anı, dikkatle yapılmalı

- [ ] **T7:** Onboarding akışı → `src/app/onboarding/page.tsx` (YENİ)
  - 3 adım wizard
  - WS kodu video rehberi
  - WhatsApp destek butonu
  - Bağımlılık: T2, T3

### 🟢 Aşama 3: Destek sayfaları

- [ ] **T8:** Krediler sayfası → `src/app/credits/page.tsx` (YENİ)
  - Bakiye + grafik
  - Paket kartları (3'lü)
  - "İlgilendim" waitlist (ödeme Phase 2)
  - Bağımlılık: T2, T3
  - **[PARALLEL]**

- [ ] **T9:** Ayarlar → `src/app/settings/page.tsx` (YENİ)
  - Profil
  - Firma bilgileri (WS kodu, domain)
  - Fatura bilgileri (Phase 2 placeholder)
  - Bağımlılık: T2, T3
  - **[PARALLEL]**

- [ ] **T10:** Admin panel → `src/app/admin/*` (YENİ)
  - Dashboard, müşteri listesi, sistem sağlığı, impersonate
  - Rol middleware kontrolü
  - Bağımlılık: T2, T3
  - **[PARALLEL]**

- [ ] **T11:** "Yakında" sayfaları → `src/app/ads/page.tsx`, `src/app/analytics/page.tsx`
  - Basit coming-soon + waitlist input
  - Bağımlılık: T2
  - **[PARALLEL]**

### 🟠 Aşama 4: Legacy temizlik

- [ ] **T12:** `src/app/firm/[id]/` route'unu kaldır → artık tek firma sistemi
  - Data migration stratejisi: Supabase'da organization'ları user'a 1:1 bind et
  - Bağımlılık: T4, T5 bitince
  - **[BREAKING]**

---

## Risk Listesi

| Risk | Olasılık | Etki | Önlem |
|---|---|---|---|
| AppShell tüm sayfaları kırar | Yüksek | Yüksek | Branch'te yap, sayfa-sayfa migrate et |
| Rol yönetimi karmaşıklaşır | Orta | Orta | Supabase RLS + user_metadata.role basit tutulmalı |
| Before/After data yapısı backend ile uyumsuz | Orta | Yüksek | Backend response şemasını önce kontrol et |
| Onboarding video çekilmedi | Yüksek | Orta | Placeholder animation ile başlat, video sonra eklenir |

---

## Karar Bekleyen Noktalar

- [ ] Ajans müşteri davet akışı nasıl olacak? (Agency tipi user bir müşteri firma ekleyebilmeli mi?)
- [ ] Kredi paylaşımı: Ajans kendi kredisini müşterilerine mi paylaştırır?
- [ ] Ödeme entegrasyonu hangi sağlayıcı? (Iyzico / Stripe)
- [ ] Waitlist nereye kaydedilecek? (Supabase yeni tablo mu?)

---

## Sıradaki Adım

1. ✅ Plan yazıldı — bu dosya
2. → T1 başla (design token refinement)
3. → T2 (AppShell) — sonra T3-T11 paralel gidebilir
