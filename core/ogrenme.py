"""Persistent learning of user corrections (village / material / unit names).

A single JSON map of canonical(raw) -> corrected value, stored on a SEPARATE
GitHub branch (so saving does not redeploy the app branch). Falls back to a
local file when no GitHub token is configured (local launcher use).

Shape:
    {"koy": {...}, "malzeme": {...}, "birim": {...}}
"""
import base64
import json

import requests

import config
from core.normalize import kanonik

ALANLAR = ("koy", "malzeme", "birim")
_API = "https://api.github.com"


def _bos() -> dict:
    return {a: {} for a in ALANLAR}


def aktif_github() -> bool:
    return bool(config.GITHUB_TOKEN and config.GITHUB_REPO)


def _basliklar() -> dict:
    return {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _url(yol: str) -> str:
    return f"{_API}/repos/{config.GITHUB_REPO}/{yol}"


def _branch_hazirla():
    """Create the learning branch off the default branch if it doesn't exist."""
    r = requests.get(_url(f"branches/{config.OGRENME_BRANCH}"), headers=_basliklar(), timeout=15)
    if r.status_code == 200:
        return
    r = requests.get(_url(f"git/refs/heads/{config.GITHUB_DEFAULT_BRANCH}"),
                     headers=_basliklar(), timeout=15)
    r.raise_for_status()
    sha = r.json()["object"]["sha"]
    requests.post(_url("git/refs"), headers=_basliklar(), timeout=15,
                  json={"ref": f"refs/heads/{config.OGRENME_BRANCH}", "sha": sha})


def yukle() -> tuple[dict, str | None]:
    """Return (memory, sha). sha is None when there is no remote file yet."""
    if not aktif_github():
        p = config.OGRENME_LOCAL
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            return _normalize(data), None
        return _bos(), None
    try:
        _branch_hazirla()
        r = requests.get(_url(f"contents/{config.OGRENME_PATH}"), headers=_basliklar(),
                         params={"ref": config.OGRENME_BRANCH}, timeout=15)
        if r.status_code == 200:
            j = r.json()
            data = json.loads(base64.b64decode(j["content"]).decode("utf-8"))
            return _normalize(data), j["sha"]
        return _bos(), None
    except Exception:
        # never break the app over the learning back-end
        return _bos(), None


def _normalize(data: dict) -> dict:
    out = _bos()
    for a in ALANLAR:
        if isinstance(data.get(a), dict):
            out[a] = data[a]
    return out


def kaydet(data: dict, sha: str | None) -> str | None:
    """Persist memory; return new sha (or None for local file)."""
    govde = json.dumps(data, ensure_ascii=False, indent=2)
    if not aktif_github():
        config.OGRENME_LOCAL.parent.mkdir(parents=True, exist_ok=True)
        config.OGRENME_LOCAL.write_text(govde, encoding="utf-8")
        return None
    payload = {
        "message": "öğrenilen düzeltmeler güncellendi",
        "content": base64.b64encode(govde.encode("utf-8")).decode("ascii"),
        "branch": config.OGRENME_BRANCH,
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(_url(f"contents/{config.OGRENME_PATH}"), headers=_basliklar(),
                     json=payload, timeout=20)
    r.raise_for_status()
    return r.json()["content"]["sha"]


def uygula(kalemler, data: dict):
    """Apply learned corrections to freshly extracted items (in place)."""
    for k in kalemler:
        yeni = data["koy"].get(kanonik(k.koy))
        if yeni:
            k.koy = yeni
        yeni = data["malzeme"].get(kanonik(k.malzeme_adi))
        if yeni:
            k.malzeme_adi = yeni
        if k.olcu_birimi:
            yeni = data["birim"].get(kanonik(k.olcu_birimi))
            if yeni:
                k.olcu_birimi = yeni
    return kalemler


def ekle(data: dict, alan: str, ham: str, dogru: str) -> bool:
    """Record a correction kanonik(ham) -> dogru. Returns True if memory changed."""
    ham = (ham or "").strip()
    dogru = (dogru or "").strip()
    if not ham or not dogru or kanonik(ham) == kanonik(dogru):
        return False
    if data[alan].get(kanonik(ham)) == dogru:
        return False
    data[alan][kanonik(ham)] = dogru
    return True


def sayilar(data: dict) -> dict:
    return {a: len(data.get(a, {})) for a in ALANLAR}
