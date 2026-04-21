# Scope: Ticimax SEO/GEO SaaS
**Tarih:** 2026-04-17
**Karar Verenler:** Semih (Teknik), Partumajans (Pazarlama)

## Problem
Ticimax altyapisini kullanan e-ticaret site sahipleri urun icerik girisinde ciddi zaman kaybediyor. Ozellikle sifirdan panel acan firmalar icin yuzlerce/binlerce urunun SEO baslik, aciklama, anahtar kelime, Google Shopping (Adwords) alanlari ve gorsel bazli icerik uretimi manuel olarak saatler/gunler suruyor. Bu surecte uretilen icerikler genellikle SEO/GEO standartlarini karsilamiyor.

## Hedef Kitle
- Ticimax altyapisini kullanan e-ticaret site sahipleri
- Ozellikle sifirdan panel acan veya cok urunlu (500+) magazalar
- Ilk musteri kanali: Partumajans (dijital reklam ajansi) musteri portfoyu

## Kapsam Ici (MVP)
- Ticimax WS entegrasyonu ile mevcut urunleri cekme ve guncelleme
- Gemini Vision AI ile gorsel bazli SEO/GEO icerik uretimi (toplu)
- Ticimax'e toplu geri yazma (SEO, aciklama, Adwords/Pazarlama alanlari)
- Multi-tenant: birden fazla firma yonetimi (Supabase auth + firma kaydi)
- Kullanici dashboard: analiz durumu, maliyet takibi
- Klasorden gorsel yukleme (yerel mod) + URL'den cekme (bulut mod)

## Kapsam Disi (Simdilik)
- Diger altyapilar (T-Soft, IdeaSoft, Shopify) — basariya gore sonra
- Siparis cekme ve karlilik analizi — Phase 2
- Rakip analizi ve haftalik kelime guncelleme — veri kaynagi belirsiz, Phase 3
- Sifirdan urun olusturma (fiyat, stok, varyasyon girisi) — Phase 2
- AI reklam yonetimi (iyzads benzeri) — tamamen ayri proje

## Basari Kriterleri
1. Bir kullanici 500 urunu 2-3 saat icinde analiz edip Ticimax'e aktarabilmeli
2. Ilk 3 ayda en az 5 odeme yapan musteri edinilmeli
3. Urun basina maliyet 0.10 TL'yi gecmemeli
4. Kullanici NPS skoru 7+ olmali

## Dogrulanmamis Varsayimlar
- "Kullanicilar bu hizmet icin aylik abonelik odeyecek" → Ilk 3 musteri ile test et
- "SEO/GEO icerik kalitesi musterileri cezbedecek" → Orneklerle satis sayfasi yap
- "2-3 saatte 500+ urun analiz edilebilir" → Paralel islem ve hiz optimizasyonu gerekli (su an 44sn/urun)
- "Haftalik rakip analizi retention saglayacak" → Veri kaynagi ve maliyet belirsiz
- "Her Ticimax musterisinin WS yetki kodu aktif" → Kontrol edilmeli

## Secilen Yaklasim
Mevcut calisan MVP uzerine insa et. Once hiz ve olcek sorunlarini coz, sonra SaaS katmanini (auth, abonelik, multi-tenant) ekle.

## Ilk Slice (MVP — Satis Yapilabilir Minimum)
1. **Hiz Optimizasyonu** — Paralel analiz (5-10 concurrent), hedef: 500 urun < 3 saat
2. **Landing Page** — Ne yaptigini, ornekleri ve fiyatlandirmayi gosteren satis sayfasi
3. **Abonelik Sistemi** — Supabase + Stripe/Iyzico entegrasyonu
4. **Onboarding Akisi** — Kullanici kayit > firma ekle > WS kodu gir > urunleri cek > analiz > Ticimax'e gonder
5. **Kullanim Limitleri** — Paketlere gore aylik urun analiz limiti

## Sonraki Adim
→ `writing-plans` skill'i ile Phase 1 implementasyon plani olustur
