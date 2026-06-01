"""Structured extraction schema. Vision output is bound to this via tool use;
never parse free text."""
from typing import Optional

from pydantic import BaseModel, Field


class Kalem(BaseModel):
    """A single requested material line, tied to the village it belongs to."""

    koy: str = Field(description="Köy/mahalle adı")
    malzeme_adi: str = Field(description="İstenen malzemenin adı")
    miktar: float = Field(description="Sayısal miktar")
    olcu_birimi: Optional[str] = Field(default=None, description="Ölçü birimi; yoksa boş")
    kodu: Optional[str] = Field(default=None, description="Taşınır kodu; yoksa boş")

    guven_koy: float = Field(ge=0, le=1, description="Köy adı güveni 0-1")
    guven_malzeme: float = Field(ge=0, le=1, description="Malzeme adı güveni 0-1")
    guven_miktar: float = Field(ge=0, le=1, description="Miktar güveni 0-1")


class Tutanak(BaseModel):
    """All line items extracted from one photo (may span multiple villages)."""

    kalemler: list[Kalem] = Field(default_factory=list)


# JSON schema for Anthropic tool use; keeps the model bound to the structure.
TUTANAK_TOOL = {
    "name": "tutanak_kaydet",
    "description": "Taşınır İstek Belgesi'nden okunan tüm malzeme kalemlerini kaydet.",
    "input_schema": {
        "type": "object",
        "properties": {
            "kalemler": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "koy": {"type": "string"},
                        "malzeme_adi": {"type": "string"},
                        "miktar": {"type": "number"},
                        "olcu_birimi": {"type": ["string", "null"]},
                        "kodu": {"type": ["string", "null"]},
                        "guven_koy": {"type": "number", "minimum": 0, "maximum": 1},
                        "guven_malzeme": {"type": "number", "minimum": 0, "maximum": 1},
                        "guven_miktar": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": [
                        "koy", "malzeme_adi", "miktar",
                        "guven_koy", "guven_malzeme", "guven_miktar",
                    ],
                },
            }
        },
        "required": ["kalemler"],
    },
}
