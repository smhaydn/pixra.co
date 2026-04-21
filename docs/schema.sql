-- 1. Eklentileri aciyoruz (UUID uretimi icin)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Firmalar (Organizations) Tablosu
-- Bu tablo, Pixra sistemine kayitli SaaS musterilerini (Ticimax saticilarini) tutar.
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    company_name TEXT NOT NULL,
    domain_url TEXT,
    ws_kodu TEXT,
    gemini_api_key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- RLS (Row Level Security) - Musteri sadece KENDI firmasini gorur ve duzenler
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "View own organization" ON organizations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Update own organization" ON organizations
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Insert own organization" ON organizations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 3. AI Oturumlari (Sessions) Tablosu
-- Her bir "Analiz Baslat" isleminde bir session acilir. 
CREATE TABLE ai_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    job_name TEXT NOT NULL, -- Ozet (Canta analizi vs)
    status TEXT NOT NULL DEFAULT 'pending', -- pending, processing, completed, error
    total_products INTEGER DEFAULT 0,
    processed_products INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE ai_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "View own sessions" ON ai_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Insert own sessions" ON ai_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 4. AI Sonuclari (Results) Tablosu
-- Yapay zekanin tamamladigi her bir urun buraya duser
CREATE TABLE ai_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES ai_sessions(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    stok_kodu TEXT,
    urun_adi TEXT,
    ai_urun_adi TEXT,
    ai_seo_baslik TEXT,
    ai_seo_aciklama TEXT,
    ai_onyazi TEXT,
    ai_html_icerik TEXT, -- Tum E-E-A-T, tablo ve FAQ'lu format
    status TEXT NOT NULL DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE ai_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "View own ai results" ON ai_results
    FOR SELECT USING (auth.uid() = user_id);

-- 5. Kullanici kayit oldugunda otomatik tetikleyici (Trigger) ile organization olusturma:
-- Eger kullanici kayit oldugunda direkt bir sirket atansin isterseniz asagidaki yapiyi kullanabilirsiniz.
-- (Bunu frontend icerisinden onboarding adimiyla yonetmek daha iyidir, bu yuzden SQL icinde bos birakildi)
