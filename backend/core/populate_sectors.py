"""
Sektör İstihbarat Verisi Populate Scripti

Tüm Türk e-ticaret sektörleri için otomatik tarama ve DB populate.
Kullanım: python backend/core/populate_sectors.py
"""

import os
import json
import logging
from sector_crawler import SectorCrawler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECTORS = {
    "ic_giyim": "İç Çamaşır",
    "gumus_taki": "Gümüş Takı",
    "kadin_canta": "Kadın Çanta",
    "hirdavat": "Hırdavat",
    "ayakkabi": "Ayakkabı",
    "elektronik": "Elektronik",
    "kozmetik": "Kozmetik",
    "mobilya_ev": "Mobilya & Ev",
    "spor": "Spor",
    "bebek_cocuk": "Bebek & Çocuk",
    "kadin_giyim": "Kadın Giyim",
}


def populate_sector_intelligence():
    """Tüm sektörler için tarama yap, Supabase'e yükle."""
    
    import httpx
    from dotenv import load_dotenv
    
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    if not url or not key:
        logger.error("SUPABASE_URL veya SUPABASE_SERVICE_ROLE_KEY tanımlanmamış")
        return
    
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    
    # Sektör ID'lerini çek
    sector_map = {}
    r = httpx.get(
        f"{url}/rest/v1/sectors?select=id,slug",
        headers=headers,
        timeout=10
    )
    if r.status_code == 200:
        for row in r.json():
            sector_map[row["slug"]] = row["id"]
    
    logger.info(f"Bulundu {len(sector_map)} sektör: {list(sector_map.keys())}")
    
    crawler = SectorCrawler()
    
    for slug, display_name in SECTORS.items():
        if slug not in sector_map:
            logger.warning(f"Sektör bulunamadı: {slug}")
            continue
        
        sector_id = sector_map[slug]
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 Taraniyor: {display_name} ({slug})")
        logger.info(f"{'='*60}")
        
        try:
            result = crawler.crawl(slug, display_name)
            
            if "error" in result:
                logger.error(f"Tarama hatası: {result['error']}")
                continue
            
            # Sonuçları Supabase'e yükle
            _upload_sector_data(url, headers, sector_id, slug, result)
            
            logger.info(f"✅ Tamamlandı: {display_name}")
            logger.info(f"   - Quality: {result['quality_score']}/10")
            logger.info(f"   - SERP Sonuçları: {result['serp_results_count']}")
            logger.info(f"   - Kazınan Sayfalar: {result['pages_scraped']}")
            
        except Exception as e:
            logger.error(f"❌ {display_name} taraması başarısız: {e}")


def _upload_sector_data(url: str, headers: dict, sector_id: str, slug: str, result: dict):
    """Tarama sonuçlarını sector_intelligence tablosuna yükle."""
    
    import httpx
    
    data_types = {
        "keywords": result.get("keywords", {}),
        "faq": result.get("faq", {}),
        "competitor": result.get("competitor", {}),
    }
    
    for data_type, content in data_types.items():
        if not content:
            continue
        
        payload = {
            "sector_id": sector_id,
            "data_type": data_type,
            "content": content,
            "quality_score": result["quality_score"],
        }
        
        # Upsert: varsa güncelle, yoksa ekle
        r = httpx.post(
            f"{url}/rest/v1/sector_intelligence",
            json=payload,
            headers=headers,
            timeout=10,
            params={"on_conflict": "sector_id,data_type"}
        )
        
        if r.status_code in [200, 201]:
            logger.info(f"   ✓ {data_type} yüklendi")
        else:
            logger.warning(f"   ⚠ {data_type} yükleme hatası: {r.status_code} - {r.text[:100]}")


if __name__ == "__main__":
    populate_sector_intelligence()
    logger.info("\n" + "="*60)
    logger.info("✨ Sektör verisi populate işlemi tamamlandı")
    logger.info("="*60)
