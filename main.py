import os
import requests
import pandas as pd
from ticimax_api import TicimaxClient
from vision_engine import VisionEngine

def download_image(url: str, save_path: str) -> bool:
    """Belirtilen URL'den görseli indirir."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return True
    except Exception as e:
        print(f"Görsel indirilemedi ({url}): {e}")
        return False

def get_field(obj, field_name: str, default=""):
    """
    Zeep/SOAP objesi içinde hem attribute hem de dict key arar.
    Ticimax API si bazen obj bazen de dictionary döndürebilmektedir.
    """
    if hasattr(obj, field_name):
        val = getattr(obj, field_name)
        return val if val is not None else default
    elif isinstance(obj, dict):
        return obj.get(field_name, default)
    return default

def main():
    print("Ticimax Bağlantısı Kuruluyor...")
    ticimax = TicimaxClient()
    
    print("Vision Engine Başlatılıyor...")
    engine = VisionEngine()

    print("Ürün Listesi Çekiliyor... (Lütfen bekleyin)")
    # Güvenlik ve test amaçlı şimdilik ilk 5 ürünü işleyecek şekilde kurgulu. 
    # Sistemin yoğunluğunu artırmamak adına bu test aşamasında 5 ürünle sınırlıyoruz.
    MAX_TEST_LIMIT = 5
    
    urunler = ticimax.get_urun_liste(urun_karti_id=0)  # 0: Tüm veriler (bazen limitli döner)
    if not urunler:
        print("Tüh! Hiç ürün bulunamadı. Servis parametrelerini kontrol edin.")
        return

    print(f"Toplam Çekilen Ürün: {len(urunler)}")
    
    data_records_review = []
    data_records_upload = []
    
    TEMPLATE_COLS = ['URUNKARTIID', 'URUNID', 'STOKKODU', 'VARYASYONKODU', 'BARKOD', 'URUNADI', 'ONYAZI', 'ACIKLAMA', 'PUANDEGER', 'PUANYUZDE', 'MARKA', 'TEDARIKCI', 'MAKSTAKSITSAYISI', 'BREADCRUMBKAT', 'KATEGORILER', 'SATISBIRIMI', 'VITRIN', 'YENIURUN', 'FIRSATURUNU', 'FBSTOREGOSTER', 'SEO_SAYFABASLIK', 'SEO_ANAHTARKELIME', 'SEO_SAYFAACIKLAMA', 'UCRETSIZKARGO', 'STOKADEDI', 'ALISFIYATI', 'SATISFIYATI', 'INDIRIMLIFIYAT', 'UYETIPIFIYAT1', 'UYETIPIFIYAT2', 'UYETIPIFIYAT3', 'UYETIPIFIYAT4', 'UYETIPIFIYAT5', 'KDVORANI', 'KDVDAHIL', 'PARABIRIMI', 'KUR', 'KARGOAGIRLIGI', 'KARGOAGIRLIGIYURTDISI', 'URUNGENISLIK', 'URUNDERINLIK', 'URUNYUKSEKLIK', 'URUNAGIRLIGI', 'KARGOUCRETI', 'URUNAKTIF', 'VARYASYON', 'TAHMINITESLIMSURESIGOSTER', 'URUNADEDIMINIMUMDEGER', 'URUNADEDIVARSAYILANDEGER', 'URUNADEDIARTISKADEMESI', 'GTIPKODU', 'OZELALAN1', 'OZELALAN2', 'OZELALAN3', 'OZELALAN4', 'OZELALAN5', 'VERGIISTISNAKODU', 'YEMEKKARTIODEMEYASAKLILISTESI', 'MOBILBEDENTABLOSUAKTIF', 'MOBILBEDENTABLOSUICERIK', 'PAZARYERIAKTIFLISTESI']
    
    
    # Geçici resim dosyası için yol
    temp_img_path = "temp_img.jpg"

    count = 0
    for urun in urunler:
        if count >= MAX_TEST_LIMIT:
            break
            
        # 1. Mevcut Verileri Ticimax response üzerinden ayıkla
        urun_id = get_field(urun, 'ID') or get_field(urun, 'UrunKartiID') or str(count+1)
        stok_kodu = get_field(urun, 'StokKodu')
        
        # Resim URL çıkartma işlemi
        resim_url = get_field(urun, 'ResimURL')
        if not resim_url:
            resimler = get_field(urun, 'Resimler')
            if resimler:
                string_list = get_field(resimler, 'string')
                if string_list and isinstance(string_list, list) and len(string_list) > 0:
                    resim_url = string_list[0]
                    
        marka = get_field(urun, 'Marka', 'Bilinmeyen Marka')
        
        # Ürün Bilgileri
        urunadi = get_field(urun, 'UrunAdi') or get_field(urun, 'Tanim')
        onyazi = get_field(urun, 'Onyazi') or get_field(urun, 'OnYazi')
        aciklama = get_field(urun, 'Aciklama')
        anahtar_kelime = get_field(urun, 'AnahtarKelime')
        
        # SEO Verileri
        seo_sayfabaslik = get_field(urun, 'SeoSayfaBaslik')
        seo_anahtarkelime = get_field(urun, 'SeoAnahtarKelime')
        seo_sayfaaciklama = get_field(urun, 'SeoSayfaAciklama')
        
        # Reklam & Kategori
        adwords_aciklama = get_field(urun, 'AdwordsAciklama')
        adwords_kategori = get_field(urun, 'AdwordsKategori')
        adwords_tip = get_field(urun, 'AdwordsTip')
        breadcrumb_kat = get_field(urun, 'BreadcrumbKat') # veya benzeri field
        
        print(f"\n--- İşleniyor: {urun_id} | {urunadi} ---")
        
        # Resim İndirme
        if not resim_url:
            print("Görsel URL bulunamadı, bu ürün atlanıyor.")
            continue
            
        # Eğer link HTTP/HTTPS ile başlamıyorsa tam link haline getirebilirsiniz.
        if not resim_url.startswith("http"):
            # Varsayılan protokolü ekle
            resim_url = f"https://www.lolaofshine.com{resim_url}"
            
        if not download_image(resim_url, temp_img_path):
            continue
        
        # 2. Vision Engine (Yapay Zeka Analizi)
        try:
            print("  [AI] Gemini Gorseli ve SEO/Adwords Ciktilarini Yorumluyor...")
            ai_result = engine.analyze_product_image(
                image_path=temp_img_path,
                marka=marka,
                adwords_aciklama=adwords_aciklama,
                adwords_kategori=adwords_kategori,
                adwords_tip=adwords_tip,
                breadcrumb_kat=breadcrumb_kat,
                mevcut_urun_adi=urunadi,
                satisfiyati=str(get_field(urun, 'SatisFiyati', '')),
                kategoriler=str(get_field(urun, 'Kategoriler', '')),
                stok_kodu=str(stok_kodu),
            )
            
            # SSS array'ini HTML olarak açıklamaya göm:
            ai_aciklama_full = f"{ai_result.aciklama}<br/><br/><h3>Sıkça Sorulan Sorular</h3>"
            for q_dict in ai_result.geo_sss:
                q = q_dict.get('soru', '')
                a = q_dict.get('cevap', '')
                ai_aciklama_full += f"<p><strong>{q}</strong><br/>{a}</p>"
                
            # 3. Excel Kaydı için Objeyi Hazırla (İnceleme Raporu)
            row_review = {
                "ÜrünID": urun_id,
                "StokKodu": stok_kodu,
                "ResimURL": resim_url,
                "Marka": marka,
                "BREADCRUMBKAT": breadcrumb_kat,
                
                "MEVCUT URUNADI": urunadi,
                "AI URUNADI": ai_result.urun_adi,
                
                "MEVCUT ONYAZI": onyazi,
                "AI ONYAZI": ai_result.onyazi,
                
                "MEVCUT ACIKLAMA": aciklama,
                "AI ACIKLAMA (GEO SSS)": ai_aciklama_full,
                
                "MEVCUT SEO_SAYFABASLIK": seo_sayfabaslik,
                "AI SEO_SAYFABASLIK": ai_result.seo_baslik,
                
                "MEVCUT SEO_SAYFAACIKLAMA": seo_sayfaaciklama,
                "AI SEO_SAYFAACIKLAMA": ai_result.seo_aciklama,
                
                "MEVCUT SEO_ANAHTARKELIME": seo_anahtarkelime,
                "AI SEO_ANAHTARKELIME": ai_result.seo_anahtarkelime,
                
                "MEVCUT ANAHTARKELIME": anahtar_kelime,
                "AI ANAHTARKELIME": ai_result.anahtar_kelime,

                "AI ODAK KELIME": getattr(ai_result, 'hedef_anahtar_kelime', ''),
                "AI GORSEL ALT TEXT": getattr(ai_result, 'gorsel_alt_text', ''),
                "AI GEO OZET": getattr(ai_result, 'geo_ozet', ''),
                "AI KULLANIM ALANLARI": getattr(ai_result, 'kullanim_alanlari', ''),
                "AI NEDEN BU URUN": getattr(ai_result, 'neden_bu_urun', ''),
                "AI LONG-TAIL SORGULAR": ', '.join(getattr(ai_result, 'uzun_kuyruk_sorgular', [])),
            }
            data_records_review.append(row_review)
            
            # 4. Ticimax Yükleme Şablonu (Upload Ready)
            row_upload = {}
            for col in TEMPLATE_COLS:
                # Orijinal verileri Zeep/Dictionary den çekiyoruz:
                # Kolon isimleri genellikle PascalCase formatındadır
                val = get_field(urun, col) 
                
                # Sadece ilgili özellikleri AI verileriyle eziyoruz!
                if col.upper() == 'URUNADI':
                    val = ai_result.urun_adi
                elif col.upper() == 'ONYAZI':
                    val = ai_result.onyazi
                elif col.upper() == 'ACIKLAMA':
                    val = ai_aciklama_full
                elif col.upper() == 'SEO_SAYFABASLIK':
                    val = ai_result.seo_baslik
                elif col.upper() == 'SEO_SAYFAACIKLAMA':
                    val = ai_result.seo_aciklama
                elif col.upper() == 'SEO_ANAHTARKELIME':
                    val = ai_result.seo_anahtarkelime
                elif col.upper() == 'ANAHTARKELIME':
                    val = ai_result.anahtar_kelime
                elif col.upper() == 'URUNKARTIID':
                    val = urun_id
                    
                row_upload[col] = val if val is not None else ""
                
            data_records_upload.append(row_upload)
            print("  [OK] Analiz Basarili!")
            count += 1
            
        except Exception as e:
            print(f"  [ERROR] AI Analizi Basarisiz: {e}")
            
    # Temizlik yap
    if os.path.exists(temp_img_path):
        os.remove(temp_img_path)

    # 5. Pandas ile Excel Çıktısı Al (İki Sekmeli)
    if data_records_review:
        with pd.ExcelWriter("ticimax_seo_dokumu.xlsx", engine="openpyxl") as writer:
            df_review = pd.DataFrame(data_records_review)
            df_review.to_excel(writer, sheet_name="Inceleme_Kiyaslama", index=False)
            
            df_upload = pd.DataFrame(data_records_upload)
            df_upload.to_excel(writer, sheet_name="Ticimax_Hazir_Yukleme", index=False)
            
        print(f"\nİşlem Tamam! {len(data_records_review)} adet ürün ticimax_seo_dokumu.xlsx dosyasına (2 sekme halinde) kaydedildi.")
    else:
        print("\nİşlenebilecek ürün analiz edilemediği için tablo oluşturulmadı.")

if __name__ == "__main__":
    main()
