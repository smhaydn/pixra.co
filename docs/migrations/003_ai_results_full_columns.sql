-- ai_results'a eksik kolonlari ekler (backend entegrasyonu icin)

ALTER TABLE ai_results
  ADD COLUMN IF NOT EXISTS original_urun_adi TEXT,
  ADD COLUMN IF NOT EXISTS original_seo_baslik TEXT,
  ADD COLUMN IF NOT EXISTS original_seo_aciklama TEXT,
  ADD COLUMN IF NOT EXISTS original_aciklama TEXT,
  ADD COLUMN IF NOT EXISTS ai_anahtar_kelime TEXT,
  ADD COLUMN IF NOT EXISTS ai_hedef_kelime TEXT,
  ADD COLUMN IF NOT EXISTS ai_geo_sss TEXT,
  ADD COLUMN IF NOT EXISTS ai_adwords_aciklama TEXT,
  ADD COLUMN IF NOT EXISTS ai_adwords_kategori TEXT,
  ADD COLUMN IF NOT EXISTS ai_adwords_tip TEXT,
  ADD COLUMN IF NOT EXISTS image_url TEXT,
  ADD COLUMN IF NOT EXISTS error_message TEXT,
  ADD COLUMN IF NOT EXISTS cost_tl NUMERIC(10, 4);

-- Tamamlanma ve iptal durumlari icin status enum'u aciyoruz
-- (ai_sessions.status bir check constraint yok, sadece text; cancelled desteklensin)
-- Mevcut bir check constraint varsa gecis icin yeterli

-- ai_results icin stok_kodu + session_id uzerinde index (hizli sorgu)
CREATE INDEX IF NOT EXISTS idx_ai_results_session ON ai_results(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_user_status ON ai_sessions(user_id, status);

-- Service role'un insert/update yapabilmesi icin policy
-- (service_role zaten RLS'i bypass eder, ama ek policy ile acik yapiyoruz)
DROP POLICY IF EXISTS "Service inserts ai_results" ON ai_results;
CREATE POLICY "Service inserts ai_results" ON ai_results
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Service updates ai_sessions" ON ai_sessions;
CREATE POLICY "Service updates ai_sessions" ON ai_sessions
    FOR UPDATE USING (true);
