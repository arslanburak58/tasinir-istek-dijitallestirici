"""Taşınır code choice: detect codes that differ from the default and resolve
each item's final code from the user's answers."""
from typing import Iterable


def farkli_kodlar(kodlar: Iterable, varsayilan: str) -> list[str]:
    """Distinct codes read from the photos that differ from the default."""
    temiz = {str(k).strip() for k in kodlar if k is not None and k == k}
    return sorted(k for k in temiz if k and k != varsayilan)


def kod_sec(ham, kodu_haritasi: dict[str, str], genel_kod: str) -> str:
    """Final code for an item: the user's answer for a differing photo code,
    otherwise the document-wide code."""
    ham = "" if ham is None or ham != ham else str(ham).strip()
    return kodu_haritasi.get(ham) or genel_kod
