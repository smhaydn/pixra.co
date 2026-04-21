-- Phase 2: credits tablosu, kredi ayarlama geçmişi, waitlist
-- Ek güvenlik için service_role dışına kapalı — RLS etkin, policy yok.

CREATE TABLE IF NOT EXISTS credits (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    balance INTEGER NOT NULL DEFAULT 10,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE credits ENABLE ROW LEVEL SECURITY;

CREATE POLICY "View own credits" ON credits
    FOR SELECT USING (auth.uid() = user_id);
-- Insert/Update sadece service_role ile yapılır.


CREATE TABLE IF NOT EXISTS credit_adjustments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    delta INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE credit_adjustments ENABLE ROW LEVEL SECURITY;
-- Sadece admin (service_role) görebilir.


CREATE TABLE IF NOT EXISTS waitlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    email TEXT NOT NULL,
    package_id TEXT,
    package_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE waitlist ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Insert own waitlist entry" ON waitlist
    FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);


-- Yeni kullanıcı kayıt olduğunda 10 ücretsiz kredi bas
CREATE OR REPLACE FUNCTION create_default_credits()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO credits (user_id, balance) VALUES (NEW.id, 10)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created_credits ON auth.users;
CREATE TRIGGER on_auth_user_created_credits
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION create_default_credits();
