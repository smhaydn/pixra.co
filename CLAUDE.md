# Ticimax AI Manager - Proje Kurallari

## Proje Yapisi
- **app.py**: PyQt6 giris noktasi
- **vision_engine.py**: Gemini Vision AI motoru (SEO/GEO analiz)
- **ticimax_api.py**: Ticimax SOAP client (zeep)
- **gui_manager.py**: Arayuz (LoginPanel, ProductDetailDialog, MainWindow)
- **ai_workers.py**: QThread worker'lar (Ticimax, Vision, Create)
- **helpers.py**: SessionState, retry, yardimci fonksiyonlar
- **theme.py**: QSS dark tema
- **main.py**: Legacy CLI test script (kullanilmiyor)

## Her Zaman Gecerli Kurallar

### Kod Standartlari
- Tum Python kodlari moduler ve OOP olmalidir
- Ticimax SOAP entegrasyonu icin sadece `zeep` kutuphanesi kullanilmalidir
- Gorsel analiz ciktilari Pydantic modelleri ile valide edilmelidir
- API anahtarlari asla koda gomulmemeli, firms.json veya .env'den okunmalidir
- Magic number/string kullanilmamali, sabitler tanimlanmalidir
- Hata mesajlari aciklayici olmalidir, genel catch-all bloklardan kacinilmalidir

### SEO/GEO Standartlari
- SEO baslik: max 60 karakter, aciklama: max 155 karakter
- GEO icin her urun aciklamasina en az bir "Neden bu urunu almaliyim?" semantik paragraf eklenmeli
- Ciktilar yapilandirilmis JSON formatinda olmali (urun_adi, aciklama, seo_baslik, seo_aciklama, geo_sss)
- 2026 standartlarina uyulmali: semantik zenginlik, FAQ bloklari, E-E-A-T sinyalleri
- Gemini Vision ciktisi her zaman yapilandirilmis JSON objesi olmali

### Multi-Tenant & Guvenlik
- Hicbir marka, URL veya API anahtari hardcoded olmamalıdir
- Tum baglanti parametreleri GUI uzerinden dinamik olarak alinmalidir
- Ticimax'e veri gonderimi (Update/Create) oncesinde kullanicidan 3 asamali onay zorunludur
- Hibrit veri kaynagi desteklenmeli: Bulut Modu (URL'den cekme) + Yerel Mod (klasorden gorsel okuma)

### Genel Calisma Prensipleri
- Dosya degistirmeden once import'lari ve bagimliliklari kontrol et
- Mevcut kod desenlerini takip et, yeni pattern olusturmadan once codebase'deki orneklere bak
- Over-engineering yapma, sadece istenen degisiklikleri yap
- Emin olunmayan durumlarda dosyayi oku, asla tahmin etme

## .agent Klasoru (Skills, Agents & Rules)
Proje icinde `.agent/` klasoru bulunmaktadir (vibe-coder-kit). Ihtiyac halinde ilgili dosyalar okunmalidir:

### Agents (`.agent/agents/`)
- `backend-dev.md` — Backend gelistirme persona (API, DB, guvenlik)
- `designer.md` — UI/UX ve tasarim persona
- `devops.md` — Altyapi ve deploy persona
- `frontend-dev.md` — Frontend gelistirme persona

### Skills (`.agent/skills/`)
- `architecture-review/SKILL.md` — Mimari degerlendirme
- `brainstorming/SKILL.md` — Fikir uretme ve planlama
- `code-review/SKILL.md` — Kod inceleme protokolu
- `dependency-audit/SKILL.md` — Bagimlilık denetimi
- `documentation-sync/SKILL.md` — Dokumantasyon guncelleme
- `github/SKILL.md` — Git/GitHub workflow'u
- `incident-response/SKILL.md` — Olay mudahale protokolu
- `knowledge-base-update/SKILL.md` — Bilgi tabani guncelleme
- `project-context-primer/SKILL.md` — Proje baglam hazirlamasi
- `prompt-enhancer/SKILL.md` — Prompt iyilestirme rehberi
- `test-driven-execution/SKILL.md` — TDD protokolu
- `writing-plans/SKILL.md` — Plan yazma workflow'u

### Rules (`.agent/rules/`)
- `code-hygiene.md` — Kod temizligi standartlari
- `code-quality.md` — Kod kalitesi ve performans
- `safety.md` — Guvenlik protokolleri
- Detayli kurallar gerektiginde bu dosyalar okunmalidir

### Kapsam (`.agent/SCOPE-ticimax-seo-saas.md`)
- Projeye ozel kapsam ve sinirlar dokumani
