"""
Ticimax AI Manager — Arka Plan Worker Thread'leri
Ticimax API cagrilari, Gemini Vision analizleri ve yerel klasor isleme worker'lari.
Fault-Tolerant: Exponential backoff retry, session checkpoint ve SOAP auto-reconnect iceriri.
"""

import os
import time
import tempfile

from PyQt6.QtCore import QThread, pyqtSignal

from ticimax_api import TicimaxClient
from vision_engine import VisionEngine, ProductAIContent
from helpers import get_field, download_image, safe_file_cleanup, SessionState


# ──────────────── TICIMAX WORKER ────────────────

class TicimaxWorker(QThread):
    """Ticimax API cagrilerini arka planda gerceklestiren worker.
    SOAP baglantisi koparsa otomatik yeniden baglanma (3 deneme) yapar."""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    log = pyqtSignal(str)

    MAX_RETRIES = 3

    def __init__(self, base_url: str, uye_kodu: str, kayit_sayisi: int = 50):
        """TicimaxWorker olusturucusu."""
        super().__init__()
        self.base_url = base_url
        self.uye_kodu = uye_kodu
        self.kayit_sayisi = kayit_sayisi

    def run(self):
        """Ticimax'ten urun listesini sayfa sayfa ceker. SOAP hatalarinda otomatik yeniden dener."""
        last_error = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                if attempt > 1:
                    self.log.emit(f"[YENIDEN DENEME] SOAP baglantisi kuruluyor... (Deneme {attempt}/{self.MAX_RETRIES})")
                    time.sleep(3 * attempt)
                else:
                    self.log.emit("Ticimax WSDL baglantisi olusturuluyor...")
                    
                client = TicimaxClient(base_url=self.base_url, uye_kodu=self.uye_kodu)
                self.log.emit("Baglanti basarili. Tum urunler sayfa sayfa cekiliyor...")
                urunler = client.get_urun_liste(urun_karti_id=0)
                self.log.emit(f"Toplam {len(urunler)} urun cekildi (otomatik sayfalama ile).")
                self.finished.emit(urunler)
                return  # Basarili, cik
            except Exception as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    self.log.emit(f"[UYARI] SOAP baglantisi basarisiz: {e}")
                    
        # Tum denemeler basarisiz
        self.error.emit(f"SOAP baglantisi {self.MAX_RETRIES} denemede de basarisiz: {last_error}")


# ──────────────── VISION WORKER ────────────────

