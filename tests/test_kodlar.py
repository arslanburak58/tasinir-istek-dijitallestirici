from core import kodlar


def test_farkli_kodlar_varsayilani_ve_boslari_eler():
    v = "150.11.02.02.01."
    assert kodlar.farkli_kodlar([v, None, "", " opt-550 ", float("nan"), "opt-550"], v) == ["opt-550"]


def test_kod_sec_soruya_verilen_cevabi_uygular():
    v = "150.11.02.02.01."
    assert kodlar.kod_sec("opt-550", {}, v) == v                     # varsayılan: fotoğraftaki yazılmaz
    assert kodlar.kod_sec("opt-550", {"opt-550": "opt-550"}, v) == "opt-550"
    assert kodlar.kod_sec("opt-550", {"opt-550": "999"}, v) == "999"
    assert kodlar.kod_sec(None, {}, "888") == "888"
    assert kodlar.kod_sec(float("nan"), {}, v) == v
