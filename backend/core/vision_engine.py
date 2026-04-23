"""Gemini Vision motoru — Strategist+Writer prompt ile entegre.

Pydantic modeli `strategist_writer.py` çıktı şemasıyla bire bir uyumludur.
Kategori-spesifik talimatlar `build_prompt(category_key)` üzerinden gelir.
"""
from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from google import genai
from google.genai import types
from dotenv import load_dotenv

from core.prompts.strategist_writer import build_prompt
from core.prompts.strategy_brief import build_strategy_brief_prompt

load_dotenv()


# ──────────────── PYDANTIC ŞEMA (strategist_writer.py ile uyumlu) ────────────────

class GeoSssItem(BaseModel):
    soru: str
    cevap: str
    intent: str = Field(default="informational")


class ClaimEntry(BaseModel):
    alan: str = Field(..., description="Hangi alanda geçtiği (aciklama, onyazi, geo_sss[0] vb.)")
    metin: str = Field(..., description="İddianın metni")
    basis: str = Field(..., description="verified | category_rag | inferred")
    kaynak: str = Field(..., description="gorsel:..., meta:..., sektör adı vb.")


class ProductAIContent(BaseModel):
    """Strategist+Writer çıktısı — Ticimax 14 alan + claim_map + IG."""

    # ── Temel SEO ──
    urun_adi: str
    seo_baslik: str = Field(..., max_length=80)  # 60 ideal, 80 hard limit
    seo_aciklama: str = Field(..., max_length=200)  # 155 ideal, 200 hard
    anahtar_kelime: str
    seo_anahtar_kelime: str

    # ── İçerik ──
    onyazi: str
    aciklama: str

    # ── Ads / Kategori ──
    adwords_aciklama: str
    adwords_kategori: str
    adwords_tip: str
    breadcrumb_kat: str

    # ── GEO/AEO ──
    geo_sss: list[GeoSssItem]
    schema_jsonld: list[dict]

    # ── Ticimax özel alanlar ──
    ozelalan_1: str = ""
    ozelalan_2: str = ""
    ozelalan_3: str = ""
    ozelalan_4: str = ""
    ozelalan_5: str = ""

    # AI null döndürürse boş string'e çevir
    @field_validator('ozelalan_1', 'ozelalan_2', 'ozelalan_3', 'ozelalan_4', 'ozelalan_5',
                     mode='before')
    @classmethod
    def none_to_empty(cls, v):
        return v if v is not None else ""

    # ── Denetim katmanı ──
    claim_map: dict[str, ClaimEntry] = Field(default_factory=dict)
    information_gain_skoru: int = Field(default=0, ge=0, le=10)
    uyarilar: list[str] = Field(default_factory=list)


# ──────────────── PROMPT BAĞLAM SARMALAYICI ────────────────

