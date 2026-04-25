# Google Search Console OAuth Setup — Pixra

Pixra'nın Google Search Console entegrasyonunu etkinleştirmek için gerçekleştirilmesi gereken adımlar.

---

## 1. Google Cloud Console Projesi Oluştur

### 1.1 Proje Oluştur
1. [Google Cloud Console](https://console.cloud.google.com/) → "Yeni Proje"
2. Proje Adı: `Pixra GSC Integration` (veya istediğin ad)
3. "Oluştur" butonuna tıkla

### 1.2 API'leri Etkinleştir
1. Sol panel → "API'ler ve Hizmetler" → "Kütüphane"
2. Ara: **"Search Console API"**
3. "Search Console API" seç → "ETKINLEŞTIR"
   
   Aynı işlemi "Google Search Console API" için tekrarla (varsa).

---

## 2. OAuth 2.0 Kimlik Bilgisi Oluştur

### 2.1 OAuth Onay Ekranını Konfigüre Et
1. Sol panel → "API'ler ve Hizmetler" → "OAuth Onay Ekranı"
2. Kullanıcı Tipi: `Harici` seç → "Oluştur"
3. Aşağıdaki alanları doldur:

   | Alan | Değer |
   |------|-------|
   | **Uygulama Adı** | Pixra SEO Assistant |
   | **Kullanıcı Destek E-postası** | senin@emailin.com |
   | **Geliştirici İletişim Bilgileri** | senin@emailin.com |

4. "Kaydet ve Devam Et" → Kapsamlar (Scopes) → "Kaydet ve Devam Et" (varsayılan tamam)
5. Test Kullanıcıları: "Kullanıcı Ekle" → E-posta gir → "Kaydet"
6. "Yönetim Panelinedonü" veya "Tamamlandı" butonuna tıkla

### 2.2 OAuth 2.0 İstemci Kimlik Bilgisi Oluştur
1. Sol panel → "API'ler ve Hizmetler" → "Kimlik Bilgileri"
2. "+ KİMLİK BİLGİSİ OLUŞTUR" → "OAuth 2.0 İstemci Kimliği"
3. Uygulama Türü: **Web Uygulaması**
4. İsim: `Pixra Backend` (veya istediğin ad)

#### Yetkilendirilmiş JavaScript Kaynakları:
```
http://localhost:8000
http://localhost:3000
https://pixra.co
https://www.pixra.co
https://api.pixra.co
```

#### Yetkilendirilmiş Yeniden Yönlendirme URI'leri:
```
http://localhost:8000/api/integrations/gsc/callback
https://api.pixra.co/api/integrations/gsc/callback
```

5. "Oluştur" → İstemci Kimliği ve İstemci Sırrı'nı kopyala

---

## 3. Environment Variable'ları Güncelle

### Backend `.env` dosyasını aç:
```bash
# C:\Users\ASUS\Desktop\Projeler\Seo-anti\backend\.env
```

Aşağıdaki satırları ekle veya güncelle:
```env
# Google Search Console OAuth
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here

# Frontend ve Backend URL'leri
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# Production için:
# FRONTEND_URL=https://pixra.co
# BACKEND_URL=https://api.pixra.co
```

### Değerleri Kopyala:
1. Google Cloud Console → Kimlik Bilgileri → OAuth 2.0 İstemci Kimliği (web)
2. "İstemci Kimliği" → `GOOGLE_CLIENT_ID`
3. "İstemci Sırrı" → `GOOGLE_CLIENT_SECRET`

---

## 4. Supabase Tablosu Hazırla

Sektör RAG'i kullanıcı tarafından bağlanacak GSC token'ları saklamak için Supabase'de alan hazırdır:

```
organizations.firma_profil -> __gsc__
  ├─ access_token
  ├─ refresh_token
  ├─ expires_at
  └─ connected_at
```

Herhangi bir migration gerekli değil (JSONB field zaten var).

---

## 5. Backend'i Test Et

### 5.1 Backend'i Başlat
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5.2 OAuth URL'sini Test Et
```bash
curl http://localhost:8000/api/integrations/gsc/auth-url
```

Çıktı (örnek):
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=..."
}
```

### 5.3 OAuth Callback'ini Simulate Et

`https://accounts.google.com/o/oauth2/v2/auth?...` linki tarayıcıda aç, Google hesabını seç, izin ver.
Eğer başarılı ise browser'ı localhost/api/integrations/gsc/callback?code=... adresine yönlendir.

---

## 6. Frontend'den Test Et

### Settings → Entegrasyonlar
1. Pixra'yı açıp Settings → Entegrasyonlar tab'ına git
2. "Google Search Console" → "Bağlan"
3. Google hesabı ile giriş yap, izin ver
4. "Başarıyla bağlandı" mesajı görmeli
5. "Verileri Güncelle" butonuyla GSC top queries'i sync edebilirsin

---

## 7. Otomatik Sektör Taraması Kontrol Et

Admin Panel'den:
1. Admin Dashboard → "🔍 Otomatik Tara" butonuna tıkla
2. Sektör seç, "Taranan" => GSC verilerini +RAG önerilerini birleştirir

---

## Gerekli Scopes (Otomatik)

Backend OAuth URL'si oluştururken otomatik olarak bu scopes eklenir:
```
https://www.googleapis.com/auth/webmasters.readonly
```

Bu, Search Console verilerini okuma-only yetkisiyle erişim sağlar (yazma yetkisi yok).

---

## Troubleshooting

| Problem | Çözüm |
|---------|-------|
| "Invalid client ID" hatası | Client ID ve Secret'ı kontrol et, `.env` dosyasını tekrar yükle |
| Redirect URI mismatch | Google Cloud'daki yetkilendirilmiş URI'leri güncelle |
| "Authorization failed" | Test kullanıcılarını OAuth onay ekranına ekle |
| Token expire hatası | Refresh token otomatik yenilenir, error handling kontrol et |

---

## Deployment (Production)

1. **Google Cloud** → İstemci Kimliği seç → URI'leri güncelle:
   ```
   https://pixra.co
   https://api.pixra.co
   ```

2. **Production .env** (Railway backend):
   ```env
   GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxx
   FRONTEND_URL=https://pixra.co
   BACKEND_URL=https://api.pixra.co
   ```

3. **Vercel frontend**:
   Ortam değişkenleri otomatik backend'den işlenir.

---

## Kaynaklar

- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Search Console API Docs](https://developers.google.com/webmaster-tools)
- [OAuth 2.0 Setup Guide](https://developers.google.com/identity/protocols/oauth2)

