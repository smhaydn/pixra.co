from ticimax_api import TicimaxClient
from zeep.helpers import serialize_object
from pprint import pprint

client = TicimaxClient()
urunler = client.get_urun_liste(urun_karti_id=0)

if urunler:
    first_urun = serialize_object(urunler[0])
    with open('debug_out.txt', 'w', encoding='utf-8') as f:
        pprint(first_urun, stream=f)
else:
    print("Ürün bulunamadı.")
