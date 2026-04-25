from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import uuid
import time
import os
import tempfile
import traceback
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv

from core.ticimax_api import TicimaxClient
from core.vision_engine import VisionEngine
from core.helpers import get_field, download_image, safe_file_cleanup
from core import supabase_sync as sb

load_dotenv()

app = FastAPI(title="Pixra Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────── IN-MEMORY DEPOLAR ────────────────

sessions_db: Dict[str, dict] = {}      # session_id -> durum
results_db: Dict[str, list] = {}       # session_id -> sonuclar
products_cache: Dict[str, dict] = {}   # stok_kodu -> urun bilgisi (fetch sirasinda doldurulur)

MAX_IMAGES_PER_PRODUCT = 3
RATE_LIMIT_DELAY = 3
MAX_RETRIES = 3
COST_LIMIT_TL = 100.0  # Maliyet limiti (TL)


# ──────────────── GEMINI KEY POOL ────────────────

import threading as _threading
_key_pool: List[str] = []
_key_pool_idx: int = 0
_key_pool_lock = _threading.Lock()
_key_pool_loaded_at: float = 0.0
_KEY_POOL_TTL = 300  # 5 dakikada bir yenile


def _load_key_pool() -> List[str]:
    """Supabase'den aktif Gemini key'lerini çeker."""
    try:
        import httpx
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            return []
        resp = httpx.get(
            f"{url}/rest/v1/gemini_keys",
            params={"is_active": "eq.true", "select": "api_key"},
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            timeout=5,
        )
        if resp.status_code == 200:
            return [r["api_key"] for r in resp.json() if r.get("api_key")]
    except Exception as e:
        print(f"[KEY POOL] Yüklenemedi: {e}")
    return []


def get_gemini_key(requested_key: str = "") -> str:
    """
    Öncelik sırası:
    1. Kullanıcıdan gelen key (varsa)
    2. Admin key pool'undan round-robin
    3. GEMINI_API_KEY env var fallback
    """
    if requested_key:
        return requested_key

    global _key_pool, _key_pool_idx, _key_pool_loaded_at
    with _key_pool_lock:
        if time.time() - _key_pool_loaded_at > _KEY_POOL_TTL:
            _key_pool = _load_key_pool()
            _key_pool_loaded_at = time.time()
            print(f"[KEY POOL] {len(_key_pool)} adet aktif Gemini key yüklendi")

        if _key_pool:
            key = _key_pool[_key_pool_idx % len(_key_pool)]
            _key_pool_idx += 1
            return key

    return os.getenv("GEMINI_API_KEY", "")


# ──────────────── MODELLER ────────────────

class FetchProductsRequest(BaseModel):
    domain_url: str
    ws_kodu: str
    organization_id: Optional[str] = None
    force_refresh: bool = False

class AnalyzeRequest(BaseModel):
    ws_kodu: str
    api_key: str
    selected_products: List[str]
    firma_kodu: str
    domain_url: str = ""
    brand_name: str = ""
    session_id: str | None = None
    organization_id: str | None = None


class SendToTicimaxRequest(BaseModel):
    domain_url: str
    ws_kodu: str
    products: List[Dict[str, Any]]  # [{stok_kodu, urun_adi, seo_baslik, seo_aciklama, seo_anahtarkelime, aciklama, ...}]


class FirmaProfilRequest(BaseModel):
    organization_id: str
    profil: Dict[str, Any]  # 10 soruluk anket cevapları


class LlmsTxtRequest(BaseModel):
    organization_id: str
    firma_adi: str = ""
    domain_url: str = ""


class AltTextRequest(BaseModel):
    domain_url: str
    ws_kodu: str
    stok_kodlari: List[str]  # Alt-text üretilecek ürünlerin stok kodları


# ──────────────── YARDIMCI ────────────────

def _load_sector_intelligence(organization_id: str) -> Optional[dict]:
    """
    Firmanın sector_id'sini al, o sektör için tüm sector_intelligence
    kayıtlarını quality_score'a göre sırala, katman bazlı birleştir.
    Dönen dict: {display_name, keywords, faq, schema, competitor, seasonal}
    """
    try:
        import httpx
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            return None

        headers = {"apikey": key, "Authorization": f"Bearer {key}"}

        # 1. Firmanın sector_id'sini çek
        r = httpx.get(
            f"{url}/rest/v1/organizations",
            params={"id": f"eq.{organization_id}", "select": "sector_id,hedef_kitle"},
            headers=headers, timeout=5
        )
        if r.status_code != 200 or not r.json():
            return None
        org = r.json()[0]
        sector_id = org.get("sector_id")
        if not sector_id:
            return None

        # 2. Sektör adını çek
        rs = httpx.get(
            f"{url}/rest/v1/sectors",
            params={"id": f"eq.{sector_id}", "select": "slug,display_name"},
            headers=headers, timeout=5
        )
        if rs.status_code != 200 or not rs.json():
            return None
        sector = rs.json()[0]

        # 3. sector_intelligence kayıtlarını çek (quality_score'a göre desc)
        ri = httpx.get(
            f"{url}/rest/v1/sector_intelligence",
            params={
                "sector_id": f"eq.{sector_id}",
                "select": "data_type,content,quality_score",
                "order": "quality_score.desc",
                "limit": "50"
            },
            headers=headers, timeout=5
        )
        if ri.status_code != 200:
            return None

        rows = ri.json()
        result: dict = {
            "display_name": sector["display_name"],
            "slug": sector["slug"],
        }

        # Her data_type için en yüksek quality_score'lu içerikleri birleştir
        for row in rows:
            dt = row["data_type"]
            if dt not in result:
                result[dt] = row["content"]

        # Firma hedef_kitle'si varsa ekle
        if org.get("hedef_kitle"):
            result["hedef_kitle"] = org["hedef_kitle"]

        return result if len(result) > 2 else None  # En az 1 katman olmalı

    except Exception as e:
        print(f"[SECTOR INTEL] Yüklenemedi ({organization_id[:8]}): {e}")
        return None


def _build_wsdl_url(domain_url: str) -> str:
    base_url = domain_url
    if not base_url.startswith("http"):
        base_url = "https://" + base_url
    if not base_url.endswith("WSDL"):
        base_url = f"{base_url.rstrip('/')}/Servis/UrunServis.svc?WSDL"
    return base_url


def _extract_image_urls(urun) -> list:
    """Ticimax urun objesinden gorsel URL'lerini cikarir."""
    urls = []

    resimler = get_field(urun, 'Resimler', None)
    if resimler:
        # Format 1: ArrayOfstring — {'string': ['url1', 'url2', ...]}
        if hasattr(resimler, 'string') and resimler.string:
            for url in resimler.string:
                if url and isinstance(url, str) and url.startswith('http'):
                    urls.append(url)
        elif isinstance(resimler, dict) and 'string' in resimler:
            for url in resimler['string']:
                if url and isinstance(url, str) and url.startswith('http'):
                    urls.append(url)
        # Format 2: UrunResim listesi
        elif hasattr(resimler, 'UrunResim') and resimler.UrunResim:
            for r in resimler.UrunResim:
                url = (get_field(r, 'Buyuk', '')
                       or get_field(r, 'Orta', '')
                       or get_field(r, 'Kucuk', ''))
                if url and isinstance(url, str) and url.startswith('http'):
                    urls.append(url)
        # Format 3: Duz liste
        elif isinstance(resimler, list):
            for item in resimler:
                if isinstance(item, str) and item.startswith('http'):
                    urls.append(item)

    # Fallback: tekli resim alanlari
    if not urls:
        for field_name in ['Resim', 'ResimUrl', 'Resim1', 'BuyukResim',
                           'OrtaResim', 'KucukResim', 'ResimYol']:
            val = get_field(urun, field_name, '')
            if val and isinstance(val, str) and val.startswith('http'):
                urls.append(val)

    return urls[:MAX_IMAGES_PER_PRODUCT]


def _extract_stok_kodu(urun) -> str:
    """Ticimax urun objesinden benzersiz stok kodunu cikarir.
    Format: ID (her zaman benzersiz) kullanilir."""
    urun_id = get_field(urun, 'ID', get_field(urun, 'UrunKartiID', ''))
    return str(urun_id)


def _log(session_id: str, msg: str):
    """Session log'una mesaj ekler ve konsola da basar."""
    print(f"[{session_id[:8]}] {msg}")
    if session_id in sessions_db:
        sessions_db[session_id].setdefault("logs", []).append(msg)


# ──────────────── URUN FETCH ────────────────

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Pixra backend API is running"}


def _sb_load_products(organization_id: str) -> Optional[list]:
    """Supabase'den cache'lenmiş ürünleri yükler. 2 saatten eskiyse None döner."""
    try:
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not supabase_url or not supabase_key:
            return None
        import httpx
        resp = httpx.get(
            f"{supabase_url}/rest/v1/ticimax_products",
            params={"organization_id": f"eq.{organization_id}", "select": "*", "limit": "5000"},
            headers={"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"},
            timeout=10
        )
        if resp.status_code != 200 or not resp.json():
            return None
        rows = resp.json()
        # En son fetch zamanını kontrol et (2 saat TTL)
        from datetime import timedelta
        latest = max(r["fetched_at"] for r in rows)
        fetched_dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) - fetched_dt > timedelta(hours=2):
            return None
        return rows
    except Exception as e:
        print(f"[CACHE LOAD] Hata: {e}")
        return None


def _sb_save_products(organization_id: str, rows: list):
    """Ürünleri Supabase'e toplu upsert eder."""
    try:
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not supabase_url or not supabase_key:
            return
        import httpx
        # Önce bu org'un eski ürünlerini sil
        httpx.delete(
            f"{supabase_url}/rest/v1/ticimax_products",
            params={"organization_id": f"eq.{organization_id}"},
            headers={"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"},
            timeout=10
        )
        # Yeni ürünleri batch insert (500'er)
        batch_size = 500
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            httpx.post(
                f"{supabase_url}/rest/v1/ticimax_products",
                json=batch,
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                timeout=30
            )
        print(f"[CACHE SAVE] {len(rows)} ürün Supabase'e kaydedildi.")
    except Exception as e:
        print(f"[CACHE SAVE] Hata: {e}")


