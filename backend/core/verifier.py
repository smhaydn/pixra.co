"""Verifier ajanı — Strategist çıktısını fact-check eder.

İki katmanlı denetim:
1. Deterministic Python (fast, free): char limit, placeholder regex, yasak ifade, claim_map yapı
2. LLM (flash-lite, ~0.02 TL): inferred risk, kaynak doğrulama, SSS kalite, IG formülü

Sonuç merge edilir, VerificationReport döner. main.py bunu Supabase'e yazar ve
fail olursa Strategist'e düzeltme döngüsü başlatır.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from core.prompts.verifier import build_verifier_prompt


# ──────────────── RAPOR ŞEMASI ────────────────

class VerifierIssue(BaseModel):
    category: str  # claim_label | schema_fake | banned_phrase | char_limit | sss_quality | claim_consistency | char_length | placeholder | yasak_ifade
    severity: str  # critical | warning | info
    field: str
    problem: str
    suggestion: str = ""


class VerificationReport(BaseModel):
    overall_status: str = "pass"  # pass | warn | fail
    summary: str = ""
    issues: list[VerifierIssue] = Field(default_factory=list)
    patches: dict[str, Any] = Field(default_factory=dict)
    verified_count: int = 0
    category_rag_count: int = 0
    inferred_count: int = 0
    banned_phrase_count: int = 0
    auto_fixable: bool = True
    llm_cost_tl: float = 0.0


# ──────────────── DETERMINISTIC KONTROLLER ────────────────

PLACEHOLDER_PATTERNS = [
    re.compile(r"example\.(com|org|net)", re.I),
    re.compile(r"placeholder", re.I),
    re.compile(r"\bTODO\b", re.I),
    re.compile(r"\bXXX\b"),
    re.compile(r"lorem ipsum", re.I),
    re.compile(r"your[-_]?domain", re.I),
]

BANNED_PHRASES = [
    "hemen keşfet", "hemen keşfedin", "hemen i̇ncele", "hemen incele",
    "ürünü incele", "ürününü incele", "şıklığını keşfet",
    "şimdi keşfedin", "bedeninizi keşfedin", "hemen sipariş", "kaçırmayın",
    "stoklar tükenmeden", "fırsatı yakalayın",
    "mükemmel", "harika", "muhteşem", "eşsiz", "essiz", "vazgeçilmez",
    "olmazsa olmaz", "en iyi", "en kaliteli", "en uygun",
    "kendinizi özel hissedin", "size özel", "sevdikleriniz için", "tam size göre",
    "tarzınıza tarz katan", "şıklığınıza şıklık",
    "kombinleyebileceğiniz", "kaliteli ve şık", "her zevke hitap eden",
]

CHAR_LIMITS = {
    "seo_baslik": 60,
    "seo_aciklama": 155,
    "adwords_aciklama": 90,
}

VALID_BASIS = {"verified", "category_rag", "inferred"}


def _scan_banned_phrases(payload: dict) -> list[VerifierIssue]:
    issues: list[VerifierIssue] = []
    scan_fields = ["seo_baslik", "seo_aciklama", "onyazi", "aciklama",
                   "adwords_aciklama", "anahtar_kelime", "seo_anahtar_kelime"]

    for field in scan_fields:
        val = payload.get(field)
        if not val or not isinstance(val, str):
            continue
        lower = val.lower()
        for phrase in BANNED_PHRASES:
            if phrase in lower:
                issues.append(VerifierIssue(
                    category="yasak_ifade",
                    severity="warning",
                    field=field,
                    problem=f"Yasak ifade: '{phrase}'",
                    suggestion="Somut fayda veya sayısal veri ile değiştir",
                ))

    # geo_sss cevapları da tara
    geo = payload.get("geo_sss")
    if isinstance(geo, list):
        for i, item in enumerate(geo):
            cevap = (item.get("cevap") or "") if isinstance(item, dict) else ""
            lower = cevap.lower()
            for phrase in BANNED_PHRASES:
                if phrase in lower:
                    issues.append(VerifierIssue(
                        category="yasak_ifade",
                        severity="warning",
                        field=f"geo_sss[{i}].cevap",
                        problem=f"Yasak ifade: '{phrase}'",
                        suggestion="Somut bilgi ile değiştir",
                    ))

    return issues


def _scan_char_limits(payload: dict) -> list[VerifierIssue]:
    issues: list[VerifierIssue] = []
    for field, limit in CHAR_LIMITS.items():
        val = payload.get(field) or ""
        if isinstance(val, str) and len(val) > limit:
            issues.append(VerifierIssue(
                category="char_length",
                severity="critical",
                field=field,
                problem=f"{len(val)} karakter, limit {limit}",
                suggestion=f"İlk {limit} karaktere kısalt",
            ))
    return issues


def _scan_schema_placeholders(payload: dict) -> list[VerifierIssue]:
    issues: list[VerifierIssue] = []
    schema = payload.get("schema_jsonld")
    if not schema:
        return issues

    schema_str = schema if isinstance(schema, str) else json.dumps(schema, ensure_ascii=False)

    for pat in PLACEHOLDER_PATTERNS:
        if pat.search(schema_str):
            issues.append(VerifierIssue(
                category="schema_fake",
                severity="critical",
                field="schema_jsonld",
                problem=f"Placeholder tespit: {pat.pattern}",
                suggestion="Bağlamda verilmemiş offers/url/image alanlarını kaldır",
            ))
    return issues


def _scan_claim_map(payload: dict) -> tuple[list[VerifierIssue], dict[str, int]]:
    issues: list[VerifierIssue] = []
    counts = {"verified": 0, "category_rag": 0, "inferred": 0}

    cm = payload.get("claim_map")
    if isinstance(cm, str):
        try:
            cm = json.loads(cm)
        except Exception:
            issues.append(VerifierIssue(
                category="claim_consistency",
                severity="critical",
                field="claim_map",
                problem="claim_map geçersiz JSON string",
                suggestion="Strategist yeniden çağır",
            ))
            return issues, counts

    if not isinstance(cm, dict):
        issues.append(VerifierIssue(
            category="claim_consistency",
            severity="warning",
            field="claim_map",
            problem="claim_map dict değil",
            suggestion="",
        ))
        return issues, counts

    if len(cm) < 3:
        issues.append(VerifierIssue(
            category="claim_consistency",
            severity="warning",
            field="claim_map",
            problem=f"claim_map çok boş ({len(cm)} kayıt) — içerik muhtemelen genel",
            suggestion="Daha spesifik iddialarla yeniden yaz",
        ))

    for claim_id, entry in cm.items():
        if not isinstance(entry, dict):
            continue
        basis = entry.get("basis")
        if basis not in VALID_BASIS:
            issues.append(VerifierIssue(
                category="claim_label",
                severity="critical",
                field=f"claim_map.{claim_id}",
                problem=f"geçersiz basis: {basis}",
                suggestion="verified | category_rag | inferred",
            ))
            continue
        counts[basis] = counts.get(basis, 0) + 1

        metin = (entry.get("metin") or "").lower()
        if basis == "inferred":
            # Sayısal veya tıbbi iddia inferred olamaz
            if re.search(r"\d+\s*%|\d+\s*(saat|gün|kg|gram|ml|litre|derece)", metin):
                issues.append(VerifierIssue(
                    category="claim_label",
                    severity="critical",
                    field=f"claim_map.{claim_id}",
                    problem=f"Sayısal iddia inferred etiketli: '{entry.get('metin')}'",
                    suggestion="category_rag yap veya iddiayı sil",
                ))
            tibbi = ["anti-bakteriyel", "antibakteriyel", "hipoalerjenik",
                     "ortopedik", "tıbbi", "sertifika", "dermatolojik"]
            if any(t in metin for t in tibbi):
                issues.append(VerifierIssue(
                    category="claim_label",
                    severity="critical",
                    field=f"claim_map.{claim_id}",
                    problem=f"Tıbbi iddia inferred etiketli: '{entry.get('metin')}'",
                    suggestion="Sertifika yoksa iddiayı sil",
                ))

        if basis == "verified":
            kaynak = entry.get("kaynak") or ""
            if not (kaynak.startswith("gorsel:") or kaynak.startswith("meta:")):
                issues.append(VerifierIssue(
                    category="claim_label",
                    severity="warning",
                    field=f"claim_map.{claim_id}",
                    problem=f"verified iddia ama kaynak formatı beklenmiyor: '{kaynak}'",
                    suggestion="kaynak → 'gorsel:...' veya 'meta:...' olmalı",
                ))

            # Kumaş kompozisyonu kuralı: "%X <fiber>" iddiası meta-kaynaklıysa FAIL
            # Meta pazarlama metnidir, kumaş etiketi değil. Oran iddiası için
            # görselde fiziksel etiket görülmeli.
            fiber_words = ("pamuk", "polyester", "elastan", "viskon", "naylon",
                           "poliamid", "akrilik", "yün", "ipek", "keten", "modal",
                           "likra", "spandeks", "lyocell", "tencel")
            ratio_match = re.search(r"%\s*\d{1,3}", metin)
            mentions_fiber = any(f in metin for f in fiber_words)
            if ratio_match and mentions_fiber:
                kaynak_lower = kaynak.lower()
                # Görsel etiket kanıtı gerekli
                has_label_evidence = ("etiket" in kaynak_lower
                                      or "kumas_etiketi" in kaynak_lower
                                      or "composition" in kaynak_lower
                                      or "kompozisyon" in kaynak_lower)
                if not has_label_evidence:
                    issues.append(VerifierIssue(
                        category="claim_label",
                        severity="critical",
                        field=f"claim_map.{claim_id}",
                        problem=(f"Kumaş oran iddiası ({ratio_match.group()}) "
                                 f"görsel etiket kanıtı olmadan verified: '{entry.get('metin')}'"),
                        suggestion=("Oranı kaldır (sadece 'pamuklu' yaz), "
                                    "veya basis'i 'inferred' yapıp metinden % çıkar"),
                    ))

    return issues, counts


def _scan_geo_sss(payload: dict) -> list[VerifierIssue]:
    issues: list[VerifierIssue] = []
    geo = payload.get("geo_sss")
    if isinstance(geo, str):
        try:
            geo = json.loads(geo)
        except Exception:
            return issues
    if not isinstance(geo, list):
        return issues

    for i, item in enumerate(geo):
        if not isinstance(item, dict):
            continue
        soru = item.get("soru") or ""
        cevap = item.get("cevap") or ""

        # Yes/No pattern
        if re.search(r"(var mı|uygun mu|mudur|midir)\s*\??\s*$", soru.strip(), re.I):
            issues.append(VerifierIssue(
                category="sss_quality",
                severity="warning",
                field=f"geo_sss[{i}].soru",
                problem=f"Yes/No yapı: '{soru[:60]}...'",
                suggestion="Açık-uçlu yap (neden/nasıl/farkı)",
            ))

        # Kelime sayısı
        kelime = len(cevap.split())
        if kelime < 25:
            issues.append(VerifierIssue(
                category="sss_quality",
                severity="warning",
                field=f"geo_sss[{i}].cevap",
                problem=f"Kısa cevap ({kelime} kelime, hedef 40-60)",
                suggestion="Kategori bilgisi veya somut veri ekle",
            ))
        elif kelime > 80:
            issues.append(VerifierIssue(
                category="sss_quality",
                severity="warning",
                field=f"geo_sss[{i}].cevap",
                problem=f"Uzun cevap ({kelime} kelime, hedef 40-60)",
                suggestion="Kısalt",
            ))

    return issues


def run_deterministic_checks(payload: dict) -> tuple[list[VerifierIssue], dict[str, int]]:
    """LLM'e gerek olmayan hızlı kontroller."""
    all_issues: list[VerifierIssue] = []
    all_issues.extend(_scan_char_limits(payload))
    all_issues.extend(_scan_schema_placeholders(payload))
    all_issues.extend(_scan_banned_phrases(payload))
    cm_issues, counts = _scan_claim_map(payload)
    all_issues.extend(cm_issues)
    all_issues.extend(_scan_geo_sss(payload))
    return all_issues, counts


