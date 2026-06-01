"""Central configuration. No defaults are hard-coded elsewhere; pull from here."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# --- Paths ---
TEMPLATE_PATH = BASE_DIR / "templates" / "bos_sablon.xlsx"
KOY_LISTESI_PATH = BASE_DIR / "data" / "koy_listesi.csv"
OUTPUT_DIR = BASE_DIR / "data" / "output"
# Source workbook used once to derive the clean template + village list.
SOURCE_XLSX = Path(
    os.getenv("SOURCE_XLSX", str(Path.home() / "Downloads" / "taşınır istek belgesi.xlsx"))
)

def _secret(name: str, default=None):
    """Read a secret from the environment (.env, local) or Streamlit Cloud
    secrets (st.secrets). The key is NEVER stored in the repo."""
    val = os.getenv(name)
    if val:
        return val
    try:  # only available when running inside Streamlit (e.g. cloud)
        import streamlit as st  # noqa: PLC0415
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return default


# --- Anthropic / Vision ---
ANTHROPIC_API_KEY = _secret("ANTHROPIC_API_KEY")
VISION_MODEL = _secret("VISION_MODEL", "claude-sonnet-4-6")          # primary
VISION_MODEL_FALLBACK = _secret("VISION_MODEL_FALLBACK", "claude-opus-4-8")  # hard-to-read pages
VISION_MAX_TOKENS = int(_secret("VISION_MAX_TOKENS", "4096"))

# --- App access (optional). If set, users must enter this password. Lets you
# share the URL without exposing your API credits to strangers. ---
APP_PAROLA = _secret("APP_PAROLA")

# --- Learning memory (persistent corrections). Stored on a SEPARATE GitHub
# branch so saving does not redeploy the app. Falls back to a local file when
# no token is set (local launcher use). ---
GITHUB_TOKEN = _secret("GITHUB_TOKEN")
GITHUB_REPO = _secret("GITHUB_REPO", "arslanburak58/tasinir-istek-dijitallestirici")
GITHUB_DEFAULT_BRANCH = _secret("GITHUB_DEFAULT_BRANCH", "main")
OGRENME_BRANCH = _secret("OGRENME_BRANCH", "ogrenme-verisi")
OGRENME_PATH = "ogrenme.json"
OGRENME_LOCAL = BASE_DIR / "data" / "ogrenme.json"

# --- Document defaults (verified from last-year records: KODU x911, single birim) ---
BIRIM_ADI = "Su ve Kanal Hizmetleri Müdürlüğü"
KODU_VARSAYILAN = "150.11.02.02.01."
OLCU_BIRIMI_VARSAYILAN = "Ad"
NO_VARSAYILAN = "No:......."

# --- Aggregation / layout rules ---
MAX_KALEM_PER_SAYFA = 25          # exceeding -> second sheet "KöyAdı 2"
MALZEME_MIKTAR_TOPLA = True       # same malzeme + same birim in a village -> sum quantities
DATA_START_ROW = 7                # first data row in the clean template

# --- Normalization / confidence thresholds (rapidfuzz on canonical names) ---
# The known list is NOT exhaustive, so matching is conservative: only clear
# variants snap; ambiguous cases ask the user (default keeps the raw name, never
# silently renames to a wrong village); clearly-new names get their own sheet.
KOY_SNAP_ESIK = 95                # >= -> auto-snap to the matched known village
KOY_SOR_ESIK = 88                 # [KOY_SOR_ESIK, KOY_SNAP_ESIK) -> ask the user
GUVEN_DUSUK_ESIK = 0.6            # field confidence below this -> flagged in UI

# --- Footer (Kıvanç AKTAN removed; Mevlüt DUMAN is the kayıt yetkilisi) ---
FOOTER = {
    "istek_yapan": {"ad": "Burak ARSLAN", "unvan": "Elektrik-Elektronik Mühendisi"},
    "kayit_yetkilisi": {"ad": "Mevlüt DUMAN", "unvan": "Taşınır Kayıt Yetkilisi"},
    "birim_yoneticisi": {"ad": "İsmail TAŞTAN", "unvan": "Su ve Kanal Hizmetleri Müdürü"},
}
FOOTER_METIN = {
    "istek_sol": "Birimimiz ihtiyacı için yukarıda belirtilen taşınırların verilmesi rica olunur.",
    "teslim_sag": '"Karşılanan Miktar" sütununda kayıtlı miktarları teslim edilmiştir.',
    "label_istek": "İstek Yapan Kontrol Müh.",
    "label_kayit": "Taşınır Kayıt Yetkilisi",
    "label_yonetici": "İstek Yapan Birim Yöneticisi",
    "imza": "İmzası",
    "belge_ornegi": "Belgenin bir örneği istek yapan birimde dosyalanmak üzere "
    "taşınırın teslim edildiği görevliye verilir.",
    "tmy": "T.M.Y. Örnek No:7",
}