@app.post("/api/products/fetch")
def fetch_products(req: FetchProductsRequest):
    """Supabase cache varsa oradan, yoksa Ticimax'ten çeker."""
    try:
        # ── Supabase cache kontrolü ──
        if req.organization_id and not req.force_refresh:
            cached_rows = _sb_load_products(req.organization_id)
            if cached_rows:
                formatted = []
                for r in cached_rows:
                    resim_urls = r.get("resim_urls") or []
                    products_cache[r["internal_key"]] = {
                        "raw": None,
                        "urun_adi": r["urun_adi"],
                        "resim_urls": resim_urls,
                        "stok_kodu": r["display_stok"],
                        "marka": r["marka"],
                        "satis_fiyati": r["satis_fiyati"],
                        "mevcut_aciklama": r["mevcut_aciklama"],
                        "mevcut_seo_anahtar": r["mevcut_seo_anahtar"],
                        "mevcut_seo_aciklama": r["mevcut_seo_aciklama"],
                        "ana_kategori": r["ana_kategori"],
                        "adwords_aciklama": r.get("adwords_aciklama", ""),
                        "adwords_kategori": r.get("adwords_kategori", ""),
                        "adwords_tip": r.get("adwords_tip", ""),
                        "breadcrumb_kat": r.get("breadcrumb_kat", ""),
                        "kategoriler": r.get("kategoriler", ""),
                    }
                    formatted.append({
                        "id": 0,
                        "stok_kodu": r["internal_key"],
                        "display_stok": r["display_stok"],
                        "urun_adi": r["urun_adi"],
                        "resim_url": r.get("resim_url_ilk", ""),
                    })
                print(f"[CACHE HIT] {len(formatted)} ürün Supabase'den yüklendi.")
                return {"status": "success", "products": formatted, "total": len(formatted), "from_cache": True}

        wsdl_url = _build_wsdl_url(req.domain_url)
        print(f"[FETCH] Ticimax WSDL: {wsdl_url}")
        client = TicimaxClient(base_url=wsdl_url, uye_kodu=req.ws_kodu)

        tum_urunler = []
        sb_rows_to_save = []
        sayfa_boyutu = 100
        baslangic = 0

        while True:
            sayfalama = {
                'BaslangicIndex': baslangic,
                'KayitSayisi': sayfa_boyutu,
                'KayitSayisinaGoreGetir': True,
                'SiralamaDegeri': 'id',
                'SiralamaYonu': 'Asc'
            }
            res = client.client.service.SelectUrun(
                UyeKodu=client.uye_kodu, f={'Aktif': 1}, s=sayfalama
            )

            sayfa_urunler = []
            if res:
                if hasattr(res, 'Urunler') and res.Urunler:
                    sayfa_urunler = res.Urunler
                elif hasattr(res, 'UrunKarti') and res.UrunKarti:
                    sayfa_urunler = res.UrunKarti
                elif isinstance(res, list):
                    sayfa_urunler = res
                else:
                    sayfa_urunler = [res]

            if not sayfa_urunler:
                break

            tum_urunler.extend(sayfa_urunler)

            if len(sayfa_urunler) < sayfa_boyutu:
                break

            baslangic += sayfa_boyutu

        print(f"[FETCH] Toplam {len(tum_urunler)} urun cekildi")

        # UI icin formatla VE cache'e kaydet
        formatted = []
        for u in tum_urunler:
            urun_id = get_field(u, 'ID', get_field(u, 'UrunKartiID', 0))
            internal_key = str(urun_id)  # Benzersiz anahtar
            urun_adi = str(get_field(u, 'UrunAdi',
                                     get_field(u, 'Tanim', "Isimsiz Urun")))
            resim_urls = _extract_image_urls(u)

            # Gosterim icin varyasyon stok kodu
            display_stok = ""
            varyasyonlar = get_field(u, 'Varyasyonlar', None)
            if varyasyonlar:
                varys = None
                if hasattr(varyasyonlar, 'Varyasyon'):
                    varys = varyasyonlar.Varyasyon
                elif isinstance(varyasyonlar, dict) and 'Varyasyon' in varyasyonlar:
                    varys = varyasyonlar['Varyasyon']
                if varys and isinstance(varys, list) and len(varys) > 0:
                    display_stok = str(get_field(varys[0], 'StokKodu', ''))

            tk = get_field(u, 'TedarikciKodu', None)
            if tk and str(tk).strip():
                display_stok = str(tk).strip()

            if not display_stok:
                display_stok = internal_key

            # SatisFiyati — varyasyondan al
            satis_fiyati = ""
            if varyasyonlar:
                varys = None
                if hasattr(varyasyonlar, 'Varyasyon'):
                    varys = varyasyonlar.Varyasyon
                elif isinstance(varyasyonlar, dict) and 'Varyasyon' in varyasyonlar:
                    varys = varyasyonlar['Varyasyon']
                if varys and isinstance(varys, list) and len(varys) > 0:
                    sf = get_field(varys[0], 'SatisFiyati', '')
                    if sf:
                        satis_fiyati = str(sf)

            # Mevcut urun aciklamasi ve SEO bilgilerini al
            mevcut_aciklama = str(get_field(u, 'Aciklama', ''))
            mevcut_seo_anahtar = str(get_field(u, 'SeoAnahtarKelime', ''))
            mevcut_seo_aciklama = str(get_field(u, 'SeoSayfaAciklama', ''))
            ana_kategori = str(get_field(u, 'AnaKategori', ''))
            adwords_aciklama = str(get_field(u, 'AdwordsAciklama', ''))
            adwords_kategori = str(get_field(u, 'AdwordsKategori', ''))
            adwords_tip = str(get_field(u, 'AdwordsTip', ''))
            breadcrumb_kat = str(get_field(u, 'BreadcrumbKat', ''))
            kategoriler = str(get_field(u, 'Kategoriler', ''))
            marka = str(get_field(u, 'Marka', ''))

            products_cache[internal_key] = {
                "raw": u,
                "urun_adi": urun_adi,
                "resim_urls": resim_urls,
                "stok_kodu": display_stok,
                "marka": marka,
                "satis_fiyati": satis_fiyati,
                "mevcut_aciklama": mevcut_aciklama,
                "mevcut_seo_anahtar": mevcut_seo_anahtar,
                "mevcut_seo_aciklama": mevcut_seo_aciklama,
                "ana_kategori": ana_kategori,
                "adwords_aciklama": adwords_aciklama,
                "adwords_kategori": adwords_kategori,
                "adwords_tip": adwords_tip,
                "breadcrumb_kat": breadcrumb_kat,
                "kategoriler": kategoriler,
            }

            sb_rows_to_save.append({
                "organization_id": req.organization_id,
                "internal_key": internal_key,
                "urun_adi": urun_adi,
                "display_stok": display_stok,
                "resim_urls": resim_urls,
                "resim_url_ilk": resim_urls[0] if resim_urls else "",
                "marka": marka,
                "satis_fiyati": satis_fiyati,
                "mevcut_aciklama": mevcut_aciklama,
                "mevcut_seo_anahtar": mevcut_seo_anahtar,
                "mevcut_seo_aciklama": mevcut_seo_aciklama,
                "ana_kategori": ana_kategori,
                "adwords_aciklama": adwords_aciklama,
                "adwords_kategori": adwords_kategori,
                "adwords_tip": adwords_tip,
                "breadcrumb_kat": breadcrumb_kat,
                "kategoriler": kategoriler,
            })

            formatted.append({
                "id": int(urun_id) if str(urun_id).isdigit() else 0,
                "stok_kodu": internal_key,
                "display_stok": display_stok,
                "urun_adi": urun_adi,
                "resim_url": resim_urls[0] if resim_urls else "",
            })

        if not formatted:
            raise Exception("Bos urun listesi")

        print(f"[FETCH] {len(formatted)} urun cache'e kaydedildi. "
              f"Gorsel olan: {sum(1 for f in formatted if f['resim_url'])}")

        # Supabase'e arka planda kaydet
        if req.organization_id and sb_rows_to_save:
            import threading
            threading.Thread(
                target=_sb_save_products,
                args=(req.organization_id, sb_rows_to_save),
                daemon=True
            ).start()

        return {
            "status": "success",
            "products": formatted,
            "total": len(formatted),
            "from_cache": False
        }

    except Exception as e:
        print(f"[FETCH HATA] {e}")
        traceback.print_exc()
        return {
            "status": "error",
            "products": [],
            "error": f"Ticimax baglantisi basarisiz: {str(e)}"
        }


# ──────────────── ANALIZ ────────────────

