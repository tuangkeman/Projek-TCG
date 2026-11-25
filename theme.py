"""
Tema & Warna Tampilan Aplikasi.

Mengatur tampilan visual Streamlit (warna latar, tombol, navigasi, kotak
statistik, dan ikon aplikasi) dengan palet warna terinspirasi logo Pokemon.
"""

import base64
from pathlib import Path

from PIL import Image
import streamlit as st

# --- Lokasi Aset ---
FOLDER_ASET = Path(__file__).parent / "assets"
LOKASI_IKON = FOLDER_ASET / "icon.png"

# --- Palet Warna Utama ---
WARNA_KUNING = "#FFCB05"
WARNA_BIRU = "#3B4CCA"
WARNA_MERAH = "#EE1515"
WARNA_PUTIH = "#FFFFFF"
WARNA_BIRU_TUA = "#0A1A6B"


# --- Fungsi Ikon ---

def ambil_ikon_halaman() -> Image.Image:
    """Membuka file ikon aplikasi untuk ditampilkan di tab browser."""
    return Image.open(LOKASI_IKON)


def ambil_ikon_untuk_html() -> str:
    """Mengubah file icon.png menjadi string Base64 agar bisa disisipkan di HTML."""
    teks_base64 = base64.b64encode(LOKASI_IKON.read_bytes()).decode()
    return f"data:image/png;base64,{teks_base64}"


# --- Pengaturan Tema CSS ---

def pasang_tema_tampilan() -> None:
    """Memasang aturan gaya tampilan (CSS) ke seluruh halaman Streamlit."""
    st.markdown(_buat_css_tema(), unsafe_allow_html=True)


def _buat_css_tema() -> str:
    """Menyusun blok CSS tema aplikasi."""
    return f"""
<style>
/* Definisi variabel warna agar mudah diubah di satu tempat */
:root {{
    --kuning: {WARNA_KUNING};
    --biru: {WARNA_BIRU};
    --merah: {WARNA_MERAH};
    --putih: {WARNA_PUTIH};
    --biru-tua: {WARNA_BIRU_TUA};
    --merah-gelap: #C70E0E;
    --sidebar-bg: #F3F6FF;
    --metric-bg: #EAF0FF;
}}

/* --- Latar, Header, Sidebar, & Teks --- */
.stApp {{
    background-color: var(--putih);
}}
[data-testid="stHeader"] {{
    background: transparent;
}}
[data-testid="stSidebar"] {{
    background: var(--sidebar-bg);
    border-right: 3px solid var(--kuning);
}}
h1, h2, h3 {{
    color: var(--biru) !important;
}}
hr {{
    border-color: rgba(59, 76, 202, 0.25) !important;
}}

/* --- Tombol Standar (Biru) --- */
.stButton > button,
.stFormSubmitButton > button,
.stDownloadButton > button {{
    border-radius: 10px;
    font-weight: 700;
    border: 2px solid var(--biru-tua);
    background: var(--biru);
    color: var(--putih);
}}
.stButton > button:hover,
.stFormSubmitButton > button:hover,
.stDownloadButton > button:hover {{
    border-color: var(--kuning);
    color: var(--kuning);
}}

/* --- Tombol Utama / Primary (Merah) --- */
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {{
    background: var(--merah);
    border-color: var(--biru-tua);
    color: var(--putih);
}}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {{
    background: var(--merah-gelap);
    border-color: var(--kuning);
    color: var(--kuning);
}}

/* --- Menu Navigasi Atas --- */
[class*="st-key-nav_"] button {{
    background: transparent !important;
    border: none !important;
    border-radius: 0;
    border-bottom: 3px solid transparent !important;
    color: var(--biru-tua) !important;
    box-shadow: none;
    padding: 0.6rem 0.5rem;
    min-height: 3.2rem;
}}
[class*="st-key-nav_"] button p {{
    font-size: 1.7rem !important;
    font-weight: 800;
    line-height: 1.2;
}}
[class*="st-key-nav_"] button:hover {{
    color: var(--biru) !important;
}}
[class*="st-key-nav_"] button[kind="primary"] {{
    color: var(--merah) !important;
    border-bottom: 3px solid var(--merah) !important;
}}

/* --- Kotak Angka Statistik (st.metric) --- */
[data-testid="stMetric"] {{
    background: var(--metric-bg);
    border: 2px solid var(--biru);
    border-radius: 12px;
    padding: 0.5rem 0.8rem;
}}
[data-testid="stMetricLabel"] {{
    color: var(--biru);
}}

/* --- Judul & Logo di Sidebar --- */
.app-title {{
    font-size: 2rem;
    font-weight: 900;
    overflow-wrap: anywhere;
    line-height: 1.15;
    text-align: center;
    margin: 0.2rem 0 0.6rem 0;
    color: var(--kuning);
    -webkit-text-stroke: 7px var(--biru);
    paint-order: stroke fill;
    text-shadow: 0 3px 0 var(--biru-tua);
}}
.app-icon {{
    display: block;
    width: 110px;
    margin: 0 auto 0.4rem auto;
    border-radius: 22px;
}}
</style>
"""