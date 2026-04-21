-- 004: Strategist+Writer prompt yeni alanları
-- ai_aciklama, ai_seo_anahtar_kelime, ai_schema_jsonld, ai_breadcrumb_kat,
-- ai_ozelalan_1..5, ai_claim_map, ai_information_gain, ai_uyarilar

ALTER TABLE ai_results
  ADD COLUMN IF NOT EXISTS ai_aciklama TEXT,
  ADD COLUMN IF NOT EXISTS ai_seo_anahtar_kelime TEXT,
  ADD COLUMN IF NOT EXISTS ai_schema_jsonld JSONB,
  ADD COLUMN IF NOT EXISTS ai_breadcrumb_kat TEXT,
  ADD COLUMN IF NOT EXISTS ai_ozelalan_1 TEXT,
  ADD COLUMN IF NOT EXISTS ai_ozelalan_2 TEXT,
  ADD COLUMN IF NOT EXISTS ai_ozelalan_3 TEXT,
  ADD COLUMN IF NOT EXISTS ai_ozelalan_4 TEXT,
  ADD COLUMN IF NOT EXISTS ai_ozelalan_5 TEXT,
  ADD COLUMN IF NOT EXISTS ai_claim_map JSONB,
  ADD COLUMN IF NOT EXISTS ai_information_gain SMALLINT,
  ADD COLUMN IF NOT EXISTS ai_uyarilar JSONB;

-- Information Gain üzerinden kalite trend takibi için index
CREATE INDEX IF NOT EXISTS idx_ai_results_ig
  ON ai_results (session_id, ai_information_gain DESC NULLS LAST);
