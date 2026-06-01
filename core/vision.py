"""Anthropic Vision extraction via tool use -> Pydantic. No free-text parsing.

Reads an image, sends it to the Messages API forcing the `tutanak_kaydet` tool,
and validates the structured result. Hard-to-read pages fall back to the opus
model. Unreadable fields are left blank with low confidence (no hallucination).
"""
import base64
from pathlib import Path
from typing import Optional, Union

import anthropic

import config
from core.schema import TUTANAK_TOOL, Tutanak

SISTEM_PROMPT = """Sen bir Taşınır İstek Belgesi tutanağını okuyorsun. Görüntü el yazısı \
olabilir. SADECE gördüğünü çıkar, hiçbir şey uydurma. Okuyamadığın alanı boş bırak ve o \
alanın güvenini düşük ver.

Her malzeme kalemi için şu alanları çıkar:
- koy: köy/mahalle adı (Türkçe karakterleri koru: ç ğ ı İ ş ü ö)
- malzeme_adi: TEK bir malzemenin adı
- miktar: sayı (sadece rakam; "bir" yazılıysa 1)
- olcu_birimi: yazılı değilse boş bırak (varsayılan sonradan 'Ad' atanır)
- kodu: taşınır kodu görünüyorsa yaz, yoksa boş
Belgede birden çok köy olabilir; her kalemi ait olduğu köyle eşle.

ÇOK ÖNEMLİ — HER MALZEME AYRI BİR KALEM:
Bir köyün karşısında '-', ',', '/' ile ayrılmış birden çok malzeme varsa, HER \
MALZEMEYİ AYRI bir kalem olarak çıkar. ASLA birden çok malzemeyi tek malzeme_adi \
içinde birleştirme. Her malzemenin KENDİ miktarı ve ölçü birimi olur. Bir sayı/birim \
(örn. '25 kg') yalnızca o sayının yazıldığı malzemeye aittir; sayısı yazılmayan \
cihazlar için miktar=1 ve ölçü birimi boş bırak.

Örnek: 'Merkez Acıpınar => Akü - ORP - Şarj Kiti - Emiş çekvalfi - 25 kg Sıvı Klor' \
satırı TAM OLARAK şu 5 ayrı kalem olur:
1) koy=Merkez Acıpınar, malzeme_adi=Akü, miktar=1, olcu_birimi=(boş)
2) koy=Merkez Acıpınar, malzeme_adi=ORP, miktar=1, olcu_birimi=(boş)
3) koy=Merkez Acıpınar, malzeme_adi=Şarj Kiti, miktar=1, olcu_birimi=(boş)
4) koy=Merkez Acıpınar, malzeme_adi=Emiş çekvalfi, miktar=1, olcu_birimi=(boş)
5) koy=Merkez Acıpınar, malzeme_adi=Sıvı Klor, miktar=25, olcu_birimi=kg

Çıktıyı yalnızca verilen araç (tool) ile, JSON şemasına göre döndür. Her kalem için \
alan-bazlı güven (0.0-1.0) ekle; özellikle miktar ve köy adında emin değilsen düşük ver."""

_MEDIA = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".gif": "image/gif",
}


def _client() -> anthropic.Anthropic:
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY tanımlı değil (.env).")
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def _media_type(name: str, override: Optional[str]) -> str:
    if override:
        return override
    return _MEDIA.get(Path(name).suffix.lower(), "image/jpeg")


def _extract_with_model(client, model: str, b64: str, media_type: str) -> Tutanak:
    resp = client.messages.create(
        model=model,
        max_tokens=config.VISION_MAX_TOKENS,
        system=SISTEM_PROMPT,
        tools=[TUTANAK_TOOL],
        tool_choice={"type": "tool", "name": TUTANAK_TOOL["name"]},
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": "Bu tutanaktaki tüm kalemleri çıkar."},
            ],
        }],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == TUTANAK_TOOL["name"]:
            return Tutanak.model_validate(block.input)
    return Tutanak(kalemler=[])


def _dusuk_guven(t: Tutanak) -> bool:
    if not t.kalemler:
        return True
    esik = config.GUVEN_DUSUK_ESIK
    dusuk = sum(
        1 for k in t.kalemler
        if min(k.guven_koy, k.guven_malzeme, k.guven_miktar) < esik
    )
    return dusuk / len(t.kalemler) > 0.5


def cikar(
    image: Union[str, Path, bytes],
    media_type: Optional[str] = None,
    dosya_adi: str = "image.jpg",
    fallback: bool = True,
) -> Tutanak:
    """Extract line items from one photo. Falls back to the opus model when the
    primary result is empty or mostly low-confidence."""
    if isinstance(image, (str, Path)):
        data = Path(image).read_bytes()
        dosya_adi = str(image)
    else:
        data = image
    b64 = base64.standard_b64encode(data).decode("ascii")
    mt = _media_type(dosya_adi, media_type)

    client = _client()
    sonuc = _extract_with_model(client, config.VISION_MODEL, b64, mt)

    if fallback and config.VISION_MODEL_FALLBACK and _dusuk_guven(sonuc):
        try:
            yedek = _extract_with_model(client, config.VISION_MODEL_FALLBACK, b64, mt)
            if yedek.kalemler and not _dusuk_guven(yedek):
                return yedek
            # keep whichever has more items
            if len(yedek.kalemler) > len(sonuc.kalemler):
                return yedek
        except anthropic.APIError:
            pass
    return sonuc
