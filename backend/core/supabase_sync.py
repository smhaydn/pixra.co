"""Supabase ile backend analiz durumu senkronizasyonu.

Bu modul, analiz sirasinda ai_sessions ve ai_results tablolarini
guncelleyen yardimci fonksiyonlar saglar. Service role key kullanir
(RLS'i bypass eder).

Tum fonksiyonlar best-effort calisir — Supabase'e yazim basarisiz olursa
analiz devam eder, sadece log atilir. Bu, backend'in Supabase kesintilerinde
calismaya devam etmesini saglar.
"""
from __future__ import annotations

import os
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

_client = None
_session_meta_cache: dict[str, tuple[str, str]] = {}  # session_id -> (org_id, user_id)


def _get_client():
    """Lazy init — ilk cagrida client olusturur, sonra cache'ler."""
    global _client
    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        logger.warning("SUPABASE_URL veya SUPABASE_SERVICE_ROLE_KEY bos — senkronizasyon devre disi")
        return None

    try:
        from supabase import create_client
        _client = create_client(url, key)
        logger.info("Supabase client baslatildi")
        return _client
    except Exception as e:
        logger.error(f"Supabase client olusturulamadi: {e}")
        return None


def is_enabled() -> bool:
    return _get_client() is not None


def get_session_meta(session_id: str) -> Optional[tuple[str, str]]:
    """ai_sessions'tan organization_id ve user_id'yi getirir (cache'li)."""
    if session_id in _session_meta_cache:
        return _session_meta_cache[session_id]

    client = _get_client()
    if not client:
        return None

    try:
        res = client.table("ai_sessions").select("organization_id, user_id").eq("id", session_id).maybe_single().execute()
        if res and res.data:
            meta = (res.data["organization_id"], res.data["user_id"])
            _session_meta_cache[session_id] = meta
            return meta
    except Exception as e:
        logger.error(f"Session meta okunamadi ({session_id[:8]}): {e}")
    return None


def update_session(session_id: str, **fields) -> bool:
    """ai_sessions satirini gunceller. Basarili ise True."""
    client = _get_client()
    if not client:
        return False
    try:
        client.table("ai_sessions").update(fields).eq("id", session_id).execute()
        return True
    except Exception as e:
        logger.error(f"Session update basarisiz ({session_id[:8]}): {e}")
        return False


def mark_processing(session_id: str) -> None:
    update_session(session_id, status="processing")


def mark_completed(session_id: str, processed: int) -> None:
    update_session(
        session_id,
        status="completed",
        processed_products=processed,
        completed_at=datetime.now(timezone.utc).isoformat(),
    )


def mark_cancelled(session_id: str, processed: int) -> None:
    update_session(
        session_id,
        status="cancelled",
        processed_products=processed,
        completed_at=datetime.now(timezone.utc).isoformat(),
    )


def mark_failed(session_id: str, error: str, processed: int = 0) -> None:
    update_session(
        session_id,
        status="failed",
        processed_products=processed,
        completed_at=datetime.now(timezone.utc).isoformat(),
        error_message=error[:500] if error else None,
    )


def update_progress(session_id: str, processed: int) -> None:
    update_session(session_id, processed_products=processed)


def insert_result(
    session_id: str,
    stok_kodu: str,
    urun_adi: str,
    status: str,
    ai_payload: Optional[dict] = None,
    original: Optional[dict] = None,
    image_url: Optional[str] = None,
    error_message: Optional[str] = None,
    cost_tl: Optional[float] = None,
    verifier_report: Optional[dict] = None,
) -> bool:
    """ai_results'a bir satir ekler. ai_payload VisionEngine ciktisidir."""
    client = _get_client()
    if not client:
        return False

    meta = get_session_meta(session_id)
    if not meta:
        logger.error(f"Session meta yok, result yazilamadi ({session_id[:8]})")
        return False
    org_id, user_id = meta

    row: dict[str, Any] = {
        "session_id": session_id,
        "organization_id": org_id,
        "user_id": user_id,
        "stok_kodu": stok_kodu,
        "urun_adi": urun_adi,
        "status": status,
    }

    if image_url:
        row["image_url"] = image_url
    if error_message:
        row["error_message"] = error_message[:500]
    if cost_tl is not None:
        row["cost_tl"] = round(cost_tl, 4)

    if original:
        row["original_urun_adi"] = original.get("urun_adi")
        row["original_seo_baslik"] = original.get("seo_baslik")
        row["original_seo_aciklama"] = original.get("seo_aciklama")
        row["original_aciklama"] = original.get("aciklama")

    if ai_payload:
        # Temel SEO
        row["ai_urun_adi"] = ai_payload.get("urun_adi")
        row["ai_seo_baslik"] = ai_payload.get("seo_baslik")
        row["ai_seo_aciklama"] = ai_payload.get("seo_aciklama")
        row["ai_onyazi"] = ai_payload.get("onyazi")
        row["ai_aciklama"] = ai_payload.get("aciklama")
        row["ai_anahtar_kelime"] = ai_payload.get("anahtar_kelime")
        row["ai_seo_anahtar_kelime"] = ai_payload.get("seo_anahtar_kelime")

        # GEO/AEO
        geo = ai_payload.get("geo_sss")
        if geo is not None:
            row["ai_geo_sss"] = geo if isinstance(geo, str) else json.dumps(geo, ensure_ascii=False)
        schema = ai_payload.get("schema_jsonld")
        if schema is not None:
            row["ai_schema_jsonld"] = schema if isinstance(schema, str) else json.dumps(schema, ensure_ascii=False)

        # Adwords / kategori
        row["ai_adwords_aciklama"] = ai_payload.get("adwords_aciklama")
        row["ai_adwords_kategori"] = ai_payload.get("adwords_kategori")
        row["ai_adwords_tip"] = ai_payload.get("adwords_tip")
        row["ai_breadcrumb_kat"] = ai_payload.get("breadcrumb_kat")

        # Ticimax özel alanlar
        for i in range(1, 6):
            key = f"ozelalan_{i}"
            val = ai_payload.get(key)
            if val:
                row[f"ai_{key}"] = val

        # Görsel alt taglar
        alt_tags = ai_payload.get("gorsel_alt_tags")
        if alt_tags:
            row["ai_gorsel_alt_tags"] = alt_tags if isinstance(alt_tags, list) else []

        # Denetim katmanı
        cm = ai_payload.get("claim_map")
        if cm is not None:
            row["ai_claim_map"] = cm if isinstance(cm, str) else json.dumps(cm, ensure_ascii=False)
        ig = ai_payload.get("information_gain_skoru")
        if ig is not None:
            row["ai_information_gain"] = int(ig)
        uy = ai_payload.get("uyarilar")
        if uy:
            row["ai_uyarilar"] = uy if isinstance(uy, str) else json.dumps(uy, ensure_ascii=False)

    if verifier_report:
        row["verifier_status"] = verifier_report.get("overall_status")
        row["verifier_summary"] = verifier_report.get("summary")
        issues = verifier_report.get("issues")
        if issues is not None:
            row["verifier_issues"] = issues if isinstance(issues, str) else json.dumps(issues, ensure_ascii=False)
        vc = verifier_report.get("llm_cost_tl")
        if vc is not None:
            row["verifier_cost_tl"] = round(float(vc), 4)

    try:
        client.table("ai_results").insert(row).execute()
        return True
    except Exception as e:
        logger.error(f"Result insert basarisiz ({session_id[:8]}, {stok_kodu}): {e}")
        return False


def clear_session_cache(session_id: str) -> None:
    _session_meta_cache.pop(session_id, None)