def _run_analysis(session_id: str, req: AnalyzeRequest):
    """Arka planda AI analizi yapar."""
    session = sessions_db[session_id]
    session["status"] = "processing"
    sb.mark_processing(session_id)
    session["errors"] = []
    session["cost_tl"] = 0.0
    session["cost_usd"] = 0.0
    session["total_input_tokens"] = 0
    session["total_output_tokens"] = 0
    session["started_at"] = time.time()
    session["product_times"] = []  # Her urun icin sure kaydi
    results_db[session_id] = []

    # 0. Sektör intelligence yükle (organization_id varsa)
    sector_intelligence: Optional[dict] = None
    if req.organization_id:
        sector_intelligence = _load_sector_intelligence(req.organization_id)
        if sector_intelligence:
            _log(session_id, f"Sektör verisi yüklendi: {sector_intelligence.get('display_name','?')} "
                             f"({sum(1 for k in ['keywords','faq','competitor','seasonal','schema'] if sector_intelligence.get(k))} katman)")
        else:
            _log(session_id, "Sektör verisi bulunamadı — genel prompt kullanılacak")

    # 1. Gemini API key kontrolu (pool'dan al, kullanici keyi yoksa)
    gemini_key = get_gemini_key(req.api_key or "")
    if not gemini_key:
        session["status"] = "error"
        session["errors"].append("Gemini API Key bulunamadi! Admin panelinden key eklenmeli.")
        _log(session_id, "HATA: Gemini API Key bos (pool da bos)!")
        sb.mark_failed(session_id, "Gemini API Key bulunamadi — admin key eklemeli")
        return

    _log(session_id, f"Gemini API Key secildi ({gemini_key[:8]}...)")

    # 2. VisionEngine baslat
    try:
        engine = VisionEngine(api_key=gemini_key)
        _log(session_id, "VisionEngine baslatildi")
    except Exception as e:
        session["status"] = "error"
        session["errors"].append(f"VisionEngine hatasi: {str(e)}")
        _log(session_id, f"HATA: VisionEngine baslatilamadi: {e}")
        sb.mark_failed(session_id, f"VisionEngine hatasi: {str(e)}")
        return

    # 3. Cache'te olmayan urunler icin Ticimax'e baglan
    eksik_urunler = [s for s in req.selected_products if s not in products_cache]
    if eksik_urunler and req.domain_url:
        _log(session_id,
             f"{len(eksik_urunler)} urun cache'te yok, Ticimax'ten cekilecek...")
        try:
            wsdl_url = _build_wsdl_url(req.domain_url)
            client = TicimaxClient(base_url=wsdl_url, uye_kodu=req.ws_kodu)
            tum = client.get_urun_liste(urun_karti_id=0)
            for u in tum:
                stok = _extract_stok_kodu(u)
                if stok not in products_cache:
                    products_cache[stok] = {
                        "raw": u,
                        "urun_adi": str(get_field(u, 'UrunAdi',
                                                   get_field(u, 'Tanim', ''))),
                        "resim_urls": _extract_image_urls(u),
                        "stok_kodu": stok,
                        "marka": str(get_field(u, 'Marka', '')),
                    }
            _log(session_id, f"Ticimax'ten {len(tum)} urun cekildi ve cache guncellendi")
        except Exception as e:
            _log(session_id, f"UYARI: Ticimax tekrar baglantisi basarisiz: {e}")
            session["errors"].append(f"Ticimax baglantisi basarisiz: {str(e)}")

    # 4. Her secili urun icin analiz
    toplam = len(req.selected_products)
    marka = req.brand_name or "Marka"

    _log(session_id, f"Analiz basliyor: {toplam} urun, marka={marka}")

    for idx, stok_kodu in enumerate(req.selected_products):
        if session.get("cancel_requested"):
            session["status"] = "cancelled"
            session["current_product"] = ""
            session["elapsed_sn"] = round(time.time() - session["started_at"], 1)
            _log(session_id, f"Analiz kullanici tarafindan iptal edildi (idx={idx}/{toplam})")
            sb.mark_cancelled(session_id, processed=idx)
            return
        product_start = time.time()
        session["current_product"] = stok_kodu
        cached = products_cache.get(stok_kodu)

        if not cached:
            msg = f"{stok_kodu}: Cache'te bulunamadi, atlandi."
            _log(session_id, msg)
            session["errors"].append(msg)
            session["completed"] = idx + 1
            results_db[session_id].append({
                "stok_kodu": stok_kodu,
                "urun_adi": stok_kodu,
                "status": "skipped",
                "error": "Urun verisi bulunamadi"
            })
            sb.insert_result(session_id, stok_kodu, stok_kodu, "skipped",
                             error_message="Urun verisi bulunamadi")
            sb.update_progress(session_id, idx + 1)
            continue

        urun = cached.get("raw")  # Supabase cache'den yüklendiğinde None olabilir
        urun_adi = cached["urun_adi"]
        resim_urls = cached["resim_urls"]
        urun_marka = cached.get("marka", "") or marka

        _log(session_id,
             f"[{idx+1}/{toplam}] {urun_adi} — {len(resim_urls)} gorsel")

        if not resim_urls:
            msg = f"{stok_kodu} ({urun_adi}): Gorsel bulunamadi, atlandi."
            _log(session_id, msg)
            session["errors"].append(msg)
            session["completed"] = idx + 1
            results_db[session_id].append({
                "stok_kodu": stok_kodu,
                "urun_adi": urun_adi,
                "status": "skipped",
                "error": "Gorsel bulunamadi"
            })
            sb.insert_result(session_id, stok_kodu, urun_adi, "skipped",
                             error_message="Gorsel bulunamadi")
            sb.update_progress(session_id, idx + 1)
            continue

        # Gorselleri gecici dosyalara indir
        temp_paths = []
        for img_idx, img_url in enumerate(resim_urls):
            temp_path = os.path.join(
                tempfile.gettempdir(),
                f"pixra_{session_id[:8]}_{idx}_{img_idx}.jpg"
            )
            if download_image(img_url, temp_path):
                temp_paths.append(temp_path)
                _log(session_id, f"  Gorsel {img_idx+1} indirildi: {img_url[:60]}...")
            else:
                _log(session_id, f"  Gorsel {img_idx+1} indirilemedi: {img_url[:60]}...")

        if not temp_paths:
            msg = f"{stok_kodu} ({urun_adi}): Gorseller indirilemedi."
            _log(session_id, msg)
            session["errors"].append(msg)
            session["completed"] = idx + 1
            results_db[session_id].append({
                "stok_kodu": stok_kodu,
                "urun_adi": urun_adi,
                "status": "skipped",
                "error": "Gorseller indirilemedi"
            })
            sb.insert_result(session_id, stok_kodu, urun_adi, "skipped",
                             error_message="Gorseller indirilemedi",
                             image_url=resim_urls[0] if resim_urls else None)
            sb.update_progress(session_id, idx + 1)
            continue

        # AI analiz — retry mekanizmasi (kota hatalari icin aninda fail)
        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                _log(session_id,
                     f"  Gemini analiz basliyor (deneme {attempt}/{MAX_RETRIES})...")

                # Mevcut urun bilgilerini referans olarak hazirla
                ref_parts = []
                if cached.get("mevcut_aciklama"):
                    ref_parts.append(f"MEVCUT ACIKLAMA: {cached['mevcut_aciklama'][:1000]}")
                if cached.get("mevcut_seo_anahtar"):
                    ref_parts.append(f"MEVCUT SEO ANAHTAR: {cached['mevcut_seo_anahtar']}")
                if cached.get("mevcut_seo_aciklama"):
                    ref_parts.append(f"MEVCUT SEO ACIKLAMA: {cached['mevcut_seo_aciklama']}")
                if cached.get("ana_kategori"):
                    ref_parts.append(f"ANA KATEGORI: {cached['ana_kategori']}")
                reference_content = "\n".join(ref_parts)

                ai_result = engine.analyze_product_image(
                    image_path=temp_paths[0],
                    marka=urun_marka,
                    adwords_aciklama=cached.get("adwords_aciklama") or (str(get_field(urun, 'AdwordsAciklama', '')) if urun else ''),
                    adwords_kategori=cached.get("adwords_kategori") or (str(get_field(urun, 'AdwordsKategori', '')) if urun else ''),
                    adwords_tip=cached.get("adwords_tip") or (str(get_field(urun, 'AdwordsTip', '')) if urun else ''),
                    breadcrumb_kat=cached.get("breadcrumb_kat") or (str(get_field(urun, 'BreadcrumbKat', '')) if urun else ''),
                    image_paths=temp_paths,
                    mevcut_urun_adi=urun_adi,
                    satisfiyati=cached.get("satis_fiyati", ""),
                    kategoriler=cached.get("kategoriler") or (str(get_field(urun, 'Kategoriler', '')) if urun else ''),
                    stok_kodu=stok_kodu,
                    reference_content=reference_content,
                    sector_intelligence=sector_intelligence,
                )

                # SEO baslik karakter kontrolu
                if len(ai_result.seo_baslik) > 60:
                    kesilmis = ai_result.seo_baslik[:60]
                    son_bosluk = kesilmis.rfind(' ')
                    if son_bosluk > 40:
                        kesilmis = kesilmis[:son_bosluk]
                    ai_result.seo_baslik = kesilmis.strip()

                # Maliyet ve token bilgisini guncelle
                usage = engine.last_usage
                session["cost_tl"] += usage["cost_tl"]
                session["cost_usd"] += usage["cost_usd"]
                session["total_input_tokens"] += usage["input_tokens"]
                session["total_output_tokens"] += usage["output_tokens"]

                product_elapsed = round(time.time() - product_start, 1)
                session["product_times"].append({
                    "stok_kodu": stok_kodu,
                    "urun_adi": urun_adi[:40],
                    "sure_sn": product_elapsed,
                    "input_tokens": usage["input_tokens"],
                    "output_tokens": usage["output_tokens"],
                    "cost_tl": usage["cost_tl"],
                })

                result_data = ai_result.model_dump()
                result_data["stok_kodu"] = stok_kodu
                result_data["orijinal_urun_adi"] = urun_adi
                result_data["status"] = "completed"

                # ── Verifier ajanı (denetim + otomatik patch) ──
                verifier_report_dict = None
                try:
                    from core.verifier import verify_strategist_output, apply_patches
                    verifier_context = (
                        f"marka: {urun_marka}\n"
                        f"mevcut_urun_adi: {urun_adi}\n"
                        f"mevcut_aciklama: {cached.get('mevcut_aciklama', '')[:800]}\n"
                        f"mevcut_seo_baslik: {cached.get('mevcut_seo_baslik', '')}\n"
                        f"mevcut_seo_aciklama: {cached.get('mevcut_seo_aciklama', '')}\n"
                        f"kategoriler: {get_field(urun, 'Kategoriler', '')}\n"
                        f"stok_kodu: {stok_kodu}\n"
                        f"satis_fiyati_TL: {cached.get('satis_fiyati', '(verilmedi)')}\n"
                    )
                    report = verify_strategist_output(
                        client=engine.client,
                        strategist_output=result_data,
                        original_context=verifier_context,
                        skip_llm=False,
                    )
                    verifier_report_dict = report.model_dump()

                    # Patch uygula (LLM önermişse)
                    if report.patches:
                        patched = apply_patches(result_data, report.patches)
                        result_data.update(patched)

                    session["cost_tl"] += report.llm_cost_tl
                    _log(session_id,
                         f"  Verifier: {report.overall_status} — {report.summary} "
                         f"(v:{report.verified_count} r:{report.category_rag_count} i:{report.inferred_count}, "
                         f"+{report.llm_cost_tl:.4f} TL)")
                except Exception as verr:
                    _log(session_id, f"  Verifier hatası (devam): {verr}")

                # ── Schema.org post-process: placeholder temizliği + E-E-A-T sinyalleri ──
                try:
                    import datetime as _dt
                    schema = result_data.get("schema_jsonld")
                    if isinstance(schema, list):
                        _PLACEHOLDERS = ("example.com", "example.org", "domain.com",
                                         "yourdomain", "placeholder", "lorem")
                        _today = _dt.date.today().isoformat()
                        for block in schema:
                            if not isinstance(block, dict):
                                continue
                            if block.get("@type") != "Product":
                                continue

                            # ── E-E-A-T: dateModified (Google güvenilirlik sinyali) ──
                            block["dateModified"] = _today

                            # ── E-E-A-T: brand bloğu — gerçek marka adı injekte ──
                            real_brand = req.brand_name or cached.get("marka", "")
                            if real_brand:
                                existing_brand = block.get("brand")
                                if isinstance(existing_brand, dict):
                                    existing_brand["name"] = real_brand
                                elif not existing_brand:
                                    block["brand"] = {"@type": "Brand", "name": real_brand}

                            # ── Gerçek URL injekte (SEO + rich results) ──
                            domain = req.domain_url.strip().rstrip("/")
                            if domain and cached.get("seo_url"):
                                seo_path = cached["seo_url"]
                                if not domain.startswith("http"):
                                    domain = "https://" + domain
                                real_url = f"{domain}/{seo_path.lstrip('/')}"
                                block["url"] = real_url
                                offers = block.get("offers")
                                if isinstance(offers, dict) and not offers.get("url"):
                                    offers["url"] = real_url

                            # ── Gerçek image varsa injekte, yoksa placeholder'ı temizle ──
                            if resim_urls:
                                block["image"] = resim_urls[:5]
                            else:
                                img = block.get("image")
                                if isinstance(img, list):
                                    block["image"] = [u for u in img if isinstance(u, str)
                                                       and not any(p in u.lower() for p in _PLACEHOLDERS)]
                                    if not block["image"]:
                                        block.pop("image", None)
                                elif isinstance(img, str) and any(p in img.lower() for p in _PLACEHOLDERS):
                                    block.pop("image", None)

                            # ── offers placeholder temizliği ──
                            offers = block.get("offers")
                            if isinstance(offers, dict):
                                url = offers.get("url", "")
                                if isinstance(url, str) and any(p in url.lower() for p in _PLACEHOLDERS):
                                    offers.pop("url", None)
                                if not cached.get("satis_fiyati") and "price" in offers:
                                    block.pop("offers", None)
                except Exception as serr:
                    _log(session_id, f"  Schema post-process hatası (devam): {serr}")

                # ── Görsel Alt Tag üretimi (tüm görseller, best-effort) ──────────
                try:
                    alt_tags_list = []
                    for tmp_path in temp_paths:
                        alt = engine.generate_alt_text(
                            image_path=tmp_path,
                            urun_adi=result_data.get("urun_adi") or urun_adi,
                            kategori=cached.get("kategoriler", ""),
                            marka=urun_marka,
                        )
                        alt_tags_list.append(alt)
                    result_data["gorsel_alt_tags"] = alt_tags_list
                    if alt_tags_list:
                        _log(session_id,
                             f"  Alt tag: {len(alt_tags_list)} gorsel — "
                             f"'{alt_tags_list[0][:50]}...'")
                except Exception as _alt_err:
                    _log(session_id, f"  Alt tag uretimi basarisiz (devam): {_alt_err}")
                    result_data["gorsel_alt_tags"] = []

                results_db[session_id].append(result_data)

                # Supabase'e yaz (best-effort)
                sb.insert_result(
                    session_id=session_id,
                    stok_kodu=stok_kodu,
                    urun_adi=urun_adi,
                    status="completed",
                    ai_payload=result_data,
                    original={
                        "urun_adi": urun_adi,
                        "seo_baslik": cached.get("mevcut_seo_baslik"),
                        "seo_aciklama": cached.get("mevcut_seo_aciklama"),
                        "aciklama": cached.get("mevcut_aciklama"),
                    },
                    image_url=resim_urls[0] if resim_urls else None,
                    cost_tl=usage["cost_tl"],
                    verifier_report=verifier_report_dict,
                )
                sb.update_progress(session_id, idx + 1)

                _log(session_id,
                     f"  BASARILI: {ai_result.seo_baslik[:50]}... "
                     f"({product_elapsed}sn, {usage['cost_tl']:.4f} TL)")
                success = True

                # Maliyet limiti kontrolu
                if session["cost_tl"] >= COST_LIMIT_TL:
                    _log(session_id,
                         f"  UYARI: Maliyet limiti asildi! "
                         f"Toplam: {session['cost_tl']:.2f} TL >= {COST_LIMIT_TL} TL")
                    session["errors"].append(
                        f"MALIYET LIMITI: Toplam {session['cost_tl']:.2f} TL harcandi. "
                        f"Limit: {COST_LIMIT_TL} TL. Analiz durduruldu."
                    )
                    safe_file_cleanup(temp_paths)
                    session["completed"] = idx + 1
                    session["status"] = "error"
                    session["current_product"] = ""
                    session["elapsed_sn"] = round(time.time() - session["started_at"], 1)
                    sb.mark_failed(session_id, f"Maliyet limiti asildi ({session['cost_tl']:.2f} TL)", processed=idx + 1)
                    return

                break

            except Exception as e:
                err_msg = str(e)
                _log(session_id,
                     f"  HATA (deneme {attempt}): {err_msg[:100]}")

                # Kota, izin veya sunucu hatasi — retry anlamsiz, hemen dur
                is_fatal = ("kota" in err_msg.lower()
                            or "erisim" in err_msg.lower()
                            or "yogun" in err_msg.lower()
                            or "429" in err_msg
                            or "403" in err_msg
                            or "503" in err_msg
                            or "PERMISSION" in err_msg
                            or "EXHAUSTED" in err_msg
                            or "UNAVAILABLE" in err_msg
                            or "gecersiz" in err_msg.lower())

                if is_fatal or attempt == MAX_RETRIES:
                    session["errors"].append(
                        f"{stok_kodu} ({urun_adi}): {err_msg[:150]}"
                    )
                    results_db[session_id].append({
                        "stok_kodu": stok_kodu,
                        "urun_adi": urun_adi,
                        "status": "error",
                        "error": err_msg[:200]
                    })
                    sb.insert_result(session_id, stok_kodu, urun_adi, "error",
                                     error_message=err_msg[:500],
                                     image_url=resim_urls[0] if resim_urls else None)
                    sb.update_progress(session_id, idx + 1)
                    if is_fatal:
                        # Kota hatasi — kalan urunler icin de durum guncelle
                        _log(session_id,
                             f"  FATAL: Kota/izin hatasi, analiz durduruluyor")
                        safe_file_cleanup(temp_paths)
                        session["completed"] = idx + 1
                        session["status"] = "error"
                        session["current_product"] = ""
                        sb.mark_failed(session_id, err_msg[:300], processed=idx + 1)
                        return  # Tum analizi durdur
                    break
                else:
                    delay = RATE_LIMIT_DELAY * (2 ** (attempt - 1))
                    time.sleep(delay)

        # Gecici dosyalari temizle
        safe_file_cleanup(temp_paths)

        # Ilerleme guncelle
        session["completed"] = idx + 1

        # Rate limit korunmasi
        if success and idx < toplam - 1:
            time.sleep(RATE_LIMIT_DELAY)

    # Tamamlandi
    basarili = sum(1 for r in results_db[session_id] if r["status"] == "completed")
    toplam_sonuc = len(results_db[session_id])
    session["status"] = "completed"
    session["current_product"] = ""
    session["elapsed_sn"] = round(time.time() - session["started_at"], 1)
    sb.mark_completed(session_id, processed=toplam_sonuc)
    _log(session_id,
         f"Analiz tamamlandi: {basarili}/{toplam_sonuc} basarili | "
         f"Sure: {session['elapsed_sn']}sn | "
         f"Maliyet: {session['cost_tl']:.4f} TL | "
         f"Tokenlar: {session['total_input_tokens']} in / {session['total_output_tokens']} out")


