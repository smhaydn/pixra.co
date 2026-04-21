"""Kayip 7 urunu bulmak icin kapsamli debug scripti."""
from ticimax_api import TicimaxClient

c = TicimaxClient()
sayfa = {
    'BaslangicIndex': 0,
    'KayitSayisi': 200,
    'KayitSayisinaGoreGetir': True,
    'SiralamaDegeri': 'id',
    'SiralamaYonu': 'Asc'
}
missing = [156, 162, 163, 164, 183, 184, 185]

# 1) UrunKartiIDList ile toplu sorgu
print("=== 1) UrunKartiIDList ile toplu sorgu ===")
try:
    # Zeep type factory ile ArrayOfint olustur
    namespaces = c.client.wsdl.types.prefix_map
    print("Mevcut namespace'ler:", namespaces)
    
    # Service signature'i goster
    for service in c.client.wsdl.services.values():
        for port in service.ports.values():
            for op_name, op in port.binding._operations.items():
                if 'Urun' in op_name:
                    print(f"  Method: {op_name}")
except Exception as e:
    print(f"Hata: {e}")

# 2) Tum urun metotlarini listele
print("\n=== 2) Tum Urun servis metotlari ===")
for service in c.client.wsdl.services.values():
    for port in service.ports.values():
        for op_name in sorted(port.binding._operations.keys()):
            if 'urun' in op_name.lower() or 'Urun' in op_name:
                print(f"  {op_name}")

# 3) SelectUrunKarti veya benzeri bir metod var mi?
print("\n=== 3) SelectUrunKarti denemesi ===")
try:
    r = c.client.service.SelectUrunKarti(
        UyeKodu=c.uye_kodu,
        UrunKartiID=156
    )
    print(f"SelectUrunKarti(156): {r}")
except Exception as e:
    print(f"SelectUrunKarti yok veya hata: {e}")

# 4) UrunKartiIDList kullanarak filtrele
print("\n=== 4) UrunKartiIDList ile filtre ===")
try:
    filtre = {'UrunKartiIDList': {'int': missing}}
    r = c.client.service.SelectUrun(
        UyeKodu=c.uye_kodu,
        f=filtre,
        s=sayfa
    )
    if r:
        print(f"Bulunan: {len(r)} urun")
        for u in r:
            print(f"  ID={getattr(u, 'ID', '?')} Ad={getattr(u, 'UrunAdi', '?')}")
    else:
        print("Sonuc: None")
except Exception as e:
    print(f"Hata: {e}")

# 5) Alternatif: Her kayip ID icin UrunKartiID filtresi (Aktif kalksin)
print("\n=== 5) Her kayip ID icin tek tek (filtresiz Aktif) ===")
for mid in missing:
    try:
        r = c.client.service.SelectUrun(
            UyeKodu=c.uye_kodu,
            f={'UrunKartiID': mid},
            s=sayfa
        )
        if r:
            u = r[0] if isinstance(r, list) else r
            print(f"  ID={mid}: BULUNDU - Aktif={getattr(u, 'Aktif', '?')} Ad={getattr(u, 'UrunAdi', '?')}")
        else:
            print(f"  ID={mid}: API'den donus yok (None)")
    except Exception as e:
        print(f"  ID={mid}: HATA - {e}")

# 6) Bilinen bir ID ile kontrol (mesela ID=198)
print("\n=== 6) Bilinen aktif ID ile kontrol (198) ===")
try:
    r = c.client.service.SelectUrun(
        UyeKodu=c.uye_kodu,
        f={'UrunKartiID': 198},
        s=sayfa
    )
    if r:
        u = r[0] if isinstance(r, list) else r
        attrs = [a for a in dir(u) if not a.startswith('_')]
        print(f"  ID=198 ozellikleri: {attrs[:20]}")
        print(f"  Aktif={getattr(u, 'Aktif', '?')}")
        print(f"  UrunTipi={getattr(u, 'UrunTipi', '?')}")
        print(f"  UrunKartiID={getattr(u, 'UrunKartiID', '?')}")
    else:
        print("  198 de bulunamadi!")
except Exception as e:
    print(f"  Hata: {e}")
