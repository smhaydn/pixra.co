-- Migration 006: Firma Profil Anketi + llms.txt desteği
-- Açıklama: organizations tablosuna firma_profil JSONB alanı ekliyoruz.
-- Bu alan 10 soruluk onboarding anketinin cevaplarını saklar.
-- llms.txt için ek meta alanlar da ekleniyor.

-- 1. Firma profil anketi cevapları
ALTER TABLE organizations
  ADD COLUMN IF NOT EXISTS firma_profil JSONB DEFAULT '{}';

-- 2. AI içerik üretiminde kullanılacak ek firma meta alanları
ALTER TABLE organizations
  ADD COLUMN IF NOT EXISTS marka_tonu TEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS urun_kategorileri TEXT[] DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS hedef_kitle TEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS uretim_yeri TEXT DEFAULT NULL;

-- 3. llms.txt için son üretim tarihi
ALTER TABLE organizations
  ADD COLUMN IF NOT EXISTS llms_txt_generated_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

-- 4. Index: firma_profil sorguları için
CREATE INDEX IF NOT EXISTS idx_organizations_firma_profil
  ON organizations USING GIN (firma_profil);

-- Örnek firma_profil yapısı:
-- {
--   "ana_kategori": "ic_giyim",
--   "hedef_kitle": "25-44 yaş arası kadın, kalite öncelikli",
--   "deger_onerisi": "Türkiye üretimi, uzun ömürlü iç giyim",
--   "en_cok_satan": "Sütyen ve külot setleri",
--   "rakip_farki": "Pamuk ağırlıklı ürünler, hipoalerjenik dikkat",
--   "marka_tonu": "samimi",
--   "uretim_yeri": "turkiye",
--   "musteri_kriteri": "kalite",
--   "platformlar": ["ticimax", "trendyol"],
--   "marka_hikayesi": "2018'den beri Türk kadınına konfor odaklı iç giyim..."
-- }