@app.post("/api/analyze/start")
def start_analysis(req: AnalyzeRequest, bg_tasks: BackgroundTasks):
    """Secili urunlerin AI analizini baslatir."""
    session_id = req.session_id or str(uuid.uuid4())

    # Validasyon
    if not req.selected_products:
        raise HTTPException(status_code=400, detail="Urun secilmedi")

    sessions_db[session_id] = {
        "status": "pending",
        "total": len(req.selected_products),
        "completed": 0,
        "firma": req.firma_kodu,
        "current_product": "",
        "errors": [],
        "logs": [],
        "cancel_requested": False,
    }

    print(f"\n{'='*60}")
    print(f"[ANALIZ BASLADI] session={session_id[:8]}")
    print(f"  Urun sayisi: {len(req.selected_products)}")
    print(f"  Stok kodlari: {req.selected_products[:5]}...")
    print(f"  Domain: {req.domain_url}")
    print(f"  API Key: {req.api_key[:8] + '...' if req.api_key else 'BOS!'}")
    print(f"  Cache'teki urun sayisi: {len(products_cache)}")
    print(f"  Cache'te eslesen: {sum(1 for s in req.selected_products if s in products_cache)}")
    print(f"{'='*60}\n")

    bg_tasks.add_task(_run_analysis, session_id, req)

    return {"message": "Analysis started", "session_id": session_id}


@app.get("/api/analyze/status/{session_id}")
def get_status(session_id: str):
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions_db[session_id]
    total = int(session["total"])
    completed = int(session["completed"])
    percent = (completed / total * 100) if total > 0 else 0.0

    elapsed = round(time.time() - session.get("started_at", time.time()), 1) if session["status"] == "processing" else session.get("elapsed_sn", 0)

    return {
        "session_id": session_id,
        "status": session["status"],
        "total": total,
        "completed": completed,
        "percent": round(percent, 1),
        "current_product": session.get("current_product", ""),
        "errors": session.get("errors", []),
        "cost_tl": round(session.get("cost_tl", 0), 4),
        "cost_usd": round(session.get("cost_usd", 0), 6),
        "elapsed_sn": elapsed,
        "total_input_tokens": session.get("total_input_tokens", 0),
        "total_output_tokens": session.get("total_output_tokens", 0),
        "cost_limit_tl": COST_LIMIT_TL,
        "product_times": session.get("product_times", []),
    }


@app.post("/api/analyze/cancel/{session_id}")
def cancel_analysis(session_id: str):
    """Devam eden analizi iptal eder."""
    session = sessions_db.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] in ("completed", "cancelled", "error"):
        return {"message": "Already finished", "status": session["status"]}
    session["cancel_requested"] = True
    _log(session_id, "Iptal istegi alindi, bir sonraki urunden once durdurulacak")
    return {"message": "Cancel requested", "session_id": session_id}


@app.get("/api/analyze/results/{session_id}")
def get_results(session_id: str):
    if session_id not in results_db:
        raise HTTPException(status_code=404, detail="Results not found")

    return {
        "session_id": session_id,
        "results": results_db[session_id],
        "total": len(results_db[session_id])
    }


@app.get("/api/debug/last-adwords")
def debug_last_adwords():
    """Debug: Son analiz sonuclarindaki adwords alanlarini goster."""
    all_results = []
    for sid, results in results_db.items():
        for r in results:
            if r.get("status") == "completed":
                all_results.append({
                    "stok_kodu": r.get("stok_kodu"),
                    "urun_adi": r.get("urun_adi", "")[:50],
                    "adwords_aciklama": r.get("adwords_aciklama", "ALAN YOK"),
                    "adwords_kategori": r.get("adwords_kategori", "ALAN YOK"),
                    "adwords_tip": r.get("adwords_tip", "ALAN YOK"),
                    "has_adwords": all([
                        r.get("adwords_aciklama"),
                        r.get("adwords_kategori"),
                        r.get("adwords_tip"),
                    ])
                })
    return {"results": all_results, "count": len(all_results)}


# ──────────────── FİRMA PROFİL ANKETİ ────────────────

