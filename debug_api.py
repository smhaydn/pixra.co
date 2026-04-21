"""Ticimax API debug — kac urun donuyor, filtre detaylari."""
from ticimax_api import TicimaxClient
from dotenv import load_dotenv
import os

load_dotenv()

client = TicimaxClient()

# Filtre olmadan dene (tum urunler)
filtre_bos = {}

# Sayfalama
sayfalama = {
    'BaslangicIndex': 0,
    'KayitSayisi': 100,
    'KayitSayisinaGoreGetir': True,
    'SiralamaDegeri': 'id',
    'SiralamaYonu': 'Asc'
}

print("=== SAYFA 1 (0-100) ===")
response = client.client.service.SelectUrun(
    UyeKodu=client.uye_kodu,
    f=filtre_bos,
    s=sayfalama
)

if response is not None:
    if isinstance(response, list):
        urunler = response
    elif hasattr(response, '__iter__'):
        urunler = list(response)
    else:
        urunler = [response]
    print(f"Gelen urun sayisi: {len(urunler)}")
    for i, u in enumerate(urunler):
        urun_id = getattr(u, 'ID', None) or getattr(u, 'UrunKartiID', None)
        adi = getattr(u, 'UrunAdi', None) or getattr(u, 'Tanim', None)
        aktif = getattr(u, 'Aktif', 'bilgi yok')
        print(f"  {i+1}. ID={urun_id} | Aktif={aktif} | {adi}")
else:
    print("Response None dondu!")

# Sayfa 2 dene
print("\n=== SAYFA 2 (100-200) ===")
sayfalama2 = {
    'BaslangicIndex': 100,
    'KayitSayisi': 100,
    'KayitSayisinaGoreGetir': True,
    'SiralamaDegeri': 'id',
    'SiralamaYonu': 'Asc'
}
response2 = client.client.service.SelectUrun(
    UyeKodu=client.uye_kodu,
    f=filtre_bos,
    s=sayfalama2
)
if response2 is not None:
    if isinstance(response2, list):
        urunler2 = response2
    elif hasattr(response2, '__iter__'):
        urunler2 = list(response2)
    else:
        urunler2 = [response2]
    print(f"Gelen urun sayisi: {len(urunler2)}")
else:
    print("Response None dondu!")

# SelectUrunCount dene
print("\n=== SelectUrunCount ===")
try:
    count = client.client.service.SelectUrunCount(
        UyeKodu=client.uye_kodu,
        Filtre=filtre_bos
    )
    print(f"Toplam urun sayisi (Count): {count}")
except Exception as e:
    print(f"Count hatasi: {e}")
