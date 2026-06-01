import pytest
from pydantic import ValidationError

from core.schema import Kalem, Tutanak


def test_kalem_temel():
    k = Kalem(koy="Gaziköy", malzeme_adi="Dalgıç Pompa", miktar=2,
              guven_koy=0.9, guven_malzeme=0.8, guven_miktar=0.95)
    assert k.olcu_birimi is None and k.kodu is None
    assert k.miktar == 2


def test_guven_sinir_disi():
    with pytest.raises(ValidationError):
        Kalem(koy="X", malzeme_adi="Y", miktar=1,
              guven_koy=1.5, guven_malzeme=0.5, guven_miktar=0.5)
    with pytest.raises(ValidationError):
        Kalem(koy="X", malzeme_adi="Y", miktar=1,
              guven_koy=0.5, guven_malzeme=-0.1, guven_miktar=0.5)


def test_tutanak_bos():
    assert Tutanak().kalemler == []


def test_tutanak_validate():
    t = Tutanak.model_validate({"kalemler": [
        {"koy": "A", "malzeme_adi": "M", "miktar": 1,
         "guven_koy": 1, "guven_malzeme": 1, "guven_miktar": 1}
    ]})
    assert len(t.kalemler) == 1
