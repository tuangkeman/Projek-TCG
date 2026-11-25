import os
from pathlib import Path

from dotenv import load_dotenv

FOLDER_UTAMA = Path(__file__).resolve().parent.parent
FOLDER_DATA = FOLDER_UTAMA / "data"
FOLDER_CACHE = FOLDER_DATA / "cache"

SETKARTUREK = [
    "base1", "base2", "basep", "wp", "base3", "base4", "base5", "lc", "dpp", "dp1", "dp2", "dp3", "dp4", "dp5", "dp6", "dp7", "pl1", "pl2", "pl3", "pl4", "ru1", "bw1", "bwp", "bw2", "bw3", "bw4", "bw5", "bw6", "dv1", "bw7", "bw8", "bw9", "bw10", "bw11", "rc", "xyp", "xy0", "xya", "xy1", "xy2", "xy3", "xy4", "xy5", "dc1", "xy6", "xy7", "xy8", "xy9",
    "g1", "xy10", "xy11", "xy12", "smp", "sm1", "sm2", "sm3", "sm3.5", "sm4", "sm5", "sm6", "sm7", "sm7.5", "sm8", "sm9", "det1", "sm10", "sm11", "sma", "sm115", "sm12", "mee", "me01", "mep", "me02", "me02.5", "me03", "me04", "me05", "30th-c", "30th", "me06",
]

load_dotenv(FOLDER_UTAMA / ".env")

class ErrorKonfigurasi(Exception):
    """Pesan error jika ada pengaturan wajib di file .env yang lupa diisi."""


"""Mengambil alamat web (URL) API data kartu dari file .env."""
def ambil_alamat_api_kartu():
    alamatapi = os.getenv("CARD_API_URL", "").strip() # hapus garis miring '/' di ujung paling belakang supaya alamatnya rapi
    return alamatapi.rstrip("/")

"""Mengambil alamat server, API key, nama model, dan batas waktu tunggu AI dari .env."""
def ambil_pengaturan_ai():
    batasWaktuT = os.getenv("AI_TIMEOUT", "120")
    if not batasWaktuT:
        batasWaktuT = "120"
    return {
        "base_url": os.getenv("AI_BASE_URL", "").strip().rstrip("/"),
        "api_key": os.getenv("AI_API_KEY", "").strip(),
        "model": os.getenv("AI_MODEL", "").strip(),
        "timeout": float(batasWaktuT),
    }
