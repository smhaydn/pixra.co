<!--
  TÜRKÇE AÇIKLAMA
  ───────────────
  Kodun temiz ve bakımı kolay kalmasını sağlayan kurallar.
  Yorum stili, debug log temizliği ve hassas veri yönetimi
  bu dosyada tanımlanmıştır. Her commit öncesi kontrol edilir.
-->

---
name: code-hygiene
description: >
  Keeps code clean and maintainable. Defines comment style (method-level only),
  debug log cleanup policy, and environment variable / sensitive data handling.
---

# Code Hygiene Rules

## 1. Yorum Stili — Yalnızca Metot Seviyesinde

Kod içine **satır arası yorum yazılmaz.** Yorumlar yalnızca fonksiyon/metot başlıklarında bulunur.

```typescript
// ✅ Doğru — metot üstünde, ne yaptığını açıklayan JSDoc
/**
 * Kullanıcıyı email ile bulur, bulamazsa null döner.
 */
async function findUserByEmail(email: string): Promise<User | null> {
  return db.users.findUnique({ where: { email } });
}

// ❌ Yanlış — satır içi açıklama
async function findUserByEmail(email: string) {
  // email'i küçük harfe çevir
  const normalized = email.toLowerCase();
  // veritabanında ara
  return db.users.findUnique({ where: { email: normalized } });
}
```

**Kural:** Bir satırı açıklamak zorunda hissediyorsan, kod yeterince açık değildir. Yorumu sil, kodu düzelt.

İstisnalar (tek kabul edilen):
- `// TODO: #123 — açıklaması` (ticket numarası zorunlu)
- `// FIXME: #456 — nedeni` (ticket numarası zorunlu)

---

## 2. Debug Log Temizliği

Görev tamamlandıktan sonra, commit öncesinde şunlar kaldırılır:

| Dil | Temizlenecekler |
|-----|----------------|
| JavaScript/TypeScript | `console.log`, `console.warn`, `console.error`, `console.table`, `debugger` |
| Python | `print()` (loglama için değil debug için kullanılanlar) |
| CSS/HTML | Geçici `outline: 1px solid red` veya test renkleri |

**Kontrol komutu:**
```bash
# Commit öncesi — staged dosyalarda debug log var mı?
git diff --staged | grep -E "console\.(log|warn|error|table)|debugger|print\("
```

Gerçek loglama (`logger.info`, `logger.error`) bu kuralın kapsamı dışındadır — bunlar kalır.

---

## 3. Environment Variable & Hassas Veri Yönetimi

### 3a. Görünür Değer Yasağı
API key, token, şifre, connection string — bunların hiçbiri kod içinde görünmez:

```typescript
// ❌ Yasak
const apiKey = "sk-1234abcd...";
const dbUrl = "postgresql://user:pass@host/db";

// ✅ Doğru
const apiKey = process.env.OPENAI_API_KEY;
const dbUrl = process.env.DATABASE_URL;
```

### 3b. API'den Alınabilecek Değerler
Eğer bir değer runtime'da API'den çekilebiliyorsa → kod içine sabit yazılan değer yerine API'den al:

```typescript
// ❌ Yanlış — config'i koda göm
const maxUploadSize = 10 * 1024 * 1024; // hardcoded 10MB

// ✅ Doğru — config endpoint varsa oradan al
const { maxUploadSize } = await configService.getAppConfig();
```

### 3c. Yeni ENV Variable → .env.example Zorunlu
Her yeni environment variable eklendiğinde `.env.example` güncellenir:

```bash
# .env.example
OPENAI_API_KEY=your-key-here          # OpenAI API anahtarı
DATABASE_URL=postgresql://...          # Veritabanı bağlantı URL'i
```

Açıklama satırı (# ile başlayan) zorunludur. Değer örnek/placeholder olmalı, gerçek değer asla girilmez.
