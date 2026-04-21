# PLAN: Pixra SaaS Web Migration

## 1. Proje Özeti
Pixra e-ticaret yapay zekasını, çok oyunculu (multi-tenant) bir SaaS formatına taşıyacağız. 
- **Mevcut Durum:** Masaüstü PyQt6 uygulaması (Local Python işlemleri).
- **Hedef:** `www.pixra.com` alan adında çalışan, Supabase veritabanıyla kullanıcıları yöneten, Vercel üzerinden yayınlanan web tabanlı bir SAAS uygulaması.

---

## 2. Mimari Kararları (Architecture)

### 🖥️ Frontend (Arayüz)
- **Teknoloji:** Next.js (React) + Tailwind CSS + Shadcn UI
- **Hosting:** Vercel
- **Görev:** Kullanıcı girişi (Supabase Auth), firma ekleme-yönetme masası, interaktif ürün tabloları (Update/Create ekranları), analiz raporları ve indirme aşamaları.

### 🗄️ Database & Auth (Veritabanı ve Kimlik Doğrulama)
- **Teknoloji:** Supabase (PostgreSQL)
- **Modüller:**
  - `Supabase Auth`: Müşterilere (Ticimax partnerlerine) özel üyelik sistemi.
  - `PostgreSQL`: Oturumlar, analiz sonuçları, firma API anahtarları saklanacak.
- **Güvenlik:** RLS (Row Level Security) ile her müşteri kendi firmasının datasını ve API keyini (şifrelenmiş) görecek.

### ⚙️ Backend (Python Mikroservisi)
- **Teknoloji:** FastAPI (Python)
- **Görev:** `vision_engine.py`, `ticimax_api.py`, ve Gemini etkileşimleri burada çalışacak.
- **Kritik Durum (Socratic Check 1):** Vercel API rotaları, uzun süren analizlerde (örneğin 200 ürün analizi 30 dakika sürebilir) zaman aşımına (Timeout) uğrar. Bu yüzden, arka plan işlemcisini (AI Python kodları) **Railway** veya **Render** gibi bir platforma ayrı bir servis (Worker) olarak yüklemeliyiz.

---

## 3. Veritabanı Şeması (Supabase)

### `organizations (firmalar)` tablosu
- `id` (uuid)
- `user_id` (Auth bağıntısı - Sahibi kim?)
- `domain_url` (www.ornek.com)
- `ws_kodu` 
- `gemini_api_key` (Güvenli şifrelenmiş)

### `ai_sessions (işlem geçmişi)` tablosu
- `id` (uuid)
- `firm_id` (Hangi firmaya ait?)
- `status` (pending, active, completed, failed)
- `total_products`, `processed_products`, `success_rate`
- `created_at`

### `ai_results (analiz sonuçları)` tablosu
- `id` (uuid)
- `session_id` 
- `stok_kodu`, `eski_urun_adi`, `ai_urun_adi` vb. (Product AI verileri, JSON formatında)

---

## 4. Geliştirme Süreci (Fazlar)

### Faz 1: Supabase & Next.js Kurulumu (Temel Hazırlık)
- `pixra` projesi için Vercel üzerinde Next.js ayağa kaldırılacak.
- Supabase Projesi oluşturulacak (Veritabanı tabloları, Auth RLS kuralları yazılacak).
- Supabase Auth entegrasyonu ile Login sayfası yapılacak.

### Faz 2: Python Backend (FastAPI API Servisi)
- PyQt6 kodu (`gui_manager.py`) atılıp, sistem bir REST API'ye dönüştürülecek (`main.py` -> `app = FastAPI()`).
- `vision_engine` ve `ticimax_api`, API uçları (endpoints) arkasında asenkron çalışacak.
- **Kuyruk Sistemi (Redis/Celery veya BackgroundTasks):** Web kullanıcısı analize basınca Python arkada çalışırken Vercel arayüzüne soket veya sık sorma (polling) ile "%10 ... %20 .. tıklandı" verisi basacak.

### Faz 3: Web UI Dashboard Gelişimi
- Dashboard sayfası: Firmalarım, Aktif Analizler.
- Firma Detay Sayfası: "Update Mode (Bulut)", "Create Mode (Yerel)".
- Analiz bittiğinde, Supabase veritabanından çekilip Excel aktarım veya doğrudan Ticimax'a (SaveUrun) Triple-Check mekanizması ile aktarım ekranları.

### Faz 4: Deployment & Prod Geçişi
- Next.js kodları -> Vercel'e push. `www.pixra.com` DNS yönlendirmesi.
- Python Backend -> Railway/Render ortamına deploy.
- Canlı ortam testleri.

---

## 5. Doğrulama Paneli (Verification Checklist)
- [ ] Kullanıcı kendi email ve şifresiyle girebiliyor mu?
- [ ] `Firmalarım` ekranında API keyleri güvenle saklandı mı?
- [ ] Kullanıcı "100 Ürün Cek" tuşuna basınca Vercel arayüzünde dönen ibare çıkıp hata vermeden bitiyor mu?
- [ ] Ürünler analiz edilirken Vercel Timeout (5 dk sınırı) sorununa takılmadan asenkron işlemler Railway Python tarafında işleniyor mu?
- [ ] `www.pixra.com`'da canlı yayına alındı mı?
