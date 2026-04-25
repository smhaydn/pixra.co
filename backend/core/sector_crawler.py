"""Sprint 2 — Sektör İstihbarat Otomatik Tarayıcı

Ücretsiz SERP verisi: duckduckgo-search (API key yok, %100 ücretsiz)
Sayfa kazıma:        httpx + BeautifulSoup
İleride güçlendirme: Google Search Console API (org bazlı OAuth)

Bir sektör taraması:
  - ~4 DuckDuckGo sorgusu
  - ~4 rakip sayfa kazıma
  - Süre: ~30-60 saniye
  - Maliyet: 0 TL

Çıktı: sector_intelligence tablosuna hazır {keywords, faq, competitor} objeleri.
"""

from __future__ import annotations

import re
import time
import logging
from collections import Counter
from typing import Optional

logger = logging.getLogger(__name__)

# ──────────────── SEKTÖR SORGU ŞABLONLARı ────────────────

SECTOR_QUERIES: dict[str, list[str]] = {
    "ic_giyim": [
        "pamuklu sütyen modelleri fiyatları türkiye",
        "balensiz sütyen yorumları nasıl seçilir",
        "iç çamaşır beden tablosu nasıl ölçülür",
        "sütyen kablo balina avantajı dezavantajı",
    ],
    "gumus_taki": [
        "925 ayar gümüş kolye fiyatları türkiye",
        "gümüş takı kararma nasıl önlenir bakım",
        "gerçek gümüş nasıl anlaşılır sahte ayrımı",
        "el yapımı gümüş takı marka tavsiye türkiye",
    ],
    "kadin_canta": [
        "hakiki deri çanta nasıl anlaşılır sahte",
        "kadın çanta bakımı uzun ömür nasıl",
        "omuz kol çanta boy uyumu nasıl seçilir",
        "uygun fiyat kaliteli kadın çanta türkiye",
    ],
    "hirdavat": [
        "akülü matkap tavsiye fiyat türkiye 2024",
        "el aleti seti ev kullanımı başlangıç",
        "profesyonel alet markası karşılaştırma inceleme",
        "hırdavat ürünü kalite nasıl anlaşılır",
    ],
    "ayakkabi": [
        "deri ayakkabı bakımı uzun ömür nasıl",
        "ayakkabı numarası ölçüm beden tablosu türkiye",
        "kaliteli spor ayakkabı tavsiye fiyat 2024",
        "ayakkabı içi taban malzeme farkı nedir",
    ],
    "elektronik": [
        "bluetooth kulaklık inceleme karşılaştırma türkiye",
        "türkiye garantili vs paralel ithalat fark",
        "akıllı saat hangi marka tavsiye 2024",
        "elektronik ürün garanti koşulları türkiye",
    ],
    "kozmetik": [
        "cilt tipine göre nemlendirici nasıl seçilir",
        "retinol kullanımı yeni başlayanlar rehber",
        "uzun kalıcı parfüm tavsiye bütçe türkiye",
        "organik doğal kozmetik marka türkiye 2024",
    ],
    "mobilya_ev": [
        "mdf masif ahşap fark mobilya kalite",
        "küçük oda mobilya seçimi pratik öneriler",
        "e1 formaldehit emisyonu mobilya sağlık",
        "montajlı mobilya kargo teslimat sorunları",
    ],
    "spor": [
        "koşu ayakkabısı nasıl seçilir yeni başlayan",
        "sporcu giysisi nem giderici kumaş farkı",
        "yoga matı kalınlık malzeme nasıl seçilir",
        "fitness ekipmanı ev spor salonu tavsiye",
    ],
    "bebek_cocuk": [
        "bebek giysileri organik pamuk neden önemli",
        "oeko-tex sertifikası nedir bebek ürünleri güvenlik",
        "bebek beden tablosu aylık kilo boy",
        "bebek oyuncak güvenlik standardı türkiye",
    ],
    "kadin_giyim": [
        "boy tipine göre kıyafet seçimi kadın rehber",
        "kumaş kalitesi nasıl anlaşılır etiket bakımı",
        "sezon modası giyim kadın 2025 trend",
        "uygun kaliteli kadın giyim marka türkiye",
    ],
    "genel": [
        "e-ticaret kaliteli ürün seçimi ipuçları türkiye",
        "online alışveriş kalite güvenilir nasıl anlaşılır",
        "ürün yorumları değerlendirme güvenilirlik",
    ],
}

