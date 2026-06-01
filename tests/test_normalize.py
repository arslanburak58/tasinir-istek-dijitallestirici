from core import normalize
from core.normalize import kanonik, turkish_lower, birim_normalize, topla
from core.schema import Kalem


def _k(koy, malz, mik, birim=None, gk=1.0):
    return Kalem(koy=koy, malzeme_adi=malz, miktar=mik, olcu_birimi=birim,
                 guven_koy=gk, guven_malzeme=1.0, guven_miktar=1.0)


def test_turkish_lower():
    assert turkish_lower("İSTANBUL") == "istanbul"
    assert turkish_lower("IŞIK") == "ışık"


def test_kanonik_varyantlar_birlesir():
    assert kanonik("Gaziköy") == kanonik("gaziköy") == kanonik("GAZİKÖY")
    assert kanonik("  Gazi köy ") == kanonik("gazi  köy")


def test_birim_normalize_varsayilan():
    assert birim_normalize(None) == "Ad"
    assert birim_normalize("") == "Ad"
    assert birim_normalize("  Kg ") == "Kg"


def test_topla_ayni_koy_tek_sayfa():
    kalemler = [_k("Gaziköy", "Pompa", 1), _k("GAZİKÖY", "Vana", 2)]
    sayfalar = topla(kalemler)
    assert len(sayfalar) == 1
    assert len(sayfalar[0].kalemler) == 2


def test_topla_ayni_malzeme_toplanir():
    kalemler = [_k("Köy A", "Pompa", 1, "Ad"), _k("Köy A", "Pompa", 3, "Ad")]
    sayfalar = topla(kalemler, miktar_topla=True)
    assert len(sayfalar) == 1
    assert len(sayfalar[0].kalemler) == 1
    assert sayfalar[0].kalemler[0].miktar == 4


def test_topla_miktar_toplama_kapali():
    kalemler = [_k("Köy A", "Pompa", 1, "Ad"), _k("Köy A", "Pompa", 3, "Ad")]
    sayfalar = topla(kalemler, miktar_topla=False)
    assert len(sayfalar[0].kalemler) == 2


def test_koy_snap_bilinen():
    # 'gaziköy' kaynak dosyada sekme adı olarak var -> tam eşleşme
    es = normalize.koy_snap("Gaziköy")
    assert es.skor == 100.0
    assert not es.kullanici_onayi_gerek
    assert kanonik(es.onerilen) == kanonik("gaziköy")