class VisionWorker(QThread):
    """Gemini Vision analizlerini arka planda gerceklestiren worker.
    Fault-Tolerant: Her urun icin 3 deneme, checkpoint kaydi ve rate-limit korunmasi."""
    progress = pyqtSignal(int, int)  # mevcut, toplam
    product_done = pyqtSignal(int, object)  # satir_index, ai_result
    finished = pyqtSignal()
    error = pyqtSignal(int, str)  # satir_index, hata_mesaji
    log = pyqtSignal(str)

    MAX_RETRIES = 3       # Urun basi maksimum deneme
    MAX_IMAGES = 3        # Urun basi maksimum gorsel (hiz optimizasyonu)
    RATE_LIMIT_DELAY = 3  # Basarili istek arasi bekleme (saniye)
    ERROR_DELAY = 5       # Hata sonrasi bekleme (saniye)

    def __init__(self, api_key: str, urunler_data: list, site_domain: str, 
                 session_state: SessionState = None):
        """VisionWorker olusturucusu."""
        super().__init__()
        self.api_key = api_key
        self.urunler_data = urunler_data
        self.site_domain = site_domain
        self.session = session_state

    def run(self):
        """Her urun icin TUM gorselleri indirip Gemini analizi yapar.
        Basarisiz urunler icin exponential backoff ile yeniden dener."""
        try:
            engine = VisionEngine(api_key=self.api_key)
        except Exception as e:
            self.log.emit(f"[HATA] Vision Engine baslatilamadi: {e}")
            self.finished.emit()
            return

        toplam = len(self.urunler_data)
        total_start_time = time.time()
        basarili = 0
        basarisiz = 0
        stok_kodu_cache = {}  # Ayni stok kodlu urunleri gruplamak icin (Varyasyon tutarliligi)
        used_seo_titles = set() # Keyword cannibalization kontrolu icin
        
        for idx, urun_info in enumerate(self.urunler_data):
            self.progress.emit(idx + 1, toplam)
            urun = urun_info['raw']
            urun_adi = urun_info.get('urun_adi', '?')

            # Tum gorsel URL'lerini al
            resim_urls = urun_info.get('resim_urls', [])
            if not resim_urls:
                # Geriye uyumluluk: eski tekli format
                tek_url = urun_info.get('resim_url', '')
                if tek_url:
                    resim_urls = [tek_url]

            if not resim_urls:
                self.log.emit(f"[{idx+1}/{toplam}] {urun_adi} -> Gorsel bulunamadi, atlandi.")
                self.error.emit(idx, "Gorsel URL bulunamadi")
                basarisiz += 1
                if self.session:
                    self.session.mark_failed(idx, "Gorsel URL bulunamadi")
                continue

            # HIZ OPTIMIZASYONU: Maksimum gorsel siniri
            if len(resim_urls) > self.MAX_IMAGES:
                resim_urls = resim_urls[:self.MAX_IMAGES]

            self.log.emit(f"[{idx+1}/{toplam}] Isleniyor: {urun_adi} ({len(resim_urls)} gorsel)")

            # Gorselleri gecici dosyalara indir
            temp_paths = []
            for img_idx, img_url in enumerate(resim_urls):
                temp_path = os.path.join(tempfile.gettempdir(), f"ticimax_ai_{idx}_{img_idx}_{int(time.time())}.jpg")
                if download_image(img_url, temp_path):
                    temp_paths.append(temp_path)
                else:
                    self.log.emit(f"  -> Gorsel {img_idx+1} indirilemedi veya bos, atlandi.")

            if not temp_paths:
                self.log.emit(f"  -> Hicbir gecerli gorsel indirilemedi, urun atlandi.")
                self.error.emit(idx, "Gorseller gecersiz veya indirilemedi")
                basarisiz += 1
                if self.session:
                    self.session.mark_failed(idx, "Gorseller indirilemedi")
                continue

            # Ayni stok koduna sahip onceki bir analiz varsa, referans olarak kullan
            stok_kodu = str(get_field(urun, 'StokKodu', '')).strip()
            reference_content = ""
            if stok_kodu and stok_kodu in stok_kodu_cache:
                reference_content = stok_kodu_cache[stok_kodu]
                self.log.emit(f"  -> [VARYASYON] {stok_kodu} stok kodlu urun algoritmasi kullanilarak sadece renk/detaylara gore uyarlaniyor.")

            # RETRY MEKANIZMASI: Exponential Backoff
            ai_start_time = time.time()
            success = False
            
            for attempt in range(1, self.MAX_RETRIES + 1):
                try:
                    ai_result = engine.analyze_product_image(
                        image_path=temp_paths[0],
                        marka=urun_info.get('marka', ''),
                        adwords_aciklama=get_field(urun, 'AdwordsAciklama'),
                        adwords_kategori=get_field(urun, 'AdwordsKategori'),
                        adwords_tip=get_field(urun, 'AdwordsTip'),
                        breadcrumb_kat=get_field(urun, 'BreadcrumbKat'),
                        image_paths=temp_paths,
                        mevcut_urun_adi=urun_info.get('urun_adi', ''),
                        satisfiyati=str(get_field(urun, 'SatisFiyati', '')),
                        kategoriler=str(get_field(urun, 'Kategoriler', '')),
                        stok_kodu=stok_kodu,
                        reference_content=reference_content
                    )
                    
                    # Basarili analiz sonucunu cache'e ekle (sonrakiler icin referans olsun)
                    if stok_kodu and stok_kodu not in stok_kodu_cache:
                        stok_kodu_cache[stok_kodu] = ai_result.model_dump_json()
                    
                    # KALITE KONTROL KATMANI (QC)
                    # 1. Duplicate SEO Baslik kontrolu (Keyword Cannibalization onleme)
                    temp_baslik = ai_result.seo_baslik.strip()
                    if temp_baslik in used_seo_titles:
                        # Eger duplicate varsa, basliga urun adinin ilk 1-2 kelimesini ekle
                        ai_result.seo_baslik = f"{temp_baslik} - {urun_info.get('urun_adi', 'Yeni').split()[0]}"
                    
                    # 2. SEO Baslik Karakter Siniri Kontrolu (Sert kirpma degil, bosluktan akilli kirpma)
                    if len(ai_result.seo_baslik) > 60:
                        kesilmis = ai_result.seo_baslik[:60]
                        # Eger son kelime ortasinda kaldıysa, kelime oncesindeki bosluga kadar dön
                        son_bosluk = kesilmis.rfind(' ')
                        if son_bosluk > 40:
                            kesilmis = kesilmis[:son_bosluk]
                        ai_result.seo_baslik = kesilmis.strip()
                    
                    used_seo_titles.add(ai_result.seo_baslik)
                    
                    ai_elapsed = time.time() - ai_start_time
                    self.product_done.emit(idx, ai_result)
                    retry_info = f" (Deneme: {attempt})" if attempt > 1 else ""
                    self.log.emit(f"  -> [OK] {len(temp_paths)} gorsel analiz edildi. (Sure: {ai_elapsed:.1f}s){retry_info}")
                    basarili += 1
                    success = True
                    
                    # Checkpoint kaydet
                    if self.session:
                        self.session.mark_processed(idx, {
                            "urun_adi": ai_result.urun_adi,
                            "sure": round(ai_elapsed, 1)
                        })
                    
                    # Rate limit korunmasi
                    if idx < toplam - 1:
                        time.sleep(self.RATE_LIMIT_DELAY)
                    break  # Basarili, retry dongusunden cik
                    
                except Exception as e:
                    err_msg = str(e)
                    is_rate_limit = "429" in err_msg or "quota" in err_msg.lower()
                    
                    if attempt < self.MAX_RETRIES:
                        # Yeniden deneme bekleme suresi hesapla
                        delay = self.ERROR_DELAY * (3 ** (attempt - 1))
                        if is_rate_limit:
                            delay = delay * 2  # Rate limit icin ekstra bekleme
                        self.log.emit(f"  -> [RETRY {attempt}/{self.MAX_RETRIES}] Hata: {err_msg[:80]}... ({delay:.0f}s bekleniyor)")
                        time.sleep(delay)
                    else:
                        # Tum denemeler basarisiz
                        ai_elapsed = time.time() - ai_start_time
                        if is_rate_limit:
                            err_msg += " (API Limiti Asildi)"
                        self.log.emit(f"  -> [HATA] {self.MAX_RETRIES} denemede de basarisiz (Sure: {ai_elapsed:.1f}s): {err_msg[:120]}")
                        self.error.emit(idx, "Hata: " + err_msg[:200])
                        basarisiz += 1
                        if self.session:
                            self.session.mark_failed(idx, err_msg[:200])
                        time.sleep(self.ERROR_DELAY)

            # Gecici dosyalari temizle
            safe_file_cleanup(temp_paths)

        # Toplam sure ve ozet
        total_elapsed = time.time() - total_start_time
        mins, secs = divmod(total_elapsed, 60)
        self.log.emit(f"\n{'='*50}")
        self.log.emit(f"[OZET] Toplam islem suresi: {int(mins)} dakika {secs:.0f} saniye")
        self.log.emit(f"[OZET] Basarili: {basarili} | Basarisiz: {basarisiz} | Toplam: {toplam}")
        self.log.emit(f"{'='*50}")
        self.finished.emit()


