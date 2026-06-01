"""Learning memory: apply + record corrections (local/no-GitHub mode)."""
from core import ogrenme
from core.schema import Kalem


def _k(koy, malz, birim=None):
    return Kalem(koy=koy, malzeme_adi=malz, miktar=1, olcu_birimi=birim,
                 guven_koy=1.0, guven_malzeme=1.0, guven_miktar=1.0)


def test_bos_ekle_ve_uygula():
    data = {"koy": {}, "malzeme": {}, "birim": {}}
    assert ogrenme.ekle(data, "koy", "Duadulu", "Merkez Durdulu") is True
    assert ogrenme.ekle(data, "malzeme", "Emiş Çekvalf", "Emiş Çekvalfi") is True
    assert ogrenme.ekle(data, "birim", "kgr", "Kg") is True

    kalemler = [_k("Duadulu", "Emiş Çekvalf", "kgr")]
    ogrenme.uygula(kalemler, data)
    assert kalemler[0].koy == "Merkez Durdulu"
    assert kalemler[0].malzeme_adi == "Emiş Çekvalfi"
    assert kalemler[0].olcu_birimi == "Kg"


def test_ekle_degisiklik_yoksa_false():
    data = {"koy": {}, "malzeme": {}, "birim": {}}
    # same canonical value -> nothing to learn
    assert ogrenme.ekle(data, "koy", "Merkez Durdulu", "merkez durdulu") is False
    assert ogrenme.ekle(data, "koy", "", "X") is False
    assert ogrenme.ekle(data, "koy", "X", "") is False
    # idempotent
    assert ogrenme.ekle(data, "koy", "Duadulu", "Merkez Durdulu") is True
    assert ogrenme.ekle(data, "koy", "Duadulu", "Merkez Durdulu") is False


def test_uygula_canonical_eslesme():
    # learned key is canonical, so case/space variants still match
    data = {"koy": {ogrenme.kanonik("Duadulu"): "Merkez Durdulu"}, "malzeme": {}, "birim": {}}
    kalemler = [_k("DUADULU", "X")]
    ogrenme.uygula(kalemler, data)
    assert kalemler[0].koy == "Merkez Durdulu"


def test_yukle_kaydet_yerel(tmp_path, monkeypatch):
    import config
    monkeypatch.setattr(config, "GITHUB_TOKEN", None)
    monkeypatch.setattr(config, "OGRENME_LOCAL", tmp_path / "ogrenme.json")
    data, sha = ogrenme.yukle()
    assert sha is None and data == {"koy": {}, "malzeme": {}, "birim": {}}
    ogrenme.ekle(data, "koy", "Duadulu", "Merkez Durdulu")
    ogrenme.kaydet(data, None)
    tekrar, _ = ogrenme.yukle()
    assert tekrar["koy"][ogrenme.kanonik("Duadulu")] == "Merkez Durdulu"