@app.post("/api/firma-profil")
def save_firma_profil(req: FirmaProfilRequest):
    """10 soruluk firma profil anketini Supabase'e kaydeder.

    Profil, AI içerik üretiminde strateji brifing'ine enjekte edilir.
    """
    client = sb._get_client()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase bağlantısı yok")

    try:
        # firma_profil + türetilmiş hızlı erişim alanları
        profil = req.profil
        update_data = {
            "firma_profil": profil,
            "marka_tonu": profil.get("marka_tonu"),
            "hedef_kitle": profil.get("hedef_kitle"),
            "uretim_yeri": profil.get("uretim_yeri"),
        }
        # urun_kategorileri diziye çevir
        kategori = profil.get("ana_kategori")
        if kategori:
            update_data["urun_kategorileri"] = [kategori] if isinstance(kategori, str) else kategori

        client.table("organizations").update(update_data).eq("id", req.organization_id).execute()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profil kaydedilemedi: {str(e)}")


@app.get("/api/firma-profil/{organization_id}")
def get_firma_profil(organization_id: str):
    """Firma profil anketini getirir."""
    client = sb._get_client()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase bağlantısı yok")

    try:
        res = client.table("organizations").select(
            "id, company_name, domain_url, firma_profil, marka_tonu, hedef_kitle, uretim_yeri"
        ).eq("id", organization_id).maybe_single().execute()
        if not res or not res.data:
            raise HTTPException(status_code=404, detail="Firma bulunamadı")
        return res.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────── LLMS.TXT GENERATOR ────────────────

@app.get("/api/llms-txt/{organization_id}", response_class=PlainTextResponse)
def generate_llms_txt(organization_id: str):
    """Mağaza için llms.txt içeriği üretir.

    ChatGPT, Perplexity, Gemini gibi AI crawler'lar bu dosyayı okuyarak
    mağazayı güvenilir kaynak olarak tanır. Çıktı plain text.
    """
    client = sb._get_client()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase bağlantısı yok")

    try:
        # Firma bilgilerini çek
        org_res = client.table("organizations").select(
            "company_name, domain_url, firma_profil, urun_kategorileri, marka_tonu, hedef_kitle"
        ).eq("id", organization_id).maybe_single().execute()

        if not org_res or not org_res.data:
            raise HTTPException(status_code=404, detail="Firma bulunamadı")

        org = org_res.data
        firma_adi = org.get("company_name", "Mağaza")
        domain = (org.get("domain_url") or "").strip().rstrip("/")
        profil = org.get("firma_profil") or {}
        kategoriler = org.get("urun_kategorileri") or []
        marka_tonu = org.get("marka_tonu") or ""
        hedef_kitle = org.get("hedef_kitle") or ""

        # Son onaylanmış ürün özetlerini çek (max 20)
        results_res = client.table("ai_results").select(
            "ai_urun_adi, ai_seo_aciklama, ai_seo_baslik"
        ).eq("organization_id", organization_id).eq("status", "completed").limit(20).execute()

        urunler = results_res.data or [] if results_res else []

        # llms.txt oluştur (2025 llms.txt spec uyumlu)
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        lines = [
            f"# {firma_adi}",
            f"> Pixra tarafından optimize edilmiş Türk e-ticaret mağazası.",
            f"> Alan: {domain}" if domain else "",
            f"> Son güncelleme: {now_str}",
            "",
        ]

        # Mağaza tanımı
        if profil.get("marka_hikayesi"):
            lines += [
                "## Mağaza Hakkında",
                profil["marka_hikayesi"],
                "",
            ]
        elif firma_adi:
            lines += [
                "## Mağaza Hakkında",
                f"{firma_adi}, Türkiye'de hizmet veren bir e-ticaret mağazasıdır.",
                "",
            ]

        # Kategori bilgisi
        if kategoriler:
            lines += [
                "## Ürün Kategorileri",
                ", ".join(kategoriler),
                "",
            ]

        # Hedef kitle + marka tonu
        if hedef_kitle:
            lines += [f"## Hedef Kitle", hedef_kitle, ""]
        if marka_tonu:
            lines += [f"## Marka Tonu", marka_tonu.capitalize(), ""]

        # Profil detayları
        if profil.get("deger_onerisi"):
            lines += ["## Değer Önerisi", profil["deger_onerisi"], ""]
        if profil.get("rakip_farki"):
            lines += ["## Rakipten Farkı", profil["rakip_farki"], ""]
        if profil.get("uretim_yeri"):
            lines += ["## Üretim / Temin", _format_uretim_yeri(profil["uretim_yeri"]), ""]

        # Öne çıkan ürünler
        if urunler:
            lines += ["## Öne Çıkan Ürünler", ""]
            for u in urunler[:10]:
                baslik = u.get("ai_seo_baslik") or u.get("ai_urun_adi") or ""
                aciklama = u.get("ai_seo_aciklama") or ""
                if baslik:
                    lines.append(f"### {baslik}")
                    if aciklama:
                        lines.append(aciklama)
                    lines.append("")

        # Pixra imzası
        lines += [
            "---",
            "Bu içerik Pixra (pixra.co) tarafından otomatik olarak üretilmiş ve optimize edilmiştir.",
            "Pixra: Türk e-ticaret ürünlerini AI motorlarında görünür ve alıntılanır hale getirir.",
        ]

        # Boş satırları temizle (başta/sonda birden fazla boş satır olmasın)
        content = "\n".join(lines).strip()

        # Supabase'e son üretim tarihini kaydet (best-effort)
        try:
            client.table("organizations").update({
                "llms_txt_generated_at": now_str
            }).eq("id", organization_id).execute()
        except Exception:
            pass

        return content

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"llms.txt üretilemedi: {str(e)}")


def _format_uretim_yeri(val: str) -> str:
    mapping = {
        "turkiye": "Türkiye üretimi",
        "ithal": "İthal ürün",
        "el_yapimi": "El yapımı / atölye üretimi",
        "karma": "Türkiye ve yurt dışı karma üretim",
    }
    return mapping.get(val.lower(), val)


@app.get("/api/stats")
def dashboard_stats():
    """Dashboard icin genel istatistikler."""
    active = sum(1 for s in sessions_db.values() if s.get("status") == "processing")
    total_analyzed = sum(
        len([r for r in results_db.get(sid, []) if r.get("status") == "completed"])
        for sid in results_db
    )
    return {
        "active_sessions": active,
        "total_analyzed": total_analyzed,
    }


@app.get("/api/cache/stats")
def cache_stats():
    """Debug endpoint: cache durumunu goster."""
    return {
        "cached_products": len(products_cache),
        "sample_keys": list(products_cache.keys())[:10],
        "sample_with_images": sum(
            1 for v in products_cache.values() if v.get("resim_urls")
        ),
        "active_sessions": len(sessions_db),
    }


@app.get("/api/cache/product/{stok_kodu}")
def cache_product_detail(stok_kodu: str):
    """Debug: Bir urunun cache'teki raw alanlarini goster."""
    cached = products_cache.get(stok_kodu)
    if not cached:
        raise HTTPException(status_code=404, detail="Urun cache'te yok")

    raw = cached["raw"]
    # SOAP objesinin tum alanlarini listele
    fields = {}
    for attr in dir(raw):
        if not attr.startswith('_'):
            try:
                val = getattr(raw, attr)
                if not callable(val):
                    fields[attr] = str(val)[:500]
            except Exception:
                pass
    return {"stok_kodu": stok_kodu, "urun_adi": cached["urun_adi"], "fields": fields}


# ──────────────── DEBUG: RAW URUN VERISI ────────────────

@app.get("/api/debug/products")
def debug_products_list():
    """Cache'teki tum urunlerin stok kodlarini listeler."""
    items = []
    for sk, cached in products_cache.items():
        raw = cached.get("raw")
        urun_id = get_field(raw, 'ID', 0) if raw else 0
        items.append({"stok_kodu": sk, "urun_adi": cached.get("urun_adi", ""), "ID": urun_id})
    return {"count": len(items), "products": items}


@app.get("/api/debug/test-send/{stok_kodu}")
def debug_test_send(stok_kodu: str, domain_url: str, ws_kodu: str):
    """Test: Sadece SeoSayfaBaslik'i degistirip geri yükler."""
    cached = products_cache.get(stok_kodu)
    if not cached or not cached.get("raw"):
        raise HTTPException(status_code=404, detail="Urun cache'te yok")

    raw = cached["raw"]
    wsdl_url = _build_wsdl_url(domain_url)
    client = TicimaxClient(base_url=wsdl_url, uye_kodu=ws_kodu)

    original_baslik = getattr(raw, 'SeoSayfaBaslik', '')
    test_baslik = "TEST - " + str(original_baslik)[:40]

    try:
        response = client.save_urun(
            raw_urun=raw,
            updates={"SeoSayfaBaslik": test_baslik},
            update_flags={"SeoSayfaBaslikGuncelle": True},
        )

        result_code = getattr(response, 'SaveUrunResult', None)
        returned_cards = getattr(response, 'urunKartlari', None)
        has_cards = returned_cards is not None and hasattr(returned_cards, 'UrunKarti') and returned_cards.UrunKarti

        # Geri yukle
        response2 = client.save_urun(
            raw_urun=raw,
            updates={"SeoSayfaBaslik": original_baslik},
            update_flags={"SeoSayfaBaslikGuncelle": True},
        )

        return {
            "success": has_cards,
            "result_code": result_code,
            "original_baslik": original_baslik,
            "test_baslik": test_baslik,
            "restored": True,
        }
    except Exception as e:
        return {"error": str(e)[:500], "traceback": traceback.format_exc()[:1000]}


@app.get("/api/debug/product/{stok_kodu}")
def debug_product(stok_kodu: str):
    """Cache'teki raw urun verisinin tum alanlarini gosterir."""
    cached = products_cache.get(stok_kodu)
    if not cached or not cached.get("raw"):
        raise HTTPException(status_code=404, detail="Urun cache'te bulunamadi")
    raw = cached["raw"]
    fields = {}
    for attr in dir(raw):
        if not attr.startswith('_'):
            try:
                val = getattr(raw, attr)
                if not callable(val):
                    type_name = type(val).__name__
                    # Zeep ArrayOf* tiplerini ozel isle
                    if type_name.startswith("ArrayOf"):
                        # Gercek veriyi cikar: .string, .int, .Varyasyon vb.
                        inner_type = type_name.replace("ArrayOf", "").lower()
                        inner_data = None
                        for candidate in [inner_type, inner_type.capitalize(), inner_type.upper()]:
                            if hasattr(val, candidate):
                                inner_data = getattr(val, candidate)
                                break
                        if inner_data is None and hasattr(val, '__iter__'):
                            inner_data = list(val)
                        items = inner_data if inner_data else []
                        fields[attr] = {
                            "type": type_name,
                            "length": len(items),
                            "first": str(items[0])[:300] if items else None
                        }
                    elif hasattr(val, '__iter__') and not isinstance(val, (str, bytes)):
                        items = list(val) if val else []
                        fields[attr] = {
                            "type": type_name,
                            "length": len(items),
                            "first": str(items[0])[:300] if items else None
                        }
                    else:
                        fields[attr] = {"type": type_name, "value": str(val)[:300]}
            except Exception as e:
                fields[attr] = {"error": str(e)[:100]}
    return {"stok_kodu": stok_kodu, "field_count": len(fields), "fields": fields}