# ──────────────── LLM DENETİMİ ────────────────

class VerifierEngine:
    MODEL_NAME = "gemini-2.5-flash-lite"
    PRICE_INPUT_PER_M = 0.075
    PRICE_OUTPUT_PER_M = 0.30
    USD_TO_TRY = 45.0

    def __init__(self, client: genai.Client) -> None:
        self.client = client
        self.last_cost_tl = 0.0

    def _extract_cost(self, response) -> float:
        try:
            meta = response.usage_metadata
            if not meta:
                return 0.0
            input_tokens = getattr(meta, "prompt_token_count", 0) or 0
            output_tokens = getattr(meta, "candidates_token_count", 0) or 0
            cost_usd = (
                input_tokens * self.PRICE_INPUT_PER_M
                + output_tokens * self.PRICE_OUTPUT_PER_M
            ) / 1_000_000
            return round(cost_usd * self.USD_TO_TRY, 4)
        except Exception:
            return 0.0

    def verify_with_llm(
        self,
        strategist_output: dict,
        original_context: str,
    ) -> Optional[dict]:
        """LLM tabanlı denetim — kaynak doğrulama ve kalite değerlendirme."""
        try:
            prompt = build_verifier_prompt(
                strategist_output_json=json.dumps(strategist_output, ensure_ascii=False, indent=2),
                original_context=original_context,
            )
            response = self.client.models.generate_content(
                model=self.MODEL_NAME,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            self.last_cost_tl = self._extract_cost(response)
            return json.loads(response.text)
        except Exception as e:
            print(f"[Verifier] LLM hatası: {e}")
            return None


# ──────────────── BİRLEŞİK DENETİM ────────────────

def verify_strategist_output(
    client: genai.Client,
    strategist_output: dict,
    original_context: str,
    skip_llm: bool = False,
) -> VerificationReport:
    """Ana entry point — deterministic + LLM denetimlerini birleştirir."""
    det_issues, counts = run_deterministic_checks(strategist_output)

    llm_cost_tl = 0.0
    llm_issues: list[VerifierIssue] = []
    llm_patches: dict[str, Any] = {}

    if not skip_llm:
        engine = VerifierEngine(client)
        llm_result = engine.verify_with_llm(strategist_output, original_context)
        llm_cost_tl = engine.last_cost_tl

        if llm_result and isinstance(llm_result, dict):
            for raw in llm_result.get("issues") or []:
                if isinstance(raw, dict):
                    try:
                        llm_issues.append(VerifierIssue(
                            category=raw.get("category", "llm"),
                            severity=raw.get("severity", "warning"),
                            field=raw.get("field", ""),
                            problem=raw.get("problem", ""),
                            suggestion=raw.get("suggestion", ""),
                        ))
                    except Exception:
                        pass
            patches = llm_result.get("patches")
            if isinstance(patches, dict):
                llm_patches = patches

    all_issues = det_issues + llm_issues
    critical = [i for i in all_issues if i.severity == "critical"]
    warnings = [i for i in all_issues if i.severity == "warning"]

    if critical:
        status = "fail"
    elif len(warnings) > 2:
        status = "warn"
    else:
        status = "pass"

    summary_bits = []
    if critical:
        summary_bits.append(f"{len(critical)} kritik")
    if warnings:
        summary_bits.append(f"{len(warnings)} uyarı")
    if not summary_bits:
        summary_bits.append("sorun yok")
    summary = ", ".join(summary_bits)

    banned_count = sum(1 for i in all_issues if i.category == "yasak_ifade")

    return VerificationReport(
        overall_status=status,
        summary=summary,
        issues=all_issues,
        patches=llm_patches,
        verified_count=counts.get("verified", 0),
        category_rag_count=counts.get("category_rag", 0),
        inferred_count=counts.get("inferred", 0),
        banned_phrase_count=banned_count,
        auto_fixable=(status != "fail" or bool(llm_patches)),
        llm_cost_tl=llm_cost_tl,
    )


def apply_patches(strategist_output: dict, patches: dict) -> dict:
    """Verifier'ın önerdiği patch'leri uygular (shallow merge)."""
    if not patches:
        return strategist_output
    merged = dict(strategist_output)
    for key, val in patches.items():
        if val is None:
            merged.pop(key, None)
        else:
            merged[key] = val
    return merged
