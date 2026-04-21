import pandas as pd

df = pd.read_excel('12ticimax_seo_dokumu.xlsx', sheet_name='Worksheet')

for i, row in df.iterrows():
    print("=" * 60)
    print(f"URUN {i+1}")
    print("=" * 60)
    print(f"URUNKARTIID: {row.get('URUNKARTIID', '')}")
    print(f"URUNID: {row.get('URUNID', '')}")
    print(f"STOKKODU: {row.get('STOKKODU', '')}")
    print(f"URUNADI: {row.get('URUNADI', '')}")
    print(f"MARKA: {row.get('MARKA', '')}")

    # SEO kontrolleri
    seo_baslik = str(row.get('SEO_SAYFABASLIK', '') or '')
    seo_aciklama = str(row.get('SEO_SAYFAACIKLAMA', '') or '')
    seo_anahtar = str(row.get('SEO_ANAHTARKELIME', '') or '')

    baslik_ok = 'OK' if len(seo_baslik) <= 60 else 'LIMIT ASILDI!'
    aciklama_ok = 'OK' if len(seo_aciklama) <= 155 else 'LIMIT ASILDI!'

    print(f"\nSEO_SAYFABASLIK ({len(seo_baslik)}/60 kar): {seo_baslik}")
    print(f"  -> {baslik_ok}")
    print(f"SEO_SAYFAACIKLAMA ({len(seo_aciklama)}/155 kar): {seo_aciklama}")
    print(f"  -> {aciklama_ok}")
    print(f"SEO_ANAHTARKELIME: {seo_anahtar[:100]}")

    # Onyazi
    onyazi = str(row.get('ONYAZI', '') or '')
    print(f"ONYAZI: {onyazi[:150]}")

    # Aciklama HTML kontrol
    aciklama = str(row.get('ACIKLAMA', '') or '')
    has_geo = 'geo-ozet' in aciklama
    has_tablo = '<table' in aciklama
    has_faq = 'Question' in aciklama
    has_jsonld = 'application/ld+json' in aciklama
    print(f"\nACIKLAMA HTML Kontrol:")
    print(f"  GEO Ozet blogu: {'VAR' if has_geo else 'YOK'}")
    print(f"  Teknik Ozellikler tablosu: {'VAR' if has_tablo else 'YOK'}")
    print(f"  Schema.org FAQ microdata: {'VAR' if has_faq else 'YOK'}")
    print(f"  JSON-LD FAQ Schema: {'VAR' if has_jsonld else 'YOK'}")
    print(f"  Toplam HTML uzunlugu: {len(aciklama)} karakter")

    # Diger onemli alanlar
    print(f"\nSATISFIYATI: {row.get('SATISFIYATI', '')}")
    print(f"STOKADEDI: {row.get('STOKADEDI', '')}")
    print(f"KDVORANI: {row.get('KDVORANI', '')}")
    kat = str(row.get('KATEGORILER', '') or '')
    print(f"KATEGORILER: {kat[:80]}")
    print(f"BREADCRUMBKAT: {row.get('BREADCRUMBKAT', '')}")
    print(f"URUNAKTIF: {row.get('URUNAKTIF', '')}")
    
    # Bos kolon kontrolu
    bos = []
    for col in df.columns:
        val = str(row.get(col, '') or '').strip()
        if val == '' or val == 'nan':
            bos.append(col)
    print(f"\nBOS KOLONLAR ({len(bos)}): {', '.join(bos)}")
    print()
