"""Kayip ve calisan urunlerin KARTAKTIF/URUNAKTIF degerlerini karsilastir."""
import pandas as pd

df = pd.read_excel("lolaurun.xls")
missing = [156, 162, 163, 164, 183, 184, 185]

print("=== KAYIP URUNLER (API'den gelmeyen) ===")
for mid in missing:
    rows = df[df["URUNKARTIID"] == mid]
    for _, r in rows.iterrows():
        print(
            f"KartiID={mid} | UrunID={r['URUNID']} | "
            f"KARTAKTIF={r['KARTAKTIF']} | URUNAKTIF={r['URUNAKTIF']} | "
            f"StokKodu={r['STOKKODU']} | Varyasyon={r['VARYASYONKODU']}"
        )

print()
print("=== CALISAN URUNLER (API'den gelen) ===")
for sid in [157, 186, 198]:
    rows = df[df["URUNKARTIID"] == sid]
    for _, r in rows.iterrows():
        print(
            f"KartiID={sid} | UrunID={r['URUNID']} | "
            f"KARTAKTIF={r['KARTAKTIF']} | URUNAKTIF={r['URUNAKTIF']} | "
            f"StokKodu={r['STOKKODU']} | Varyasyon={r['VARYASYONKODU']}"
        )
        break  # sadece ilk satir
