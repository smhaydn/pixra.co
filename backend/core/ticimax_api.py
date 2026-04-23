import os
from typing import Dict, Any, List, Optional
from zeep import Client
from zeep.exceptions import Fault
from zeep.plugins import HistoryPlugin
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
            self._history = HistoryPlugin()
            self.client = Client(wsdl=self.base_url, plugins=[self._history])
        except Exception as e:
            raise ConnectionError(f"WSDL yüklenirken bağlantı hatası oluştu: {str(e)}")

    def get_urunkartiayar_fields(self) -> List[str]:
        """WSDL'den UrunKartiAyar tipinin alan adlarini doner (debug icin)."""
        try:
            t = self.client.get_type('ns2:UrunKartiAyar')
            elements = t._type.elements  # zeep internal
            return [e[0] for e in elements]
        except Exception:
            try:
                # Alternatif yol
                t = self.client.get_type('ns2:UrunKartiAyar')
                return list(t._type.elements_by_name.keys())
            except Exception as e:
                return [f"HATA: {e}"]

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

    def _build_resimler_with_alt_tags(self, factory, raw_resimler, alt_tags: List[str]):
        """
        Mevcut Resimler objesine alt_tags uygular.
        Ticimax WSDL'de UrunKarti.Resimler = ArrayOfResim (Resim objeleri).
        Her Resim objesinin ResimAdi alani alt tag olarak kullanilir.

        Args:
            factory: zeep type_factory('ns2')
            raw_resimler: SelectUrun'dan gelen Resimler objesi (ArrayOfResim)
            alt_tags: Gorsel sirasina gore alt text listesi ["alt1", "alt2", ...]
        Returns:
            Guncellenmis ArrayOfResim objesi (veya orijinal)
        """
        if not alt_tags or not raw_resimler:
            return raw_resimler

        # ArrayOfResim formati: raw_resimler.Resim listesi
        resim_listesi = None
        if hasattr(raw_resimler, 'Resim') and raw_resimler.Resim:
            resim_listesi = raw_resimler.Resim
        elif isinstance(raw_resimler, list):
            resim_listesi = raw_resimler

        if resim_listesi:
            try:
                yeni_resimler = []
                for i, r in enumerate(resim_listesi):
                    alt = alt_tags[i] if i < len(alt_tags) else (alt_tags[0] if alt_tags else "")
                    try:
                        yeni_r = factory.Resim(
                            ID=getattr(r, 'ID', 0),
                            ResimAdi=alt[:125],          # Alt tag = ResimAdi
                            Aktif=getattr(r, 'Aktif', True),
                            Sira=getattr(r, 'Sira', i),
                            UrunID=getattr(r, 'UrunID', 0),
                            UrunKartiID=getattr(r, 'UrunKartiID', 0),
                        )
                        yeni_resimler.append(yeni_r)
                        print(f"[ALT_TAG] Resim {i+1} ResimAdi: '{alt[:60]}'")
                    except Exception as e:
                        print(f"[ALT_TAG] Resim olusturma hatasi (index {i}): {e}")
                        yeni_resimler.append(r)  # Hata olursa orijinali kullan

                if yeni_resimler:
                    try:
                        return factory.ArrayOfResim(Resim=yeni_resimler)
                    except Exception as e:
                        print(f"[ALT_TAG] ArrayOfResim sarmalama hatasi: {e}")
                        return raw_resimler
            except Exception as e:
                print(f"[ALT_TAG] Resim guncelleme genel hatasi: {e}")
        else:
            print(f"[ALT_TAG] UYARI: Resimler formatı tanımlanamadı "
                  f"(tip={type(raw_resimler)}) — alt tag gönderilemez")

        return raw_resimler

    def get_urunresim_fields(self) -> List[str]:
        """WSDL'den UrunResim tipinin alan adlarini doner (debug icin)."""
        try:
            t = self.client.get_type('ns2:UrunResim')
            elements = t._type.elements
            return [e[0] for e in elements]
        except Exception:
            try:
                t = self.client.get_type('ns2:UrunResim')
                return list(t._type.elements_by_name.keys())
            except Exception as e:
                return [f"HATA: {e}"]

    def save_urun(self, raw_urun, updates: Dict[str, Any], update_flags: Dict[str, bool],
                  alt_tags: Optional[List[str]] = None) -> Any:
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
            alt_tags: Gorsel sirasina gore alt text listesi ["alt1", "alt2", ...]

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

            # ── UrunKarti olustur — zorunlu alanlar raw'dan ───────────────────
            # StokKodu dahil edilmeli; yoksa None donebilir
            raw_stok = getattr(raw_urun, 'StokKodu', None) or ''

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

            # Resimler: DOKUNMA — SaveUrun ile gorsel guncelleme gorsel duplikasyonuna
            # yol aciyor. Alt tag icin ayri bir API endpoint gerekiyor.
            urun.Resimler = raw_urun.Resimler

            urun.Varyasyonlar = factory.ArrayOfVaryasyon(Varyasyon=varyasyon_objeleri)
            urun.Etiketler = raw_urun.Etiketler if raw_urun.Etiketler else []

            # AI guncellemelerini uzerine yaz
            for field, value in updates.items():
                if hasattr(urun, field):
                    setattr(urun, field, value)

            print(f"[SAVE_URUN] ID={raw_urun.ID}, StokKodu='{raw_stok}', "
                  f"guncellenen_alanlar={list(updates.keys())}")

            # ArrayOfUrunKarti wrapper — zeep bunu gerektirir
            arr = factory.ArrayOfUrunKarti(UrunKarti=[urun])

            # UrunKartiAyar — flag isimleri WSDL'den dogrulanmis, dogrudan kullan
            # (dinamik filtreleme kaldirildi — introspection API'si calismiyor,
            #  flag isimleri zaten xsd2 schemasi ile dogrulanmistir)
            print(f"[SAVE_URUN] UrunKartiAyar flags: "
                  f"{[k for k,v in update_flags.items() if v]}")
            uk_ayar_obj = factory.UrunKartiAyar(**update_flags)

            # VaryasyonAyar — hicbir varyasyon alani guncellenmez
            v_ayar_obj = factory.VaryasyonAyar()

            response = self.client.service.SaveUrun(
                UyeKodu=self.uye_kodu,
                urunKartlari=arr,
                ukAyar=uk_ayar_obj,
                vAyar=v_ayar_obj
            )

            # ── Gonderilen/alinan SOAP XML'i logla ───────────────────────────
            try:
                from lxml import etree
                if self._history.last_sent:
                    sent_xml = etree.tostring(
                        self._history.last_sent["envelope"], pretty_print=True
                    ).decode()
                    # Sadece ilk 3000 karakteri log'la (Railway limit)
                    print(f"[SOAP SENT]\n{sent_xml[:3000]}")
                if self._history.last_received:
                    recv_xml = etree.tostring(
                        self._history.last_received["envelope"], pretty_print=True
                    ).decode()
                    print(f"[SOAP RECV]\n{recv_xml[:3000]}")
            except Exception as log_err:
                print(f"[SOAP LOG] XML log hatasi: {log_err}")

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