# ──────────────── CREATE MODE WORKER ────────────────

class CreateModeWorker(QThread):
    """Yerel klasorden gorselleri okuyup sifirdan urun karti olusturan worker."""
    progress = pyqtSignal(int, int)
    product_done = pyqtSignal(int, str, object)  # idx, klasor_adi, ai_result
    finished = pyqtSignal()
    log = pyqtSignal(str)

    def __init__(self, api_key: str, folder_path: str):
        """CreateModeWorker olusturucusu."""
        super().__init__()
        self.api_key = api_key
        self.folder_path = folder_path

    def run(self):
        """Her alt klasor icin ilk gorseli analiz eder."""
        try:
            engine = VisionEngine(api_key=self.api_key)
        except Exception as e:
            self.log.emit(f"[HATA] Vision Engine baslatilamadi: {e}")
            self.finished.emit()
            return

        # Alt klasorleri tara
        alt_klasorler = []
        for item in sorted(os.listdir(self.folder_path)):
            item_path = os.path.join(self.folder_path, item)
            if os.path.isdir(item_path):
                alt_klasorler.append((item, item_path))

        if not alt_klasorler:
            # Alt klasor yoksa dogrudan ana klasordeki gorselleri isle
            gorseller = [f for f in sorted(os.listdir(self.folder_path))
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            for idx, g in enumerate(gorseller):
                self.progress.emit(idx + 1, len(gorseller))
                img_path = os.path.join(self.folder_path, g)
                self.log.emit(f"[{idx+1}/{len(gorseller)}] Isleniyor: {g}")
                try:
                    ai_result = engine.analyze_product_image(image_path=img_path, marka="")
                    self.product_done.emit(idx, os.path.splitext(g)[0], ai_result)
                    self.log.emit(f"  -> [OK] Basarili!")
                except Exception as e:
                    self.log.emit(f"  -> [HATA]: {e}")
            self.finished.emit()
            return

        toplam = len(alt_klasorler)
        for idx, (klasor_adi, klasor_yolu) in enumerate(alt_klasorler):
            self.progress.emit(idx + 1, toplam)
            self.log.emit(f"[{idx+1}/{toplam}] Klasor: {klasor_adi}")
            gorseller = [f for f in sorted(os.listdir(klasor_yolu))
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            if not gorseller:
                self.log.emit(f"  -> Gorsel bulunamadi, atlandi.")
                continue
            img_path = os.path.join(klasor_yolu, gorseller[0])
            try:
                ai_result = engine.analyze_product_image(image_path=img_path, marka="")
                self.product_done.emit(idx, klasor_adi, ai_result)
                self.log.emit(f"  -> [OK] {gorseller[0]} analiz edildi.")
            except Exception as e:
                self.log.emit(f"  -> [HATA]: {e}")

        self.finished.emit()
