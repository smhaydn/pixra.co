<!--
  TÜRKÇE AÇIKLAMA
  ───────────────
  Kodun tekrar kullanılabilir ve anlaşılabilir kalmasını sağlayan kurallar.
  DRY prensibi uygulanır ama over-engineering yapılmaz.
  "Yeterince iyi" ile "aşırı soyutlama" arasındaki dengeyi tanımlar.
-->

---
name: code-quality
description: >
  Enforces DRY without over-engineering. Duplicate code is refactored when
  it appears 3+ times or would cause bugs if not updated consistently.
  Abstractions must earn their complexity — no premature generalization.
---

# Code Quality Rules

## 1. DRY Prensibi — Ama Aşırıya Kaçmadan

### Ne Zaman Refactor Edilir?
Aynı kod bloğu **3 veya daha fazla** yerde tekrar ediyorsa → extract et.

```typescript
// ❌ 3 yerde tekrar eden aynı doğrulama
if (!email || !email.includes('@')) throw new Error('Invalid email');  // kullanıcı kaydında
if (!email || !email.includes('@')) throw new Error('Invalid email');  // login'de
if (!email || !email.includes('@')) throw new Error('Invalid email');  // şifre sıfırlamada

// ✅ Bir kez yaz, her yerde kullan
function validateEmail(email: string): void {
  if (!email || !email.includes('@')) throw new ValidationError('Invalid email');
}
```

### Ne Zaman Refactor EDİLMEZ?
İki benzer kod parçası farklı bağlamlarda çalışıyorsa — aynı "görünüyor" diye birleştirme. Yanlış soyutlama, tekrarlayan koddan daha kötüdür.

```
❌ Aşırı soyutlama tuzağı:
"Bu iki fonksiyon %80 benziyor, birleştirelim."
→ 3 ay sonra biri değişti, diğeri değişmedi — şimdi 10 parametre + 5 if bloğu var.

✅ Doğru yaklaşım:
Kod benzer görünse de, değişme sebepleri farklıysa → ayrı tut.
```

---

## 2. Soyutlama Eşiği

Yeni bir soyutlama (helper function, class, util module) oluşturmadan önce:

- [ ] Bu kodu 3+ yerde mi kullanıyorum?
- [ ] Bu kodu çıkarınca her kullanım yeri daha mı okunabilir, daha mı karmaşık?
- [ ] Bu soyutlamayı 6 ay sonra başka biri anlayabilir mi?

3 soruya da "evet" → extract et.  
Birinde "hayır" → olduğu yerde bırak.

---

## 3. Overdesign Göstergeleri

Şu işaretlerden biri görünüyorsa → dur, kullanıcıya bildir:

| Gösterge | Ne Anlama Gelir |
|----------|----------------|
| Factory'nin Factory'si | Çok fazla dolaylı yönlendirme |
| 5'ten fazla parametre alan fonksiyon | Görev çok büyük, böl |
| Interface'i sadece 1 yer implement ediyor | Erken soyutlama |
| Util klasöründe 20+ küçük fonksiyon | Organize edilmemiş sepetin büyümesi |
| Her şey konfigüre edilebilir | Ne yapacağı belirsiz |

---

## 4. Refactor Zamanı

Refactor yapılabilecek durumlar:

- **Görev sırasında tespit edildi** → görevi bitir, sonra ayrı commit'te refactor et
- **Refactor bir feature'ın önkoşulu** → önce refactor commit at, sonra feature'ı ekle (tek PR'da 2 ayrı commit)
- **Refactor büyük** (5+ dosya etkileniyor) → ayrı branch, ayrı PR

```bash
# ✅ Doğru commit sırası
git commit -m "refactor(validation): extract email validation to shared util"
git commit -m "feat(auth): add password reset flow using shared email validator"

# ❌ Yanlış — ikisi aynı commit'te
git commit -m "feat(auth): add password reset + clean up email validation"
```

---

## 5. "Yeterince İyi" Prensibi

Her fonksiyon şu soruyu geçmeli:

> **"Bu kodu 6 ay sonra ilk kez gören biri, ne yaptığını 2 dakikada anlayabilir mi?"**

- Evet → yeterince iyi, devam et
- Hayır → yeniden yaz (yorum ekleme — kodu netleştir)