def _build_runtime_prompt(
    category_key: str,
    marka: str,
    gorsel_sayisi: int,
    mevcut_urun_adi: str,
    mevcut_aciklama: str,
    mevcut_seo_baslik: str,
    mevcut_seo_aciklama: str,
    kategoriler: str,
    satisfiyati: str,
    stok_kodu: str,
    breadcrumb_kat: str,
    adwords_kategori: str,
    strategy_brief: str = "",
    sector_intelligence: Optional[dict] = None,
) -> str:
    """Sistem prompt'u (strategist_writer) + ürün bağlamı + görev talimatı."""
    base = build_prompt(category_key=category_key, include_fewshot=True)

    coklu_gorsel = ""
    if gorsel_sayisi > 1:
        coklu_gorsel = (
            f"\n**Görsel sayısı:** {gorsel_sayisi} farklı açı/varyant. "
            f"Hepsini birlikte analiz et — renk tutarlılığı, detay tespiti, varyant tespiti yap."
        )

    referans_satirlari = []
    if mevcut_urun_adi:
        referans_satirlari.append(f"- mevcut_urun_adi: {mevcut_urun_adi}")
    if mevcut_seo_baslik:
        referans_satirlari.append(f"- mevcut_seo_baslik: {mevcut_seo_baslik}")
    if mevcut_seo_aciklama:
        referans_satirlari.append(f"- mevcut_seo_aciklama: {mevcut_seo_aciklama}")
    if mevcut_aciklama:
        referans_satirlari.append(f"- mevcut_aciklama: {mevcut_aciklama[:1500]}")
    if kategoriler:
        referans_satirlari.append(f"- kategoriler: {kategoriler}")
    if breadcrumb_kat:
        referans_satirlari.append(f"- breadcrumb: {breadcrumb_kat}")
    if adwords_kategori:
        referans_satirlari.append(f"- mevcut_adwords_kategori: {adwords_kategori}")
    if satisfiyati:
        referans_satirlari.append(f"- satis_fiyati_TL: {satisfiyati}")
    if stok_kodu:
        referans_satirlari.append(f"- stok_kodu: {stok_kodu}")

    referans_blogu = "\n".join(referans_satirlari) or "- (Ek meta yok — yalnız görselden çalış)"

    # ── Sektör İstihbarat Bloğu ──────────────────────────────────────
    sektor_block = ""
    if sector_intelligence:
        import json as _json
        from datetime import datetime as _dt
        current_month = _dt.now().strftime("%B")  # Ocak, Şubat ...
        sektor_adi = sector_intelligence.get("display_name", "")
        lines = [f"\n---\n\n# SEKTÖR İSTİHBARAT VERİSİ — {sektor_adi}\n"]
        lines.append(
            "Bu veriyi tüm içerik üretiminde kullan. "
            "Anahtar kelimeleri doğal dil içine yerleştir, "
            "FAQ sorularını geo_sss'e dönüştür, schema kalıplarını takip et.\n"
        )
        kws = sector_intelligence.get("keywords")
        if kws:
            lines.append(f"### Bu Sektörde Çalışan Anahtar Kelimeler\n```json\n{_json.dumps(kws, ensure_ascii=False, indent=2)[:1500]}\n```\n")
        faqs = sector_intelligence.get("faq")
        if faqs:
            lines.append(f"### Alıcıların Gerçek Soruları (FAQ Kalıpları)\n```json\n{_json.dumps(faqs, ensure_ascii=False, indent=2)[:1200]}\n```\n")
        comp = sector_intelligence.get("competitor")
        if comp:
            lines.append(f"### Rakip SEO Kalıpları\n```json\n{_json.dumps(comp, ensure_ascii=False, indent=2)[:800]}\n```\n")
        seasonal = sector_intelligence.get("seasonal")
        if seasonal:
            lines.append(f"### Mevsimsel Öncelik ({current_month})\n```json\n{_json.dumps(seasonal, ensure_ascii=False, indent=2)[:600]}\n```\n")
        sektor_block = "".join(lines)

    strategy_block = ""
    if strategy_brief:
        strategy_block = f"""
---

# MÜŞTERİ STRATEJİ BRİFİNGİ (Pass 1 analizi — içeriğe entegre et)

Aşağıdaki strateji analizi bu ürün için hazırlandı.
İçerik üretirken **müşteri profilini**, **JTBD'yi** ve **intent gap'lerini** karşıla.
Özellikle `geo_sss` sorularını bu gap'lerden türet.

{strategy_brief}

"""

    runtime_block = f"""\
---

# ÜRÜN BAĞLAMI (Bu ürün için somut veri)

**Marka:** {marka}
**Sektör (kategori_key):** {category_key}{coklu_gorsel}

## Ticimax meta verileri
{referans_blogu}

## KAYNAK ÖNCELİK SIRASI (Halüsinasyon politikası)
1. **Görsel** → `verified` etiketli iddialar için birincil kaynak
2. **Yukarıdaki Ticimax meta** → `verified` etiketli iddialar için ikincil kaynak
3. **Sektör genel bilgisi (kategori talimatı)** → `category_rag` etiketli iddialar
4. **Mantıksal çıkarım** → `inferred` etiketli (sayısal/tıbbi iddia için ASLA)

Yukarıdaki kaynaklar dışında bilgi UYDURMA. Boş kalan ozelalan_X'i boş bırak.

---

# GÖREV

Yukarıdaki tüm kuralları (rol, halüsinasyon, claim enforcement, karakter limit
self-check, IG rubric, yasaklı ifadeler, kategori talimatları, negatif/pozitif
örnekler) UYGULA ve bu ürün için JSON çıktıyı üret.

**Yalnız ve yalnız geçerli JSON döndür.** Markdown kod bloğu, açıklama, yorum YOK.
"""

    return base + sektor_block + strategy_block + runtime_block


# ──────────────── VISION ENGINE ────────────────

