# Pixra Deploy Rehberi
> Backend → Railway | Frontend → Vercel | Domain → pixra.co

---

## ADIM 1 — Backend: Railway'e Deploy (5 dakika)

**Railway = backend'in çalışacağı sunucu. Aylık ~$5.**

### 1.1 Proje Oluştur
1. railway.app adresine git → **Login with GitHub**
2. **New Project** → **Deploy from GitHub repo**
3. Repo listesinden `Seo-anti` seç (veya ne adla kayıtlıysa)
4. **Root Directory**: `backend` yaz → Confirm

### 1.2 Environment Variables Ekle
Deploy başlamadan önce Settings → Variables sekmesine git, bunları ekle:

```
SUPABASE_URL         = https://zukqlkeecpgcqitlbgma.supabase.co
SUPABASE_SERVICE_ROLE_KEY = <backend/.env dosyasındaki değer>
GEMINI_API_KEY       = <backend/.env dosyasındaki değer>
```

### 1.3 Railway URL'ini Al
Deploy tamamlandıktan sonra:
- Settings → Networking → **Generate Domain** tıkla
- URL şöyle görünür: `https://pixra-backend-production.up.railway.app`
- Bu URL'i kopyala — bir sonraki adımda lazım

---

## ADIM 2 — Frontend: Vercel'e Deploy (5 dakika)

**Vercel = Next.js frontend için en iyi hosting. Ücretsiz başlar.**

### 2.1 Vercel CLI ile Login (tek seferlik)
Terminal'de şu komutu çalıştır:
```bash
vercel login
```
Tarayıcıda mail ile doğrulama yapacak.

### 2.2 Deploy

Terminal'de şunları sırayla çalıştır:

```bash
cd C:/Users/ASUS/Desktop/Projeler/Seo-anti/frontend

vercel --prod \
  --scope smhaydns-projects \
  --name pixra-co \
  --yes
```

İlk kez sorularsa:
- Set up and deploy? → **Y**
- Which scope? → smhaydns-projects
- Link to existing? → **N** (yeni proje)
- Project name? → **pixra-co**
- Directory? → **.** (mevcut klasör)

### 2.3 Environment Variables Ekle
Deploy bittikten sonra Vercel dashboard'dan **pixra-co → Settings → Environment Variables** ekle:

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://zukqlkeecpgcqitlbgma.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGci...` (frontend/.env.local'daki değer) |
| `NEXT_PUBLIC_API_URL` | Railway URL'i (Adım 1.3'ten) |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJhbGci...` (service role key) |

Ekledikten sonra **Redeploy** tıkla.

---

## ADIM 3 — Domain: pixra.co Bağlantısı (3 dakika)

1. Vercel → pixra-co → **Settings → Domains**
2. `pixra.co` ekle
3. Vercel sana DNS kayıtları verecek, bunları GoDaddy'e gir:

**GoDaddy DNS Ayarları:**
- Mevcut A kaydını sil
- Yeni A kaydı: `@` → Vercel IP (Vercel'in verdiği IP)
- CNAME kaydı: `www` → `cname.vercel-dns.com`
- DNS yayılması 5-30 dakika sürer

---

## ADIM 4 — Canlı Test (Lola of Shine)

Backend Railway'de çalışıyorken terminal'de:

```bash
# Backend sağlık kontrolü
curl https://pixra-backend-production.up.railway.app/

# Beklenen: {"status":"ok","message":"Pixra backend API is running"}
```

Sonra `https://pixra.co` adresinden sisteme giriş yap ve ilk analizi çalıştır.

---

## Özet: Ortam Değişkenleri

### Railway (Backend)
```
SUPABASE_URL=https://zukqlkeecpgcqitlbgma.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
GEMINI_API_KEY=AIzaSy...
```

### Vercel (Frontend)
```
NEXT_PUBLIC_SUPABASE_URL=https://zukqlkeecpgcqitlbgma.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...
NEXT_PUBLIC_API_URL=https://pixra-backend-xxx.up.railway.app
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
```

---

## Sorun Çıkarsa

| Sorun | Çözüm |
|-------|-------|
| Railway build fail | Logs sekmesine bak — genellikle import hatası |
| Vercel build fail | `npm run build` local'de çalıştır, hatayı gör |
| API çalışmıyor | `NEXT_PUBLIC_API_URL` doğru Railway URL mi? |
| Domain açılmıyor | GoDaddy DNS 30 dk bekle, cache temizle |