# ──────────────── IMAGE ALT-TEXT ────────────────

@app.post("/api/alt-text/generate")
def generate_alt_text_batch(req: AltTextRequest, background_tasks: BackgroundTasks):
    """Cache'teki ürünlerin görselleri için alt-text üretir.

    Ürünler önce /api/products/fetch ile cache'e alınmış olmalı.
    Üretilen alt-text bilgi amaçlıdır — Ticimax'e göndermek için ayrıca
    /api/ticimax/send kullanılır (GorselAlt alanı ile).
    """
    missing = [sk for sk in req.stok_kodlari if sk not in products_cache]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"{len(missing)} ürün cache'te yok. Önce /api/products/fetch çalıştırın."
        )

    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY eksik")

    results = {}
    engine = VisionEngine(api_key=gemini_key)

    for stok_kodu in req.stok_kodlari[:50]:  # Güvenlik limiti: 50 ürün/istek
        cached = products_cache.get(stok_kodu)
        if not cached:
            results[stok_kodu] = {"status": "error", "alt_text": ""}
            continue

        urun_adi = cached.get("urun_adi", "")
        resim_urls = cached.get("resim_urls", [])
        kategoriler = cached.get("kategoriler", "")
        marka = cached.get("marka", "")

        if not resim_urls:
            results[stok_kodu] = {"status": "no_image", "alt_text": urun_adi}
            continue

        # İlk görseli indir ve alt-text üret
        tmp_path = None
        try:
            tmp_path = download_image(resim_urls[0])
            if not tmp_path:
                results[stok_kodu] = {"status": "download_failed", "alt_text": urun_adi}
                continue

            alt_text = engine.generate_alt_text(
                image_path=tmp_path,
                urun_adi=urun_adi,
                kategori=kategoriler,
                marka=marka,
            )
            results[stok_kodu] = {"status": "ok", "alt_text": alt_text}
        except Exception as e:
            results[stok_kodu] = {"status": "error", "alt_text": urun_adi, "error": str(e)[:200]}
        finally:
            safe_file_cleanup(tmp_path)

    ok_count = sum(1 for v in results.values() if v["status"] == "ok")
    return {
        "results": results,
        "ok": ok_count,
        "total": len(req.stok_kodlari),
        "cost_tl": round(engine.last_usage.get("cost_tl", 0), 4),
    }


# ──────────────── ALT-TEXT (ENHANCED) ────────────────

class GenerateProductAltTextRequest(BaseModel):
    """Analiz seansı sırasında ürün görselleri için alt-text üretimi."""
    session_id: str
    stok_kodu: str
    urun_adi: str
    kategori: str = ""
    marka: str = ""
    resim_urls: List[str] = []  # Kaç tane görsel olursa olsun işle


@app.post("/api/alt-text/generate-for-session")
def generate_alt_text_for_session(req: GenerateProductAltTextRequest):
    """
    Analiz oturum sırasında bir ürünün tüm görselleri için alt-text üret.
    Frontend'ten üretilen alt-text'ler onay ekranında gösterilir,
    kullanıcı düzeltebilir, sonra ticimax/send'le beraber gönderilir.

    Returns:
        {
            "stok_kodu": str,
            "results": [
                {"url": str, "alt_text": str, "status": "ok"|"error"},
                ...
            ],
            "cost_tl": float
        }
    """
    if not req.session_id or not req.stok_kodu:
        raise HTTPException(status_code=400, detail="session_id ve stok_kodu zorunludur")

    if not req.resim_urls:
        return {
            "stok_kodu": req.stok_kodu,
            "results": [],
            "cost_tl": 0,
            "message": "Görsel URL'i sağlanmamış"
        }

    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY eksik")

    engine = VisionEngine(api_key=gemini_key)
    results = []

    # Max 5 görsel işle (para tasarrufu)
    for url in req.resim_urls[:5]:
        tmp_path = None
        try:
            tmp_path = download_image(url)
            if not tmp_path:
                results.append({"url": url, "status": "download_failed", "alt_text": ""})
                continue

            alt_text = engine.generate_alt_text(
                image_path=tmp_path,
                urun_adi=req.urun_adi,
                kategori=req.kategori,
                marka=req.marka,
            )
            results.append({"url": url, "status": "ok", "alt_text": alt_text})
        except Exception as e:
            results.append({"url": url, "status": "error", "alt_text": "", "error": str(e)[:100]})
        finally:
            safe_file_cleanup(tmp_path)

    return {
        "stok_kodu": req.stok_kodu,
        "results": results,
        "cost_tl": round(engine.last_usage.get("cost_tl", 0), 4),
    }


# ──────────────── TICIMAX'E GONDERME ────────────────

@app.post("/api/ticimax/send")
def send_to_ticimax(req: SendToTicimaxRequest):
    """
    Analiz sonuclarini Ticimax'e gonderir.
    Her urun icin sadece SEO/icerik alanlarini gunceller.
    3 asamali onay frontend'de yapilir, bu endpoint sadece onaylanan urunleri isler.
    """
    if not req.domain_url or not req.ws_kodu:
        raise HTTPException(status_code=400, detail="domain_url ve ws_kodu zorunludur")

    if not req.products:
        raise HTTPException(status_code=400, detail="Gonderilecek urun listesi bos")

    # Ticimax client olustur
    try:
        wsdl_url = _build_wsdl_url(req.domain_url)
        client = TicimaxClient(base_url=wsdl_url, uye_kodu=req.ws_kodu)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ticimax baglantisi kurulamadi: {str(e)}")

    results = []

    # Ticimax'ten tam liste lazımsa (raw eksik ürünler için) bir kez çek
    _ticimax_full: Optional[list] = None

    def _ensure_raw(stok: str) -> Optional[Any]:
        """Cache'te raw yoksa Ticimax'ten çekip cache'e yazar, raw objeyi döner."""
        nonlocal _ticimax_full
        cached_item = products_cache.get(stok)
        if cached_item and cached_item.get("raw"):
            return cached_item["raw"]
        # Lazy tam liste çekimi — birden fazla ürün için tek sefer
        if _ticimax_full is None:
            try:
                _log("send", "raw eksik, Ticimax'ten tam liste çekiliyor...")
                _ticimax_full = client.get_urun_liste(urun_karti_id=0)
                for u in _ticimax_full:
                    sk = _extract_stok_kodu(u)
                    if sk:
                        existing = products_cache.get(sk, {})
                        existing["raw"] = u
                        products_cache[sk] = existing
                _log("send", f"Ticimax'ten {len(_ticimax_full)} ürün yüklendi")
            except Exception as e:
                _log("send", f"Ticimax yeniden çekme hatası: {e}")
                _ticimax_full = []
        cached_item2 = products_cache.get(stok)
        return cached_item2.get("raw") if cached_item2 else None

    for prod in req.products:
        stok_kodu = prod.get("stok_kodu", "")
        if not stok_kodu:
            results.append({"stok_kodu": stok_kodu, "status": "error", "error": "stok_kodu eksik"})
            continue

        raw = _ensure_raw(stok_kodu)
        if not raw:
            results.append({"stok_kodu": stok_kodu, "status": "error",
                             "error": "Ürün Ticimax'te bulunamadı. WS kodu veya domain kontrol edin."})
            continue
        urun_karti_id = get_field(raw, 'ID', None)
        if not urun_karti_id:
            results.append({"stok_kodu": stok_kodu, "status": "error", "error": "UrunKartiId bulunamadi"})
            continue

        # AI sonuclarini Ticimax alan adlarina maple
        updates = {}
        if prod.get("urun_adi"):
            updates["UrunAdi"] = prod["urun_adi"]
        if prod.get("aciklama"):
            updates["Aciklama"] = prod["aciklama"]
        if prod.get("seo_baslik"):
            updates["SeoSayfaBaslik"] = prod["seo_baslik"]
        if prod.get("seo_aciklama"):
            updates["SeoSayfaAciklama"] = prod["seo_aciklama"]
        if prod.get("seo_anahtarkelime"):
            updates["SeoAnahtarKelime"] = prod["seo_anahtarkelime"]
        if prod.get("onyazi"):
            updates["OnYazi"] = prod["onyazi"]
        if prod.get("adwords_aciklama"):
            updates["AdwordsAciklama"] = prod["adwords_aciklama"]
        if prod.get("adwords_kategori"):
            updates["AdwordsKategori"] = prod["adwords_kategori"]
        if prod.get("adwords_tip"):
            updates["AdwordsTip"] = prod["adwords_tip"]

        # UrunKartiAyar — sadece guncellenen alanlar True
        update_flags = {
            "UrunAdiGuncelle": "UrunAdi" in updates,
            "AciklamaGuncelle": "Aciklama" in updates,
            "SeoSayfaBaslikGuncelle": "SeoSayfaBaslik" in updates,
            "SeoSayfaAciklamaGuncelle": "SeoSayfaAciklama" in updates,
            "SeoAnahtarKelimeGuncelle": "SeoAnahtarKelime" in updates,
            "OnYaziGuncelle": "OnYazi" in updates,
            "AdwordsAciklamaGuncelle": "AdwordsAciklama" in updates,
            "AdwordsKategoriGuncelle": "AdwordsKategori" in updates,
            "AdwordsTipGuncelle": "AdwordsTip" in updates,
        }

        # Gorsel alt tagleri (analiz sirasinda uretilmis olabilir)
        gorsel_alt_tags = prod.get("gorsel_alt_tags") or []

        try:
            active_flags = {k: v for k, v in update_flags.items() if v}
            print(f"\n[TICIMAX SEND] stok={stok_kodu}, ID={urun_karti_id}, "
                  f"updates={list(updates.keys())}, "
                  f"flags={active_flags}, "
                  f"alt_tags={len(gorsel_alt_tags)} gorsel")

            response = client.save_urun(
                raw_urun=raw,
                updates=updates,
                update_flags=update_flags,
                alt_tags=gorsel_alt_tags if gorsel_alt_tags else None,
            )

            # SaveUrunResult=0 basarili demek (0 hata),
            # urunKartlari doluysa islem gerceklesti
            result_code = getattr(response, 'SaveUrunResult', None)
            returned_cards = getattr(response, 'urunKartlari', None)

            # Basari kontrolu: urunKartlari donuyorsa guncelleme yapildi
            has_cards = bool(
                returned_cards is not None
                and hasattr(returned_cards, 'UrunKarti')
                and returned_cards.UrunKarti
            )

            print(f"[TICIMAX SEND] result_code={result_code}, has_cards={has_cards}")

            if has_cards:
                results.append({
                    "stok_kodu": stok_kodu,
                    "status": "success",
                    "error": "",
                    "urun_karti_id": int(urun_karti_id),
                })
            else:
                results.append({
                    "stok_kodu": stok_kodu,
                    "status": "error",
                    "error": f"Ticimax guncelleme yapmadi (result={result_code}, cards={returned_cards})",
                    "urun_karti_id": int(urun_karti_id),
                })

        except Exception as e:
            results.append({"stok_kodu": stok_kodu, "status": "error", "error": str(e)[:300]})

    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")

    return {
        "total": len(results),
        "success": success_count,
        "errors": error_count,
        "results": results,
    }