class VisionEngine:
    MODEL_NAME = "gemini-2.5-flash"
    BRIEF_MODEL = "gemini-2.5-flash-lite"   # Pass 1: metin-tabanlı, ucuz
    FALLBACK_MODEL = "gemini-2.5-flash-lite"

    PRICE_INPUT_PER_M = 0.30
    PRICE_OUTPUT_PER_M = 2.50
    USD_TO_TRY = 45.0

    # Pass 3 tetikleme eşiği: IG skoru bu değerin altındaysa iyileştirme çalışır
    REFINE_TRIGGER_IG = 5

    DEFAULT_CATEGORY_KEY = "ic_giyim"

    def __init__(self, api_key: Optional[str] = None) -> None:
        resolved_key = api_key or os.getenv("GEMINI_API_KEY")
        if not resolved_key:
            raise ValueError("GEMINI_API_KEY eksik.")

        self.client = genai.Client(api_key=resolved_key)
        self.last_usage = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "cost_tl": 0.0}

        try:
            list(self.client.models.list())
        except Exception as e:
            raise ValueError(f"Gemini API Key geçersiz: {str(e)}")

    def _extract_usage(self, response) -> None:
        try:
            meta = response.usage_metadata
            if meta:
                input_tokens = getattr(meta, "prompt_token_count", 0) or 0
                output_tokens = getattr(meta, "candidates_token_count", 0) or 0
                cost_usd = (
                    input_tokens * self.PRICE_INPUT_PER_M
                    + output_tokens * self.PRICE_OUTPUT_PER_M
                ) / 1_000_000
                cost_tl = cost_usd * self.USD_TO_TRY
                self.last_usage = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": round(cost_usd, 6),
                    "cost_tl": round(cost_tl, 4),
                }
        except Exception:
            pass

    def _generate_strategy_brief(
        self,
        marka: str,
        kategori: str,
        urun_adi: str,
        aciklama: str,
        fiyat: str,
    ) -> str:
        """Pass 1 — Metin tabanlı müşteri strateji brifing üretimi.

        Görselsiz, Flash Lite model ile çalışır (~0.005 TL).
        Başarısız olursa sessizce boş döner (Pass 2 yine de çalışır).
        """
        try:
            brief_prompt = build_strategy_brief_prompt(
                marka=marka,
                kategori=kategori,
                urun_adi=urun_adi,
                aciklama=aciklama,
                fiyat=fiyat,
            )
            response = self.client.models.generate_content(
                model=self.BRIEF_MODEL,
                contents=[brief_prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            # Maliyet Pass 1'e ekle (ayrı takip)
            try:
                meta = response.usage_metadata
                if meta:
                    in_tok = getattr(meta, "prompt_token_count", 0) or 0
                    out_tok = getattr(meta, "candidates_token_count", 0) or 0
                    cost_usd = (in_tok * self.PRICE_INPUT_PER_M + out_tok * self.PRICE_OUTPUT_PER_M) / 1_000_000
                    self.last_usage["cost_usd"] = round(self.last_usage.get("cost_usd", 0) + cost_usd, 6)
                    self.last_usage["cost_tl"] = round(self.last_usage["cost_usd"] * self.USD_TO_TRY, 4)
            except Exception:
                pass
            return response.text or ""
        except Exception as e:
            print(f"[VisionEngine] Pass 1 (strategy brief) atlandı: {e}")
            return ""

    def _refine_content(
        self,
        result: ProductAIContent,
        verifier_issues: list[str],
    ) -> ProductAIContent:
        """Pass 3 — Koşullu iyileştirme (IG < 5 veya kritik verifier hatası).

        Mevcut çıktıyı + sorunları gösterip spesifik düzeltme ister.
        Başarısız olursa orijinal result döner.
        """
        if not verifier_issues:
            return result

        issues_text = "\n".join(f"- {i}" for i in verifier_issues)
        refine_prompt = f"""\
Aşağıdaki SEO/GEO içerik çıktısında belirtilen sorunları gider.
Sorunlara dokunmayan alanları DEĞIŞTIRME.
Yalnızca geçerli JSON döndür.

## Tespit Edilen Sorunlar
{issues_text}

## Mevcut Çıktı
{result.model_dump_json(indent=2)[:6000]}

## Kurallar
- seo_baslik ≤ 60 karakter
- seo_aciklama ≤ 155 karakter
- adwords_aciklama ≤ 90 karakter
- geo_sss: yes/no sorular değil, açık-uçlu "neden/nasıl/farkı nedir" soruları
- Yasaklı CTA: "Hemen Keşfet", "Kaçırmayın", "Hemen İncele"
- claim_map: tüm spesifik iddialar etiketli olmalı
"""
        try:
            response = self.client.models.generate_content(
                model=self.BRIEF_MODEL,
                contents=[refine_prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            self._extract_usage(response)
            refined = ProductAIContent.model_validate_json(response.text)
            refined.uyarilar = (refined.uyarilar or []) + ["[Pass 3] İyileştirme uygulandı"]
            return refined
        except Exception as e:
            print(f"[VisionEngine] Pass 3 (refine) atlandı: {e}")
            return result

    def _detect_category_key(self, kategoriler: str, breadcrumb_kat: str) -> str:
        """Kategori sezgisi — kategori şablonu seçimi için."""
        text = f"{kategoriler} {breadcrumb_kat}".lower()
        if any(k in text for k in ["sütyen", "iç giyim", "külot", "korse", "sütyan"]):
            return "ic_giyim"
        if any(k in text for k in ["çanta", "el çantası", "omuz çantası", "sırt çantası"]):
            return "kadin_canta"
        if any(k in text for k in ["takı", "gümüş", "kolye", "yüzük", "küpe", "bileklik"]):
            return "gumus_taki"
        if any(k in text for k in ["matkap", "vida", "çekiç", "anahtar", "tornavida", "hırdavat"]):
            return "hirdavat"
        if any(k in text for k in ["ayakkabı", "bot", "sandalet", "terlik", "sneaker"]):
            return "ayakkabi"
        if any(k in text for k in ["elbise", "etek", "bluz", "pantolon", "kazak", "mont", "ceket", "gömlek"]):
            return "kadin_giyim"
        return self.DEFAULT_CATEGORY_KEY

    def generate_alt_text(
        self,
        image_path: str,
        urun_adi: str = "",
        kategori: str = "",
        marka: str = "",
    ) -> str:
        """Görsel için semantik, SEO uyumlu alt-text üretir.

        Google Images + multimodal AI alıntılaması için kritik.
        Mevcut: 'urun_gorseli_001.jpg' → Hedef: 'Krem rengi nervürlü pamuklu crop top, V-yaka, Lola of Shine'
        Maliyet: ~0.004 TL/görsel (Flash Lite, tek görsel)
        """
        context_parts = []
        if marka:
            context_parts.append(f"Marka: {marka}")
        if kategori:
            context_parts.append(f"Kategori: {kategori}")
        if urun_adi:
            context_parts.append(f"Ürün adı: {urun_adi}")
        context_str = " | ".join(context_parts) if context_parts else ""

        prompt = f"""\
Bu ürün görselini tanımla ve HTML alt-text için kısa, bilgilendirici bir açıklama yaz.

Kurallar:
- Max 125 karakter
- Türkçe yaz
- Renk, materyal, kesim, şekil, öne çıkan detay — en fazla 3-4 özellik
- Marka adı varsa sona ekle
- "resim", "fotoğraf", "görsel" gibi gereksiz kelime KULLANMA
- Keyword stuffing yapma, doğal dil kullan

{f"Bağlam: {context_str}" if context_str else ""}

Yalnızca alt-text metnini döndür. Tırnak, açıklama, ek metin YOK.
"""
        uploaded = None
        try:
            if not os.path.exists(image_path):
                return urun_adi or ""
            uploaded = self.client.files.upload(file=image_path)
            response = self.client.models.generate_content(
                model=self.BRIEF_MODEL,
                contents=[prompt, uploaded],
                config=types.GenerateContentConfig(temperature=0.2),
            )
            alt_text = (response.text or "").strip().strip('"').strip("'")
            return alt_text[:125]
        except Exception as e:
            print(f"[VisionEngine] Alt-text üretimi başarısız: {e}")
            return urun_adi or ""
        finally:
            if uploaded:
                try:
                    self.client.files.delete(name=uploaded.name)
                except Exception:
                    pass

    def analyze_product_image(
        self,
        image_path: str,
        marka: str = "Bilinmeyen Marka",
        adwords_aciklama: str = "",
        adwords_kategori: str = "",
        adwords_tip: str = "",
        breadcrumb_kat: str = "",
        image_paths: Optional[list] = None,
        mevcut_urun_adi: str = "",
        satisfiyati: str = "",
        kategoriler: str = "",
        stok_kodu: str = "",
        reference_content: str = "",
        category_key: Optional[str] = None,
        sector_intelligence: Optional[dict] = None,
    ) -> ProductAIContent:
        """Ana analiz fonksiyonu — yeni Strategist+Writer prompt ile."""
        # reference_content'i parçala (geriye uyumluluk için main.py değiştirmeden)
        mevcut_aciklama = ""
        mevcut_seo_baslik = ""
        mevcut_seo_aciklama = ""
        if reference_content:
            for line in reference_content.split("\n"):
                if line.startswith("MEVCUT ACIKLAMA:"):
                    mevcut_aciklama = line.replace("MEVCUT ACIKLAMA:", "").strip()
                elif line.startswith("MEVCUT SEO ACIKLAMA:"):
                    mevcut_seo_aciklama = line.replace("MEVCUT SEO ACIKLAMA:", "").strip()
                elif line.startswith("MEVCUT SEO BASLIK:"):
                    mevcut_seo_baslik = line.replace("MEVCUT SEO BASLIK:", "").strip()

        resolved_category = category_key or self._detect_category_key(kategoriler, breadcrumb_kat)

        # ── PASS 1: Strateji Brifing (metin-tabanlı, görselsiz, ucuz) ──────────
        strategy_brief = self._generate_strategy_brief(
            marka=marka,
            kategori=f"{kategoriler} {breadcrumb_kat}".strip(),
            urun_adi=mevcut_urun_adi,
            aciklama=mevcut_aciklama,
            fiyat=satisfiyati,
        )
        if strategy_brief:
            print(f"[VisionEngine] Pass 1 (strateji) tamamlandı.")

        uploaded_files = []
        try:
            paths_to_upload = image_paths if image_paths else [image_path]
            for path in paths_to_upload:
                if path and os.path.exists(path):
                    uploaded = self.client.files.upload(file=path)
                    uploaded_files.append(uploaded)

            if not uploaded_files:
                raise ValueError("Yüklenecek geçerli görsel bulunamadı.")

            # ── PASS 2: İçerik Üretimi (vision + strateji brifing ile) ─────────
            prompt = _build_runtime_prompt(
                category_key=resolved_category,
                marka=marka,
                gorsel_sayisi=len(uploaded_files),
                mevcut_urun_adi=mevcut_urun_adi,
                mevcut_aciklama=mevcut_aciklama,
                mevcut_seo_baslik=mevcut_seo_baslik,
                mevcut_seo_aciklama=mevcut_seo_aciklama,
                kategoriler=kategoriler,
                satisfiyati=satisfiyati,
                stok_kodu=stok_kodu,
                breadcrumb_kat=breadcrumb_kat,
                adwords_kategori=adwords_kategori,
                strategy_brief=strategy_brief,
                sector_intelligence=sector_intelligence,
            )

            content_parts = [prompt] + uploaded_files
            model_to_use = self.MODEL_NAME

            try:
                response = self.client.models.generate_content(
                    model=model_to_use,
                    contents=content_parts,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.4,
                    ),
                )
            except Exception as primary_err:
                err_str = str(primary_err)
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    print(f"[VisionEngine] {model_to_use} 503, fallback: {self.FALLBACK_MODEL}")
                    model_to_use = self.FALLBACK_MODEL
                    response = self.client.models.generate_content(
                        model=model_to_use,
                        contents=content_parts,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.4,
                        ),
                    )
                else:
                    raise

            self._extract_usage(response)
            result = ProductAIContent.model_validate_json(response.text)

            # ── PASS 3: Koşullu İyileştirme (IG düşükse veya kritik sorun varsa) ─
            if result.information_gain_skoru < self.REFINE_TRIGGER_IG:
                refine_issues = [f"information_gain_skoru = {result.information_gain_skoru} (hedef ≥ 5)"]
                # Yasaklı ifade tespiti (basit kontrol)
                banned_check_text = f"{result.seo_aciklama} {result.aciklama}"
                quick_banned = [
                    "Hemen Keşfet", "Hemen İncele", "vazgeçilmez", "olmazsa olmaz",
                    "Kaçırmayın", "günlük kullanım için uygun mu",
                ]
                for phrase in quick_banned:
                    if phrase.lower() in banned_check_text.lower():
                        refine_issues.append(f"Yasaklı ifade tespit edildi: '{phrase}'")
                print(f"[VisionEngine] Pass 3 tetiklendi (IG={result.information_gain_skoru}): {len(refine_issues)} sorun")
                result = self._refine_content(result, refine_issues)

            return result

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                raise RuntimeError(
                    "Gemini API kota limiti aşıldı. Google AI Studio'dan "
                    "faturalandırma aktif edin veya bekleyin."
                )
            elif "403" in err_str or "PERMISSION_DENIED" in err_str:
                raise RuntimeError(
                    "Gemini API erişim engeli. API Key geçerli mi ve "
                    "Generative Language API aktif mi kontrol edin."
                )
            elif "503" in err_str or "UNAVAILABLE" in err_str:
                raise RuntimeError(
                    "Gemini modeli şu an yoğun. Birkaç dakika sonra tekrar deneyin."
                )
            raise RuntimeError(f"Görsel analizi hatası: {err_str}")
        finally:
            for f in uploaded_files:
                try:
                    self.client.files.delete(name=f.name)
                except Exception:
                    pass