# Türkçe stopword seti (keyword extraction için)
_TR_STOPWORDS = {
    "ve", "ile", "bu", "bir", "de", "da", "için", "olan", "var", "çok",
    "daha", "en", "ne", "nasıl", "gibi", "kadar", "sonra", "mi", "mu",
    "mı", "her", "ama", "ya", "veya", "ki", "bu", "şu", "ya", "da",
    "olan", "olur", "oldu", "olan", "olan", "hangi", "neden", "kere",
    "göre", "biri", "bazı", "tüm", "aynı", "hem", "ise", "bile",
    "yani", "sadece", "çünkü", "ancak", "fakat", "lakin", "oysa",
}


class SectorCrawler:
    """
    DuckDuckGo SERP + BeautifulSoup ile sektör bazlı rakip analizi yapar.

    Kullanım:
        crawler = SectorCrawler()
        intel = crawler.crawl("ic_giyim", "İç Çamaşır")
        # intel: {"keywords": {...}, "faq": {...}, "competitor": {...}, "quality_score": 7}
    """

    MAX_RESULTS_PER_QUERY = 8   # DuckDuckGo'dan çekilecek sonuç sayısı
    MAX_PAGES_TO_SCRAPE = 4     # Kazınacak rakip sayfa sayısı
    SERP_DELAY = 1.2            # DuckDuckGo rate limit koruması (saniye)
    PAGE_DELAY = 1.0            # Sayfa kazıma arası bekleme

    # Kazıma başlığı — bot olduğumuzu açıkça belirtiyoruz (iyi niyetli)
    CRAWLER_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; Pixra-SectorBot/1.0; "
            "+https://pixra.co/robots.txt)"
        ),
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
    }

    # ──────────────── ANA METOD ────────────────

    def crawl(
        self,
        sector_slug: str,
        sector_name: str,
        gsc_keywords: list[str] | None = None,
    ) -> dict:
        """
        Sektör için tam tarama yapar.

        Args:
            sector_slug:   Sektör slug'ı (örn: "ic_giyim")
            sector_name:   İnsan okunabilir isim (örn: "İç Çamaşır")
            gsc_keywords:  GSC'den gelen gerçek arama terimleri (varsa öncelikli kullanılır)

        Returns:
            {
                "keywords":      {...},   # sector_intelligence content
                "faq":           {...},   # sector_intelligence content
                "competitor":    {...},   # sector_intelligence content
                "quality_score": int,     # 0-10
                "crawled_queries": [...], # hangi sorgular çalıştı
            }
        """
        base_queries = SECTOR_QUERIES.get(sector_slug, SECTOR_QUERIES["genel"])

        # GSC keyword varsa ekstra sorgular oluştur
        extra_queries = []
        if gsc_keywords:
            for kw in gsc_keywords[:3]:
                extra_queries.append(f"{kw} nasıl seçilir rehber")
                extra_queries.append(f"{kw} fiyat türkiye karşılaştırma")

        queries = (extra_queries + base_queries)[:6]  # max 6 sorgu

        all_results: list[dict] = []
        ran_queries: list[str] = []

        try:
            from duckduckgo_search import DDGS  # pip install duckduckgo-search
        except ImportError:
            logger.error(
                "[CRAWLER] 'duckduckgo-search' yüklü değil. "
                "Çalıştır: pip install duckduckgo-search"
            )
            return {"error": "duckduckgo-search not installed"}

        with DDGS() as ddgs:
            for query in queries:
                try:
                    results = list(
                        ddgs.text(
                            query,
                            max_results=self.MAX_RESULTS_PER_QUERY,
                            region="tr-tr",
                        )
                    )
                    all_results.extend(results)
                    ran_queries.append(query)
                    time.sleep(self.SERP_DELAY)
                except Exception as e:
                    logger.warning(f"[CRAWLER] Sorgu hatası ({query[:35]!r}): {e}")

        if not all_results:
            logger.warning(f"[CRAWLER] {sector_slug} için hiç SERP sonucu alınamadı")
            return {"error": "no_serp_results", "crawled_queries": ran_queries}

        logger.info(
            f"[CRAWLER] {sector_slug}: {len(ran_queries)} sorgu, "
            f"{len(all_results)} SERP sonucu"
        )

        # ── Çıkarım aşamaları ──
        keywords_intel = self._extract_keywords(all_results, sector_name, gsc_keywords)
        faq_intel = self._extract_faq(all_results, sector_name)
        competitor_intel = self._extract_competitors(all_results)

        # ── Sayfa kazıma (best-effort, hata olursa devam) ──
        top_urls = [
            r["href"]
            for r in all_results[:self.MAX_PAGES_TO_SCRAPE]
            if r.get("href") and r["href"].startswith("http")
        ]
        scraped = self._scrape_pages(top_urls)

        if scraped:
            faq_intel = self._enrich_faq_from_pages(faq_intel, scraped)
            competitor_intel = self._enrich_competitors_from_pages(competitor_intel, scraped)
            logger.info(f"[CRAWLER] {len(scraped)} sayfa başarıyla kazındı")

        quality = self._calculate_quality(keywords_intel, faq_intel, competitor_intel)

        return {
            "keywords": keywords_intel,
            "faq": faq_intel,
            "competitor": competitor_intel,
            "quality_score": quality,
            "crawled_queries": ran_queries,
            "serp_results_count": len(all_results),
            "pages_scraped": len(scraped),
        }

    # ──────────────── KEYWORD EXTRACTION ────────────────

    def _extract_keywords(
        self,
        results: list[dict],
        sector_name: str,
        gsc_keywords: list[str] | None = None,
    ) -> dict:
        """SERP snippet + başlıklardan keyword kümeleri çıkar."""
        all_text = " ".join(
            (r.get("body") or "") + " " + (r.get("title") or "")
            for r in results
        ).lower()

        # Kelime frekansı (4+ harf Türkçe kelimeler)
        words = re.findall(r"\b[a-züğışçö]{4,}\b", all_text)
        freq = Counter(w for w in words if w not in _TR_STOPWORDS)
        top_terms = [w for w, _ in freq.most_common(25)]

        # Başlıklardan anlamlı ifade çıkar
        all_phrases: list[str] = []
        for r in results[:20]:
            title = r.get("title") or ""
            for sep in ("-", "|", "–", "—", ",", "·"):
                for part in title.split(sep):
                    part = part.strip()
                    if 8 < len(part) < 70:
                        all_phrases.append(part)

        # Transactional: fiyat/satın al içerenler
        transactional_kw = [
            p for p in all_phrases
            if any(k in p.lower() for k in ["fiyat", "satın", "tl", "kampanya", "indirim", "ucuz", "uygun"])
        ][:8]
        if not transactional_kw:
            transactional_kw = [f"{sector_name} fiyatları", f"en iyi {sector_name} türkiye"]

        # Informational: nasıl/ne/rehber içerenler
        informational_kw = [
            p for p in all_phrases
            if any(k in p.lower() for k in ["nasıl", "nedir", "rehber", "ipuç", "tavsiye", "öneri", "hata"])
        ][:8]
        if not informational_kw:
            informational_kw = [f"{sector_name} nasıl seçilir", f"{sector_name} rehberi"]

        clusters = [
            {
                "intent": "transactional",
                "keywords": transactional_kw,
                "top_terms": top_terms[:15],
                "difficulty": "medium",
            },
            {
                "intent": "informational",
                "keywords": informational_kw,
                "difficulty": "low",
            },
        ]

        # GSC keyword'leri varsa navigational cluster olarak ekle
        if gsc_keywords:
            clusters.append({
                "intent": "navigational",
                "keywords": gsc_keywords[:10],
                "source": "google_search_console",
                "difficulty": "mixed",
            })

        return {
            "clusters": clusters,
            "source": "duckduckgo_serp",
            "crawled_at": _now_iso(),
        }

    # ──────────────── FAQ EXTRACTION ────────────────

    def _extract_faq(self, results: list[dict], sector_name: str) -> dict:
        """Snippet ve başlıklardan olası SSS soruları çıkar."""
        questions: list[dict] = []

        for r in results:
            for field in ("title", "body"):
                text = r.get(field) or ""
                # Soru işareti içeren cümleler
                for match in re.finditer(r"[A-ZÜĞİŞÇÖa-züğışçö][^.!?]{10,100}\?", text):
                    q = match.group().strip()
                    if len(q) > 15:
                        questions.append({
                            "soru": q,
                            "cevap_tipi": "informational",
                            "intent": "informational",
                            "kaynak": (r.get("href") or "")[:60],
                        })

                # "nasıl" "nedir" "neden" "hangi" gibi kalıplar (soru işareti olmadan)
                for kw in ("nasıl ", "nedir ", "neden ", "hangi ", "ne zaman "):
                    start = text.lower().find(kw)
                    while start != -1:
                        end = text.find(".", start)
                        if end == -1:
                            end = min(start + 100, len(text))
                        snippet = text[start:end].strip()
                        if 15 < len(snippet) < 120:
                            questions.append({
                                "soru": snippet[0].upper() + snippet[1:] + "?",
                                "cevap_tipi": "informational",
                                "intent": "informational",
                                "kaynak": (r.get("href") or "")[:60],
                            })
                        start = text.lower().find(kw, start + 1)

        # Tekilleştir (ilk 30 karakter bazlı)
        seen: set[str] = set()
        unique: list[dict] = []
        for q in questions:
            key = q["soru"][:30].lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(q)

        return {
            "questions": unique[:15],
            "source": "duckduckgo_serp",
            "crawled_at": _now_iso(),
        }

    # ──────────────── COMPETITOR EXTRACTION ────────────────

    def _extract_competitors(self, results: list[dict]) -> dict:
        """SERP sonuçlarından rakip domain + içerik pattern'i çıkar."""
        sites: list[dict] = []
        seen_domains: set[str] = set()

        for r in results:
            url = r.get("href") or ""
            title = r.get("title") or ""
            body = r.get("body") or ""

            if not url:
                continue

            domain_m = re.search(r"https?://([^/]+)", url)
            domain = domain_m.group(1) if domain_m else url[:50]

            # Kendi domainimizi hariç tut
            if domain in seen_domains or "pixra" in domain:
                continue
            seen_domains.add(domain)

            sites.append({
                "url": domain,
                "full_url": url[:120],
                "title_pattern": title[:80],
                "meta_pattern": body[:150],
            })

        return {
            "sites": sites[:10],
            "source": "duckduckgo_serp",
            "crawled_at": _now_iso(),
        }

    # ──────────────── SAYFA KAZIMA ────────────────

    def _scrape_pages(self, urls: list[str]) -> list[dict]:
        """Rakip sayfaları kazı: başlık, meta desc, H2/H3 headings."""
        results: list[dict] = []

        try:
            import httpx
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("[CRAWLER] beautifulsoup4 veya lxml yüklü değil")
            return []

        for url in urls:
            try:
                resp = httpx.get(
                    url,
                    headers=self.CRAWLER_HEADERS,
                    timeout=8,
                    follow_redirects=True,
                )
                if resp.status_code != 200:
                    continue

                # Sadece HTML
                ct = resp.headers.get("content-type", "")
                if "html" not in ct:
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # Meta description
                meta_tag = soup.find("meta", attrs={"name": re.compile("description", re.I)})
                meta_desc = ""
                if meta_tag and isinstance(meta_tag, object):
                    meta_desc = str(meta_tag.get("content", ""))[:200]  # type: ignore[attr-defined]

                # Title
                title_tag = soup.find("title")
                page_title = title_tag.get_text(strip=True)[:100] if title_tag else ""

                # H2/H3 başlıklar (genellikle FAQ bölümleri)
                headings: list[str] = []
                for tag in soup.find_all(["h2", "h3"], limit=12):
                    h = tag.get_text(strip=True)
                    if 10 < len(h) < 120:
                        headings.append(h)

                results.append({
                    "url": url[:100],
                    "title": page_title,
                    "meta_desc": meta_desc,
                    "headings": headings,
                })

                time.sleep(self.PAGE_DELAY)

            except Exception as e:
                logger.debug(f"[CRAWLER] Sayfa kazınamadı ({url[:50]!r}): {e}")

        return results

    def _enrich_faq_from_pages(self, faq_intel: dict, scraped: list[dict]) -> dict:
        """Sayfa H2/H3 başlıklarından ek SSS soruları ekle."""
        extra: list[dict] = []
        for page in scraped:
            for h in page.get("headings", []):
                is_question = "?" in h or any(
                    k in h.lower()
                    for k in ("nasıl", "nedir", "neden", "hangi", "ne zaman", "kaç")
                )
                if is_question:
                    extra.append({
                        "soru": h,
                        "cevap_tipi": "informational",
                        "intent": "informational",
                        "kaynak": page.get("url", "")[:60],
                    })

        existing = faq_intel.get("questions", [])
        seen = {q["soru"][:30].lower() for q in existing}
        for q in extra:
            key = q["soru"][:30].lower()
            if key not in seen:
                existing.append(q)
                seen.add(key)

        faq_intel["questions"] = existing[:18]
        return faq_intel

    def _enrich_competitors_from_pages(
        self, competitor_intel: dict, scraped: list[dict]
    ) -> dict:
        """Sayfa içeriğiyle rakip meta description pattern'lerini güçlendir."""
        sites = competitor_intel.get("sites", [])
        for page in scraped:
            page_domain = re.sub(r"https?://([^/]+).*", r"\1", page.get("url", ""))
            for site in sites:
                if page_domain in site.get("url", ""):
                    if page.get("meta_desc"):
                        site["meta_pattern"] = page["meta_desc"]
                    if page.get("title") and not site.get("title_pattern"):
                        site["title_pattern"] = page["title"]
                    break
        competitor_intel["sites"] = sites
        return competitor_intel

    # ──────────────── KALİTE HESAPLAMA ────────────────

    def _calculate_quality(
        self, keywords: dict, faq: dict, competitor: dict
    ) -> int:
        """
        Otomatik kalite skoru: 0-10 arası.
        3 baz puan + keyword/faq/competitor zenginliğine göre artar.
        """
        score = 3  # Tarama başarıyla tamamlandı

        clusters = keywords.get("clusters", [])
        kw_count = sum(len(c.get("keywords", [])) for c in clusters)
        top_terms = len(clusters[0].get("top_terms", [])) if clusters else 0

        if kw_count >= 8:
            score += 2
        elif kw_count >= 4:
            score += 1

        if top_terms >= 15:
            score += 1

        faq_count = len(faq.get("questions", []))
        if faq_count >= 10:
            score += 2
        elif faq_count >= 5:
            score += 1

        comp_count = len(competitor.get("sites", []))
        if comp_count >= 6:
            score += 1

        # GSC verisi bonus
        has_gsc = any(
            c.get("source") == "google_search_console"
            for c in keywords.get("clusters", [])
        )
        if has_gsc:
            score += 1

        return min(score, 10)


# ──────────────── YARDIMCI ────────────────

def _now_iso() -> str:
    import datetime
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