# ──────────────── TICIMAX DEBUG ────────────────

class TicimaxDebugRequest(BaseModel):
    domain_url: str
    ws_kodu: str
    stok_kodu: Optional[str] = None


@app.post("/api/ticimax/debug-wsdl")
def debug_ticimax_wsdl(req: TicimaxDebugRequest):
    """
    WSDL'den UrunKartiAyar ve UrunResim alan adlarini doner.
    Hangi flag isimlerinin dogru oldugunu ve alt tag desteklenip desteklenmedigini anlamak icin kullanilir.
    """
    try:
        wsdl_url = _build_wsdl_url(req.domain_url)
        client = TicimaxClient(base_url=wsdl_url, uye_kodu=req.ws_kodu)
        uk_fields = client.get_urunkartiayar_fields()
        ur_fields = client.get_urunresim_fields()
        alt_tag_destekleniyor = "AlternatifMetin" in ur_fields
        return {
            "urunkartiayar_fields": uk_fields,
            "urunresim_fields": ur_fields,
            "alt_tag_destekleniyor": alt_tag_destekleniyor,
            "resimler_guncelle_flag_var": "ResimlerGuncelle" in uk_fields,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ticimax/verify-send")
def verify_ticimax_send(req: TicimaxDebugRequest):
    """
    Belirli bir urun icin SaveUrun sonrasi SelectUrun ile degerleri
    karsilastirir — guncelleme gercekten yapildi mi kontrol eder.
    """
    if not req.stok_kodu:
        raise HTTPException(status_code=400, detail="stok_kodu zorunlu")
    try:
        wsdl_url = _build_wsdl_url(req.domain_url)
        client = TicimaxClient(base_url=wsdl_url, uye_kodu=req.ws_kodu)
        urunler = client.get_urun_liste(urun_karti_id=int(req.stok_kodu))
        if not urunler:
            return {"found": False}
        u = urunler[0]
        return {
            "found": True,
            "ID": getattr(u, "ID", None),
            "StokKodu": getattr(u, "StokKodu", None),
            "UrunAdi": getattr(u, "UrunAdi", None),
            "SeoSayfaBaslik": getattr(u, "SeoSayfaBaslik", None),
            "SeoSayfaAciklama": getattr(u, "SeoSayfaAciklama", None),
            "SeoAnahtarKelime": getattr(u, "SeoAnahtarKelime", None),
            "Aciklama": (getattr(u, "Aciklama", None) or "")[:200],
            "OnYazi": getattr(u, "OnYazi", None),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────── ADMIN GEMINI KEY YÖNETİMİ ────────────────

class GeminiKeyRequest(BaseModel):
    label: str
    api_key: str


def _sb_admin_request(method: str, path: str, prefer: str = "", **kwargs):
    import httpx
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if prefer:
        headers["Prefer"] = prefer
    return httpx.request(method, f"{url}/rest/v1/{path}", headers=headers, timeout=10, **kwargs)


@app.get("/api/admin/gemini-keys")
def list_gemini_keys():
    resp = _sb_admin_request("GET", "gemini_keys", params={"select": "id,label,is_active,created_at,api_key"})
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Keys alınamadı")
    rows = resp.json()
    for r in rows:
        k = r.get("api_key", "")
        r["api_key_masked"] = k[:8] + "..." + k[-4:] if len(k) > 12 else "***"
        del r["api_key"]
    pool_size = len(_key_pool)
    return {"keys": rows, "pool_size": pool_size}


@app.post("/api/admin/gemini-keys")
def add_gemini_key(req: GeminiKeyRequest):
    resp = _sb_admin_request(
        "POST", "gemini_keys",
        prefer="return=representation",
        json={"label": req.label, "api_key": req.api_key, "is_active": True},
    )
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail=f"Key eklenemedi ({resp.status_code}): {resp.text[:200]}")
    global _key_pool_loaded_at
    _key_pool_loaded_at = 0.0
    # Body boş gelebilir — başarılı kabul et, listeden döndür
    try:
        data = resp.json()
        return data[0] if isinstance(data, list) and data else {"ok": True}
    except Exception:
        return {"ok": True}


@app.patch("/api/admin/gemini-keys/{key_id}")
def toggle_gemini_key(key_id: str, body: dict):
    is_active = body.get("is_active")
    if is_active is None:
        raise HTTPException(status_code=400, detail="is_active gerekli")
    resp = _sb_admin_request("PATCH", f"gemini_keys?id=eq.{key_id}",
        json={"is_active": is_active})
    if resp.status_code not in (200, 204):
        raise HTTPException(status_code=500, detail="Güncellenemedi")
    global _key_pool_loaded_at
    _key_pool_loaded_at = 0.0
    return {"ok": True}


@app.delete("/api/admin/gemini-keys/{key_id}")
def delete_gemini_key(key_id: str):
    resp = _sb_admin_request("DELETE", f"gemini_keys?id=eq.{key_id}")
    if resp.status_code not in (200, 204):
        raise HTTPException(status_code=500, detail="Silinemedi")
    global _key_pool_loaded_at
    _key_pool_loaded_at = 0.0
    return {"ok": True}


# ──────────────── SPRINT 2 — SEKTÖR RAG OTOMATİK TARAYICI ────────────────

# Devam eden tarama görevlerini izlemek için in-memory state
_crawl_jobs: Dict[str, dict] = {}  # sector_id -> {status, started_at, result, error}


class SectorCrawlRequest(BaseModel):
    sector_id: str
    sector_slug: str
    sector_name: str
    extra_keywords: Optional[List[str]] = None   # Admin manuel keyword ekleyebilir
    use_gsc: bool = False                         # GSC verisini de kullansın mı
    org_id: Optional[str] = None                 # use_gsc=True ise gerekli


def _run_sector_crawl(sector_id: str, sector_slug: str, sector_name: str,
                      extra_keywords: Optional[List[str]], use_gsc: bool,
                      org_id: Optional[str]) -> None:
    """Background task: sektörü tara ve sector_intelligence'a kaydet."""
    import httpx as _httpx
    from core.sector_crawler import SectorCrawler

    _crawl_jobs[sector_id]["status"] = "running"
    _crawl_jobs[sector_id]["started_at"] = time.time()

    try:
        # GSC keyword'leri al (isteğe bağlı)
        gsc_keywords: Optional[List[str]] = None
        if use_gsc and org_id:
            try:
                gsc_keywords = _fetch_gsc_top_queries(org_id, limit=15)
            except Exception as gsc_err:
                print(f"[CRAWL] GSC alınamadı ({org_id}): {gsc_err}")

        crawler = SectorCrawler()
        intel = crawler.crawl(
            sector_slug=sector_slug,
            sector_name=sector_name,
            gsc_keywords=extra_keywords or gsc_keywords,
        )

        if "error" in intel:
            _crawl_jobs[sector_id]["status"] = "error"
            _crawl_jobs[sector_id]["error"] = intel["error"]
            return

        quality = intel.get("quality_score", 5)
        crawled_at = intel["keywords"].get("crawled_at", "")

        sb_url = os.getenv("SUPABASE_URL", "")
        sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        headers = {
            "apikey": sb_key,
            "Authorization": f"Bearer {sb_key}",
            "Content-Type": "application/json",
        }

        saved_layers: list[str] = []
        for data_type in ("keywords", "faq", "competitor"):
            content = intel.get(data_type)
            if not content:
                continue

            # Önce mevcut crawler kaydını sil (upsert benzeri)
            _httpx.delete(
                f"{sb_url}/rest/v1/sector_intelligence"
                f"?sector_id=eq.{sector_id}&data_type=eq.{data_type}&source=eq.crawler",
                headers=headers,
                timeout=10,
            )

            # Yeni kayıt ekle
            resp = _httpx.post(
                f"{sb_url}/rest/v1/sector_intelligence",
                headers={**headers, "Prefer": "return=minimal"},
                json={
                    "sector_id": sector_id,
                    "data_type": data_type,
                    "content": content,
                    "quality_score": quality,
                    "source": "crawler",
                    "notes": (
                        f"DuckDuckGo SERP taraması • {intel.get('serp_results_count', 0)} sonuç • "
                        f"{intel.get('pages_scraped', 0)} sayfa kazındı"
                        + (" • GSC verisi entegre" if gsc_keywords else "")
                    ),
                },
                timeout=10,
            )
            if resp.status_code in (200, 201):
                saved_layers.append(data_type)
            else:
                print(f"[CRAWL] {data_type} kaydedilemedi: {resp.status_code} {resp.text[:200]}")

        _crawl_jobs[sector_id]["status"] = "completed"
        _crawl_jobs[sector_id]["saved_layers"] = saved_layers
        _crawl_jobs[sector_id]["quality_score"] = quality
        _crawl_jobs[sector_id]["serp_count"] = intel.get("serp_results_count", 0)
        _crawl_jobs[sector_id]["pages_scraped"] = intel.get("pages_scraped", 0)
        _crawl_jobs[sector_id]["elapsed_sn"] = round(time.time() - _crawl_jobs[sector_id]["started_at"], 1)

        print(f"[CRAWL] {sector_name} tamamlandı: {saved_layers}, Q={quality}")

    except Exception as exc:
        _crawl_jobs[sector_id]["status"] = "error"
        _crawl_jobs[sector_id]["error"] = str(exc)[:300]
        print(f"[CRAWL] {sector_name} HATA: {exc}")


@app.post("/api/admin/sector/crawl")
def start_sector_crawl(req: SectorCrawlRequest, bg_tasks: BackgroundTasks):
    """Belirtilen sektör için arka planda SERP taraması başlatır.

    Tarama sonuçları sector_intelligence tablosuna 'crawler' kaynağıyla kaydedilir.
    Mevcut 'crawler' kayıtları güncellenir, 'admin' kayıtlarına dokunulmaz.
    """
    sector_id = req.sector_id

    # Zaten çalışıyorsa reddet
    existing = _crawl_jobs.get(sector_id, {})
    if existing.get("status") == "running":
        return {
            "status": "already_running",
            "message": f"{req.sector_name} için tarama zaten devam ediyor",
        }

    _crawl_jobs[sector_id] = {
        "status": "queued",
        "sector_name": req.sector_name,
        "sector_slug": req.sector_slug,
        "started_at": None,
        "elapsed_sn": None,
        "saved_layers": [],
        "quality_score": None,
        "error": None,
    }

    bg_tasks.add_task(
        _run_sector_crawl,
        sector_id=sector_id,
        sector_slug=req.sector_slug,
        sector_name=req.sector_name,
        extra_keywords=req.extra_keywords,
        use_gsc=req.use_gsc,
        org_id=req.org_id,
    )

    return {
        "status": "queued",
        "message": f"{req.sector_name} taraması başlatıldı",
        "sector_id": sector_id,
    }


@app.get("/api/admin/sector/crawl/{sector_id}")
def get_crawl_status(sector_id: str):
    """Tarama görevinin durumunu döner."""
    job = _crawl_jobs.get(sector_id)
    if not job:
        return {"status": "not_started"}
    return job


# ──────────────── GOOGLE SEARCH CONSOLE ENTEGRASYONu ────────────────


def _fetch_gsc_top_queries(org_id: str, limit: int = 20) -> list[str]:
    """
    Bir firmanın GSC bağlantısından top arama sorgularını çeker.
    Döner: ["sorgu1", "sorgu2", ...]  veya boş liste.
    """
    import httpx as _httpx

    sb_url = os.getenv("SUPABASE_URL", "")
    sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    headers = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}

    # firma_profil.__gsc__ içinden token al
    r = _httpx.get(
        f"{sb_url}/rest/v1/organizations",
        params={"id": f"eq.{org_id}", "select": "firma_profil"},
        headers=headers,
        timeout=8,
    )
    if r.status_code != 200 or not r.json():
        return []

    profil = r.json()[0].get("firma_profil") or {}
    gsc = profil.get("__gsc__", {})
    refresh_token = gsc.get("refresh_token")
    property_url = gsc.get("property_url")
    if not refresh_token or not property_url:
        return []

    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return []

    # Refresh token → access token
    token_resp = _httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=10,
    )
    if token_resp.status_code != 200:
        return []

    access_token = token_resp.json().get("access_token", "")
    if not access_token:
        return []

    # GSC Search Analytics API — son 90 günün top sorguları
    from datetime import date, timedelta
    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=90)).isoformat()

    gsc_resp = _httpx.post(
        f"https://searchconsole.googleapis.com/webmasters/v3/sites/{property_url}/searchAnalytics/query",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query"],
            "rowLimit": limit,
            "orderBy": [{"fieldName": "impressions", "sortOrder": "DESCENDING"}],
        },
        timeout=15,
    )
    if gsc_resp.status_code != 200:
        return []

    rows = gsc_resp.json().get("rows", [])
    return [row["keys"][0] for row in rows if row.get("keys")]


