"""Gorsel sayisi kontrol scripti."""
from ticimax_api import TicimaxClient

c = TicimaxClient()
s = {
    'BaslangicIndex': 0,
    'KayitSayisi': 10,
    'KayitSayisinaGoreGetir': True,
    'SiralamaDegeri': 'id',
    'SiralamaYonu': 'Asc'
}
r = c.client.service.SelectUrun(UyeKodu=c.uye_kodu, f={'Aktif': 1}, s=s)

toplam_gorsel = 0
for u in r[:10]:
    resimler = getattr(u, 'Resimler', None)
    gorsel_list = []
    if resimler:
        string_list = getattr(resimler, 'string', [])
        if string_list:
            gorsel_list = [x for x in string_list if x]
    
    count = len(gorsel_list)
    toplam_gorsel += count
    urun_adi = getattr(u, 'UrunAdi', '?')[:45]
    print(f"ID={getattr(u, 'ID', 0):>3} | {count} gorsel | {urun_adi}")

print(f"\nOrtalama gorsel/urun: {toplam_gorsel / len(r[:10]):.1f}")
