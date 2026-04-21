<!--
  TÜRKÇE AÇIKLAMA
  ───────────────
  Sistemin zarar görmesini engelleyen kurallar.
  Geri dönülemez komutlar için onay zorunluluğu ve
  çalışan sisteme dokunmama prensibi bu dosyada tanımlıdır.
  Bu kurallar her görevde, istisnasız uygulanır.
-->

---
name: safety
description: >
  Prevents irreversible damage to systems and data.
  Destructive commands require explicit user approval.
  Working systems must not be touched unless the task directly requires it.
---

# Safety Rules

## 1. Yıkıcı Komut Onayı

Aşağıdaki pattern'lerden herhangi birini içeren komutlar **çalıştırılmadan önce kullanıcıya gösterilir** ve onay beklenir:

```
DROP TABLE      DROP DATABASE     DROP INDEX
DELETE FROM     TRUNCATE
rm -rf          rmdir /s
git push --force (ana branch'te)
kubectl delete
docker system prune
```

**Gösterim formatı:**
```
⚠️  Yıkıcı komut tespit edildi — onay gerekiyor:

  rm -rf ./dist

Bu işlem geri alınamaz. Devam etmeli miyim? (evet/hayır)
```

Kullanıcı "evet" demeden komut çalıştırılmaz. "Ufak değişiklik" veya "geçici" istisnası yoktur.

---

## 2. Çalışan Sisteme Dokunma

Eğer bir sistem şu anda çalışıyorsa (test geçiyor, production'da aktif, kullanıcı tarafından kullanılıyor):

- Görev o sistemi **doğrudan değiştirmeyi** gerektirmiyorsa → **dokunma**
- Yeni özellik eklerken mevcut çalışan kodu kırmak zorundaysan → önce kullanıcıya bildir ve alternatif öner

**Pratik kural:**
```
Yeni şey eklenince mevcut testler kırılıyorsa → dur ve bildir.
"Bunu düzeltmek için şunu yapmam gerekiyor" de, sessizce değiştirme.
```

Yeni bir özellik eklendiğinde şu sıra uygulanır:
1. Mevcut testleri çalıştır — yeşil mi? → başla
2. Değişiklik sonrası testleri tekrar çalıştır
3. Kırılan test varsa → önce bunu raporla, sonra düzelt

---

## 3. Rollback Planı Zorunluluğu

Aşağıdaki işlemlerden önce rollback adımı tanımlanır:

| İşlem | Rollback |
|-------|---------|
| Database migration | Down migration yazılmış ve test edilmiş |
| Production deploy | Önceki versiyon tag'i mevcut, deploy geri alınabilir |
| Config değişikliği | Eski değer yorum olarak veya `.env.example`'da saklı |
| Büyük refactor | Feature branch'te yapılır, main'e dokunulmaz |

Rollback tanımlanmadan yıkıcı işleme başlanmaz.
