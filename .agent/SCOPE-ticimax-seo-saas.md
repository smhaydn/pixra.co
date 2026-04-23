# Kapsam: Pixra SaaS
> Son güncelleme: 2026-04-23 | Önceki: 2026-04-17

---

## Problem

Ticimax altyapısındaki e-ticaret sahipleri yüzlerce/binlerce ürün için SEO başlık, açıklama, anahtar kelime ve GEO içerik girişini manuel yapıyor. Saatler/günler sürüyor, kalite düşük, AI motorlarında görünürlük sıfır.

---

## Hedef Kitle

- Ticimax e-ticaret sahipleri (özellikle 500+ ürünlü)
- İlk kanal: Partumajans (dijital ajans) müşteri portföyü
- Sektörler: kadın giyim/iç giyim ağırlıklı, genişletilebilir

---

## Mevcut Durum (2026-04-23)

### Tamamlananlar ✅
- FastAPI backend + Gemini 2.5 Flash Vision motoru
- Ticimax SOAP entegrasyonu (ürün çekme + geri yazma)
- Pydantic validation (21 alan), Verifier katmanı
- Next.js 16 frontend — tam çalışan SaaS UI
- Supabase Auth + multi-tenant (organizations, profiles, RLS)
- Admin Panel (impersonation, müşteri yönetimi, Gemini key pool)
- Warm amber design system v3 (dark/light mode)
- **Sektör RAG Sprint 1:** DB altyapısı + backend prompt injection + frontend sektör seçimi
- GitHub → Vercel auto-deploy bağlantısı

### Sıradaki ⏳
1. Sektör RAG Sprint 2 — Otomatik web tarama (crawler)
2. İçerik Kalitesi — Multi-pass üretim, kategori şablonları
3. Sektör RAG Sprint 3 — Öğrenme döngüsü
4. AI Görünürlük Katmanı — llms.txt, alt-text, schema.org
5. Reklam Entegrasyonu — Google Ads → Meta Ads

---

## Kapsam İçi

- Ticimax WS entegrasyonu (tek platform, başarıya göre genişler)
- Gemini Vision ile görsel bazlı SEO/GEO içerik üretimi (toplu)
- Sektör bazlı RAG — firma sektörüne göre özelleşmiş AI üretimi
- Multi-tenant SaaS (Supabase auth + firma kaydı)
- Admin dashboard — tüm firmaları yönet, impersonate
- Kullanıcı dashboard — analiz durumu, kredi takibi, onay akışı
- llms.txt üretimi — ChatGPT/Perplexity için mağaza knowledge base
- Reklam içerik üretimi (Google Ads, Meta Ads) — ileride

---

## Kapsam Dışı (şimdilik)

- T-Soft, IdeaSoft, Shopify entegrasyonu → başarıya göre Phase 3
- Sipariş çekme, karlılık analizi → Phase 2
- Rakip analizi ve haftalık kelime güncelleme → veri kaynağı belirsiz
- Sıfırdan ürün oluşturma (fiyat, stok, varyasyon) → Phase 2
- Mobil uygulama → gündemde değil
- Çoklu dil (EN/DE) → Phase 3 sonrası
- White-label lisanslama → değerlendir

---

## Başarı Kriterleri

1. 500 ürün 2-3 saat içinde analiz + Ticimax'a aktarım (şu an ~44sn/ürün → paralel gerekli)
2. İlk 3 ayda 5 ödeme yapan müşteri
3. Ürün başına maliyet ≤ 0.10 TL
4. Kullanıcı NPS skoru 7+

---

## Doğrulanmamış Varsayımlar

- "Kullanıcılar aylık abonelik öder" → İlk 3 müşteri ile test et
- "SEO/GEO kalitesi satışı artırır" → Örneklerle satis sayfası yap
- "Sektör RAG çıktı kalitesini artırır" → A/B test gerekli (sector vs genel prompt)
- "Her Ticimax müşterisinin WS yetki kodu aktif" → Onboarding'de kontrol var

---

## Kritik Teknik Kararlar

| Karar | Gerekçe |
|-------|---------|
| Gemini Flash, Claude değil | Vision + maliyet (0.10 TL/ürün hedefi) |
| SOAP/zeep, REST değil | Ticimax sadece SOAP sunuyor |
| Supabase RLS | Multi-tenant veri izolasyonu |
| styled-jsx, Tailwind utility değil | CSS token sistemi tutarlılığı |
| Sprint yaklaşımı (RAG) | Hızlı değer, kademeli iyileştirme |
