"""Village-name normalization and item aggregation (UI-independent).

Same village written differently (Turkish chars, spacing, case) must collapse
to one canonical key -> one sheet. Known names come from data/koy_listesi.csv;
rapidfuzz snaps raw names to that list, flagging low-confidence matches for the
user.
"""
import csv
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

from rapidfuzz import fuzz, process

import config
from core.schema import Kalem

# Turkish-aware case folding for the canonical key.
_UPPER_MAP = str.maketrans({"I": "ı", "İ": "i", "Ş": "ş", "Ğ": "ğ", "Ü": "ü", "Ö": "ö", "Ç": "ç"})


def turkish_lower(s: str) -> str:
    return s.translate(_UPPER_MAP).lower()


def kanonik(s: str) -> str:
    """Canonical key for grouping: case/space/diacritic-insensitive."""
    s = turkish_lower(s.strip())
    s = re.sub(r"\s+", " ", s)
    # fold diacritics so 'gaziköy' / 'gazikoy' collapse together
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = s.replace("ı", "i")
    return s.strip()


def _tr_upper_char(c: str) -> str:
    return {"i": "İ", "ı": "I"}.get(c, c.upper())


def turkish_title(s: str) -> str:
    """Title-case a (possibly ALL-CAPS) name, Turkish i/ı-aware."""
    words = re.sub(r"\s+", " ", s.strip()).split(" ")
    out = []
    for w in words:
        if not w:
            continue
        low = turkish_lower(w)
        out.append(_tr_upper_char(low[0]) + low[1:])
    return " ".join(out)


@lru_cache(maxsize=1)
def bilinen_koyler() -> list[str]:
    path = config.KOY_LISTESI_PATH
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return [r["koy"].strip() for r in rows if r.get("koy", "").strip()]


@dataclass
class KoyEslesme:
    ham: str                       # raw name from vision
    onerilen: Optional[str]        # chosen default (matched village OR cleaned raw)
    skor: float                    # 0-100 (best candidate score)
    kullanici_onayi_gerek: bool    # ambiguous band -> ask the user
    yeni_koy: bool = False         # not in the known list -> own sheet
    adaylar: list[str] = field(default_factory=list)  # top known-list candidates


def koy_snap(ham: str) -> KoyEslesme:
    """Conservatively map a raw village name to the known list.

    - exact canonical match or score >= SNAP  -> snap (no ask)
    - SOR <= score < SNAP                      -> ask user; default keeps raw
    - score < SOR                              -> new village (own sheet, no ask)
    """
    temiz = turkish_title(ham)
    bilinenler = bilinen_koyler()
    if not bilinenler:
        return KoyEslesme(ham=ham, onerilen=temiz, skor=0.0,
                          kullanici_onayi_gerek=False, yeni_koy=True)

    kanon_map = {kanonik(b): b for b in bilinenler}
    hedef = kanonik(ham)
    if hedef in kanon_map:
        return KoyEslesme(ham=ham, onerilen=turkish_title(kanon_map[hedef]), skor=100.0,
                          kullanici_onayi_gerek=False, adaylar=[kanon_map[hedef]])

    sonuc = process.extract(hedef, list(kanon_map.keys()), scorer=fuzz.ratio, limit=3)
    if not sonuc:
        return KoyEslesme(ham=ham, onerilen=temiz, skor=0.0,
                          kullanici_onayi_gerek=False, yeni_koy=True)
    adaylar = [kanon_map[k] for k, _, _ in sonuc]
    skor = float(sonuc[0][1])

    if skor >= config.KOY_SNAP_ESIK:                      # clear variant -> snap
        return KoyEslesme(ham=ham, onerilen=turkish_title(adaylar[0]), skor=skor,
                          kullanici_onayi_gerek=False, adaylar=adaylar)
    if skor >= config.KOY_SOR_ESIK:                       # ambiguous -> ask, keep raw
        return KoyEslesme(ham=ham, onerilen=temiz, skor=skor,
                          kullanici_onayi_gerek=True, yeni_koy=True, adaylar=adaylar)
    return KoyEslesme(ham=ham, onerilen=temiz, skor=skor,  # clearly new village
                      kullanici_onayi_gerek=False, yeni_koy=True, adaylar=adaylar)


def birim_normalize(olcu_birimi: Optional[str]) -> str:
    b = (olcu_birimi or "").strip()
    return b if b else config.OLCU_BIRIMI_VARSAYILAN


@dataclass
class KoySayfasi:
    koy: str                       # display name (canonical chosen)
    kalemler: list[Kalem] = field(default_factory=list)


def topla(
    kalemler: list[Kalem],
    koy_haritasi: Optional[dict[str, str]] = None,
    miktar_topla: Optional[bool] = None,
) -> list[KoySayfasi]:
    """Group items by canonical village -> one KoySayfasi per village.

    koy_haritasi: optional {raw_koy -> chosen display name} from user approval.
    miktar_topla: same malzeme + same birim within a village -> sum quantities.
    """
    if miktar_topla is None:
        miktar_topla = config.MALZEME_MIKTAR_TOPLA
    koy_haritasi = koy_haritasi or {}

    gruplar: dict[str, KoySayfasi] = {}
    for k in kalemler:
        gosterim = koy_haritasi.get(k.koy) or koy_snap(k.koy).onerilen or k.koy
        anahtar = kanonik(gosterim)
        if anahtar not in gruplar:
            gruplar[anahtar] = KoySayfasi(koy=gosterim)
        # work on a copy with normalized unit
        kk = k.model_copy(update={"olcu_birimi": birim_normalize(k.olcu_birimi)})
        gruplar[anahtar].kalemler.append(kk)

    if miktar_topla:
        for sayfa in gruplar.values():
            sayfa.kalemler = _birlestir(sayfa.kalemler)

    # stable order by display name
    return sorted(gruplar.values(), key=lambda s: turkish_lower(s.koy))


def _birlestir(kalemler: list[Kalem]) -> list[Kalem]:
    """Merge identical (malzeme, birim) lines by summing quantities, order kept."""
    birikim: dict[tuple, Kalem] = {}
    sira: list[tuple] = []
    for k in kalemler:
        anahtar = (turkish_lower(k.malzeme_adi.strip()), (k.olcu_birimi or "").strip().lower())
        if anahtar in birikim:
            mevcut = birikim[anahtar]
            birikim[anahtar] = mevcut.model_copy(update={
                "miktar": mevcut.miktar + k.miktar,
                "guven_miktar": min(mevcut.guven_miktar, k.guven_miktar),
            })
        else:
            birikim[anahtar] = k
            sira.append(anahtar)
    return [birikim[a] for a in sira]
