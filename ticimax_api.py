import os
from typing import Dict, Any, List, Optional
from zeep import Client
from zeep.exceptions import Fault
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

class TicimaxClient:
    """
    Ticimax UrunServis SOAP API entegrasyonunu yöneten çekirdek sınıf.
    Multi-tenant kullanım için tüm bağlantı parametreleri dışarıdan alınabilir.
    """

    def __init__(self, base_url: str = None, uye_kodu: str = None) -> None:
        """
        TicimaxClient constructor metodu.
        
        Parametreler verilmezse .env dosyasından okunur (geriye uyumluluk).
        
        Args:
            base_url (str, optional): Ticimax WSDL servisi URL adresi.
            uye_kodu (str, optional): Ticimax WS yetki kodu.
        """
        self.base_url = base_url or os.getenv("TICIMAX_BASE_URL")
        self.uye_kodu = uye_kodu or os.getenv("TICIMAX_UYE_KODU")
        
        if not self.base_url or not self.uye_kodu:
            raise ValueError("TICIMAX_BASE_URL veya TICIMAX_UYE_KODU eksik. Lütfen parametreleri veya .env dosyasını kontrol edin.")
            
        try:
            self.client = Client(wsdl=self.base_url)
        except Exception as e:
            raise ConnectionError(f"WSDL yüklenirken bağlantı hatası oluştu: {str(e)}")

    def get_kategori(self, kategori_id: int = 0, dil: str = "") -> List[Any]:
        """
        Sistemdeki kategorileri çeker.
        
        Args:
            kategori_id (int): Belirli bir kategoriyi getirmek için ID, tümü için 0.
            dil (str): Hangi dilde getirileceği (boş bırakılırsa varsayılan Türkçe).
            
        Returns:
            List[Any]: Kategori objeleri içeren liste.
        """
        try:
            kategoriler = self.client.service.SelectKategori(
                UyeKodu=self.uye_kodu,
                KategoriId=kategori_id,
                Dil=dil
            )
            return kategoriler
        except Fault as fault:
            print(f"Kategori çekilirken SOAP Hatası: {fault}")
            return []

    def save_urun(self, urun_kartlari: List[Dict[str, Any]], urun_karti_ayar: Dict[str, bool], varyasyon_ayar: Dict[str, bool]) -> Any:
        """
        Yeni ürün kaydeder veya mevcut ürünleri günceller.
        
        Args:
            urun_kartlari (List[Dict[str, Any]]): Eklenecek/güncellenecek ürün dataları (UrunKarti objeleri).
            urun_karti_ayar (Dict[str, bool]): Ürün kartı güncellenecek alanların ayarları.
            varyasyon_ayar (Dict[str, bool]): Varyasyon güncellenecek alanların ayarları.
            
        Returns:
            Any: SOAP servis tarafındaki işlem sonucu (örn. WebServisResponse).
        """
        try:
            response = self.client.service.SaveUrun(
                UyeKodu=self.uye_kodu,
                UrunKartlari={'UrunKarti': urun_kartlari},
                UrunKartiAyar=urun_karti_ayar,
                VaryasyonAyar=varyasyon_ayar
            )
            return response
        except Fault as fault:
            print(f"Ürün kaydedilirken SOAP Hatası: {fault}")
            return None

    def get_urun_count(self, filter_options: Dict[str, Any]) -> int:
        """
        Belirlenen filtrelere uyan ürün sayısını getirir.
        
        Args:
            filter_options (Dict[str, Any]): Ürünleri filtrelemek için seçenekler.
            
        Returns:
            int: Filtrelere uyan ürün sayısı toplamı.
        """
        try:
            count = self.client.service.SelectUrunCount(
                UyeKodu=self.uye_kodu,
                Filtre=filter_options
            )
            return count
        except Fault as fault:
            print(f"Ürün sayısı çekilirken SOAP Hatası: {fault}")
            return 0

    def get_urun_liste(self, urun_karti_id: int = 0, sayfa_boyutu: int = 100) -> List[Any]:
        """
        Urun listesini getirir. 
        Tum urunleri (aktif + pasif) otomatik sayfalama ile cekmek icin 
        sayfa sayfa dongu yapar ve sonuclari birlestirir.
        
        Args:
            urun_karti_id (int): Belirli bir urun cekilecekse ID verilir. 0 ise tum urunler cekilir.
            sayfa_boyutu (int): Her sayfada cekilecek urun sayisi (varsayilan 100).
            
        Returns:
            List[Any]: Urun objeleri liste olarak doner.
        """
        tum_urunler = []
        
        # Aktif (1) ve Pasif (0) urunleri ayri ayri cek ve birlestir
        for aktif_durum in [1, 0]:
            baslangic = 0
            while True:
                try:
                    filtre = {'Aktif': aktif_durum}
                    if urun_karti_id > 0:
                        filtre['UrunKartiID'] = urun_karti_id
                    
                    sayfalama = {
                        'BaslangicIndex': baslangic,
                        'KayitSayisi': sayfa_boyutu,
                        'KayitSayisinaGoreGetir': True,
                        'SiralamaDegeri': 'id',
                        'SiralamaYonu': 'Asc'
                    }
                    
                    response = self.client.service.SelectUrun(
                        UyeKodu=self.uye_kodu,
                        f=filtre,
                        s=sayfalama
                    )
                    
                    if response is None:
                        break
                    
                    sayfa_urunler = []
                    if hasattr(response, 'Urunler'):
                        sayfa_urunler = response.Urunler or []
                    elif hasattr(response, 'UrunKarti'):
                        sayfa_urunler = response.UrunKarti or []
                    elif isinstance(response, list):
                        sayfa_urunler = response
                    else:
                        sayfa_urunler = [response]
                    
                    if not sayfa_urunler:
                        break
                        
                    tum_urunler.extend(sayfa_urunler)
                    
                    if len(sayfa_urunler) < sayfa_boyutu:
                        break
                        
                    baslangic += sayfa_boyutu
                    
                except Fault as fault:
                    print(f"Urun listesi cekilirken SOAP Hatasi (Aktif={aktif_durum}, sayfa {baslangic}): {fault}")
                    break
        
        return tum_urunler
