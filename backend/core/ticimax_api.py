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

    def save_urun(self, raw_urun, updates: Dict[str, Any], update_flags: Dict[str, bool]) -> Any:
        """
        Mevcut urunu gunceller. Raw SelectUrun objesinden yeni UrunKarti olusturur,
        updates'teki alanlari uzerine yazar ve update_flags'e gore gunceller.

        ONEMLI zeep kurallari:
        - ArrayOfUrunKarti wrapper kullanilmali (duz liste serialize edilmez)
        - ArrayOfVaryasyon wrapper kullanilmali
        - Tum UrunKartiAyar alanlari acikca set edilmeli

        Args:
            raw_urun: SelectUrun'dan gelen zeep UrunKarti objesi
            updates: Degistirilecek alanlar (orn: {"SeoSayfaBaslik": "Yeni Baslik"})
            update_flags: UrunKartiAyar icin True olan alanlar (orn: {"SeoSayfaBaslikGuncelle": True})

        Returns:
            SaveUrunResponse objesi (SaveUrunResult=0 basarili demek)
        """
        try:
            factory = self.client.type_factory('ns2')

            # Varyasyonlari factory Varyasyon objeleri olarak olustur
            varys_src = []
            if raw_urun.Varyasyonlar and hasattr(raw_urun.Varyasyonlar, 'Varyasyon'):
                varys_src = raw_urun.Varyasyonlar.Varyasyon or []

            varyasyon_objeleri = []
            for v in varys_src:
                mv = factory.Varyasyon(
                    ID=v.ID,
                    SatisFiyati=v.SatisFiyati,
                    ParaBirimiID=v.ParaBirimiID,
                    Aktif=v.Aktif,
                    StokKodu=v.StokKodu or '',
                    StokAdedi=v.StokAdedi or 0,
                    Barkod=v.Barkod or '',
                )
                mv.Ozellikler = v.Ozellikler if v.Ozellikler else []
                mv.Resimler = v.Resimler if v.Resimler else []
                varyasyon_objeleri.append(mv)

            # UrunKarti olustur — zorunlu alanlar raw'dan
            urun = factory.UrunKarti(
                ID=raw_urun.ID,
                Aktif=raw_urun.Aktif,
                UrunAdi=raw_urun.UrunAdi or '',
                Aciklama=raw_urun.Aciklama or '',
                AnaKategori=raw_urun.AnaKategori or '',
                AnaKategoriID=raw_urun.AnaKategoriID or 0,
                MarkaID=raw_urun.MarkaID or 0,
                TedarikciID=raw_urun.TedarikciID or 0,
                SatisBirimi=raw_urun.SatisBirimi or 'Adet',
                UcretsizKargo=raw_urun.UcretsizKargo or False,
                OnYazi=raw_urun.OnYazi or '',
                SeoSayfaBaslik=raw_urun.SeoSayfaBaslik or '',
                SeoSayfaAciklama=raw_urun.SeoSayfaAciklama or '',
                SeoAnahtarKelime=raw_urun.SeoAnahtarKelime or '',
                AdwordsAciklama=raw_urun.AdwordsAciklama or '',
                AdwordsKategori=raw_urun.AdwordsKategori or '',
                AdwordsTip=raw_urun.AdwordsTip or '',
            )

            # Array alanlari raw'dan koru (zeep tipleriyle)
            urun.Kategoriler = raw_urun.Kategoriler
            urun.Resimler = raw_urun.Resimler
            urun.Varyasyonlar = factory.ArrayOfVaryasyon(Varyasyon=varyasyon_objeleri)
            urun.Etiketler = raw_urun.Etiketler if raw_urun.Etiketler else []

            # AI guncellemelerini uzerine yaz
            for field, value in updates.items():
                if hasattr(urun, field):
                    setattr(urun, field, value)

            # ArrayOfUrunKarti wrapper — zeep bunu gerektirir
            arr = factory.ArrayOfUrunKarti(UrunKarti=[urun])

            # UrunKartiAyar — tum alanlari acikca set et
            uk_ayar_obj = factory.UrunKartiAyar(**update_flags)

            # VaryasyonAyar — hicbir varyasyon alani guncellenmez
            v_ayar_obj = factory.VaryasyonAyar()

            response = self.client.service.SaveUrun(
                UyeKodu=self.uye_kodu,
                urunKartlari=arr,
                ukAyar=uk_ayar_obj,
                vAyar=v_ayar_obj
            )
            return response
        except Fault as fault:
            raise RuntimeError(f"SOAP Hatasi: {fault}")
        except Exception as e:
            raise RuntimeError(f"SaveUrun hatasi: {str(e)}")

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