class SaveGoogleOAuthRequest(BaseModel):
    org_id: str
    client_id: str
    client_secret: str

@app.post("/api/integrations/gsc/save-credentials")
def gsc_save_credentials(req: SaveGoogleOAuthRequest):
    """Google OAuth credentials'ı firma_profil.__google_oauth__ altına kaydeder (service role)."""
    import httpx as _httpx
    sb_url = os.getenv("SUPABASE_URL", "")
    sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    headers = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}

    # Mevcut profili koru
    profil = _get_org_profil(req.org_id) if sb_url else {}
    profil["__google_oauth__"] = {
        "client_id": req.client_id.strip(),
        "client_secret": req.client_secret.strip(),
    }

    r = _httpx.patch(
        f"{sb_url}/rest/v1/organizations?id=eq.{req.org_id}",
        headers={**headers, "Content-Type": "application/json"},
        json={"firma_profil": profil},
        timeout=10,
    )
    if r.status_code not in (200, 204):
        raise HTTPException(status_code=500, detail="Kayıt başarısız")
    return {"ok": True}


def _get_org_profil(org_id: str) -> dict:
    """Org'un firma_profil JSONB'sini Supabase'den çeker."""
    import httpx as _httpx
    sb_url = os.getenv("SUPABASE_URL", "")
    sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    r = _httpx.get(
        f"{sb_url}/rest/v1/organizations",
        params={"id": f"eq.{org_id}", "select": "firma_profil"},
        headers={"apikey": sb_key, "Authorization": f"Bearer {sb_key}"},
        timeout=8,
    )
    if r.status_code == 200 and r.json():
        return r.json()[0].get("firma_profil") or {}
    return {}


@app.get("/api/integrations/gsc/auth-url")
def gsc_auth_url(org_id: str):
    """Google OAuth consent URL döner. Frontend bu URL'yi açar."""
    import urllib.parse

    # Önce org'un kendi credentials'ını dene, yoksa env var'a bak
    profil = _get_org_profil(org_id)
    google_oauth = profil.get("__google_oauth__", {})
    client_id = google_oauth.get("client_id") or os.getenv("GOOGLE_CLIENT_ID", "")

    if not client_id:
        raise HTTPException(
            status_code=503,
            detail="Google Client ID girilmemiş. Ayarlar → Entegrasyonlar sayfasından ekleyin."
        )

    backend_url = os.getenv("BACKEND_URL", "").rstrip("/")
    if not backend_url:
        raise HTTPException(status_code=503, detail="BACKEND_URL env var eksik")

    params = {
        "client_id": client_id,
        "redirect_uri": f"{backend_url}/api/integrations/gsc/callback",
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/webmasters.readonly",
        "access_type": "offline",
        "prompt": "consent",
        "state": org_id,
    }
    url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)
    return {"url": url}


@app.get("/api/integrations/gsc/callback")
def gsc_oauth_callback(code: str, state: str):
    """Google OAuth callback. Token'ları alıp Supabase'e kaydeder."""
    import httpx as _httpx
    import urllib.parse

    backend_url = os.getenv("BACKEND_URL", "").rstrip("/")
    frontend_url = os.getenv("FRONTEND_URL", "https://pixra.co").rstrip("/")
    org_id = state

    # Org'un kendi credentials'ını al, yoksa env var
    profil = _get_org_profil(org_id)
    google_oauth = profil.get("__google_oauth__", {})
    client_id = google_oauth.get("client_id") or os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = google_oauth.get("client_secret") or os.getenv("GOOGLE_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth credentials eksik")

    # Code → tokens
    token_resp = _httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": f"{backend_url}/api/integrations/gsc/callback",
            "grant_type": "authorization_code",
        },
        timeout=15,
    )

    if token_resp.status_code != 200:
        # Frontend'e hata ile redirect
        from fastapi.responses import RedirectResponse
        return RedirectResponse(f"{frontend_url}/settings?gsc=error&detail=token_exchange_failed")

    tokens = token_resp.json()
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(f"{frontend_url}/settings?gsc=error&detail=no_refresh_token")

    # Property listesi çek → ilk siteyi varsayılan yap
    site_list_resp = _httpx.get(
        "https://searchconsole.googleapis.com/webmasters/v3/sites",
        headers={"Authorization": f"Bearer {tokens.get('access_token', '')}"},
        timeout=10,
    )
    property_url = ""
    if site_list_resp.status_code == 200:
        sites = site_list_resp.json().get("siteEntry", [])
        if sites:
            property_url = urllib.parse.quote(sites[0].get("siteUrl", ""), safe="")

    # Supabase'e kaydet — firma_profil.__gsc__ altında
    sb_url = os.getenv("SUPABASE_URL", "")
    sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    headers = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}

    # Mevcut profil zaten çekildi (_get_org_profil ile), yeniden kullan
    if not profil:
        profil = _get_org_profil(org_id)

    profil["__gsc__"] = {
        "refresh_token": refresh_token,
        "property_url": urllib.parse.unquote(property_url),
        "connected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sites_count": len(site_list_resp.json().get("siteEntry", [])) if site_list_resp.status_code == 200 else 0,
    }

    _httpx.patch(
        f"{sb_url}/rest/v1/organizations?id=eq.{org_id}",
        headers={**headers, "Content-Type": "application/json"},
        json={"firma_profil": profil},
        timeout=10,
    )

    # Frontend'e başarı ile redirect
    from fastapi.responses import RedirectResponse
    return RedirectResponse(f"{frontend_url}/settings?gsc=connected&tab=integrations")


@app.get("/api/integrations/gsc/status")
def gsc_status(org_id: str):
    """Firmanın GSC bağlantı durumunu döner."""
    import httpx as _httpx

    sb_url = os.getenv("SUPABASE_URL", "")
    sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    headers = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}

    r = _httpx.get(
        f"{sb_url}/rest/v1/organizations",
        params={"id": f"eq.{org_id}", "select": "firma_profil"},
        headers=headers,
        timeout=8,
    )
    if r.status_code != 200 or not r.json():
        return {"connected": False}

    profil = r.json()[0].get("firma_profil") or {}
    gsc = profil.get("__gsc__", {})

    if not gsc.get("refresh_token"):
        return {"connected": False}

    return {
        "connected": True,
        "property_url": gsc.get("property_url", ""),
        "connected_at": gsc.get("connected_at", ""),
        "sites_count": gsc.get("sites_count", 0),
    }


@app.delete("/api/integrations/gsc/disconnect")
def gsc_disconnect(org_id: str):
    """GSC bağlantısını kaldırır (token'ları siler)."""
    import httpx as _httpx

    sb_url = os.getenv("SUPABASE_URL", "")
    sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    headers = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}

    r = _httpx.get(
        f"{sb_url}/rest/v1/organizations",
        params={"id": f"eq.{org_id}", "select": "firma_profil"},
        headers=headers,
        timeout=8,
    )
    if r.status_code == 200 and r.json():
        profil = r.json()[0].get("firma_profil") or {}
        profil.pop("__gsc__", None)

        _httpx.patch(
            f"{sb_url}/rest/v1/organizations?id=eq.{org_id}",
            headers={**headers, "Content-Type": "application/json"},
            json={"firma_profil": profil},
            timeout=10,
        )

    return {"ok": True, "message": "GSC bağlantısı kaldırıldı"}


@app.get("/api/integrations/gsc/top-queries")
def gsc_top_queries(org_id: str, limit: int = 30):
    """Firmanın GSC'sinden son 90 günün top arama sorgularını döner."""
    try:
        queries = _fetch_gsc_top_queries(org_id, limit=limit)
        return {"queries": queries, "count": len(queries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GSC verisi alınamadı: {str(e)}")
