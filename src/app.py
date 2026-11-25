"""
Pintu Utama Aplikasi: TCG Card Battle.

Pusat kendali aplikasi Streamlit yang mengatur:
1. Konfigurasi halaman dan tema tampilan.
2. Pemeriksaan login pemain.
3. Navigasi menu atas, konten halaman aktif, dan panel info di sidebar.

Cara menjalankan:
    streamlit run app.py
"""

import streamlit as st

import theme
from core.autentikasi import GudangAkun, cari_file_simpanan_pemain
from core.state import ProgresPemain
from views import battle, collection, gacha, home, login, settings
from views.common import DataAplikasi, muat_katalog_kartu

# --- Konfigurasi Halaman & Daftar Menu ---
st.set_page_config(
    page_title="TCG Card Battle",
    page_icon=theme.ambil_ikon_halaman(),
    layout="wide",
)

HALAMAN_DEFAULT = "🏠 Beranda"
NAMA_MENU_PENGATURAN = "⚙️ Pengaturan"

MENU_UTAMA = {
    HALAMAN_DEFAULT: home,
    "🎰 Gacha": gacha,
    "📚 Koleksi": collection,
    "⚔️ Battle": battle,
}

SEMUA_HALAMAN = {
    **MENU_UTAMA,
    NAMA_MENU_PENGATURAN: settings,
}


# --- Fungsi Pembantu ---

def pindah_ke_halaman(nama_halaman: str) -> None:
    """Menyimpan nama halaman yang baru saja diklik pemain."""
    st.session_state["halaman_aktif"] = nama_halaman


def hitung_persen_menang(progres: ProgresPemain) -> str:
    """Menghitung persentase kemenangan pemain, misalnya '75%'."""
    total_main = progres.menang + progres.kalah
    if total_main == 0:
        return "-"
    return f"{(progres.menang / total_main) * 100:.0f}%"
    


# --- Komponen Navigasi & Sidebar ---

def tampilkan_menu_atas() -> None:
    """Menampilkan barisan tombol menu utama di bagian tengah atas layar."""
    halaman_sekarang = st.session_state["halaman_aktif"]
    _, area_tengah, _ = st.columns([1, 6, 1])

    with area_tengah:
        daftar_kolom = st.columns(len(MENU_UTAMA))
        for kolom, nama_menu in zip(daftar_kolom, MENU_UTAMA):
            warna_tombol = "primary" if halaman_sekarang == nama_menu else "secondary"
            kolom.button(
                nama_menu,
                key=f"nav_{nama_menu}",
                width="stretch",
                on_click=pindah_ke_halaman,
                args=(nama_menu,),
                type=warna_tombol,
            )

    st.divider()


# def tampilkan_panel_kiri(nama_pemain: str, progres: ProgresPemain) -> None:
#     """Menampilkan logo, info pemain, statistik, tombol Pengaturan, dan Keluar."""
#     with st.sidebar:
#         ikon_html = theme.ambil_ikon_untuk_html()
#         st.markdown(
#             f'<div class="app-title">'
#             f'<img src="{ikon_html}" class="app-icon">'
#             f"TCG Card Battle</div>",
#             unsafe_allow_html=True,
#         )
#         st.divider()

#         st.markdown(f"👤 **{nama_pemain}**")

#         total_kartu = sum(progres.koleksi.values())

#         kolom_kiri, kolom_kanan = st.columns(2)
#         kolom_kiri.metric("🪙 Koin", progres.koin)
#         kolom_kanan.metric("Total kartu", total_kartu)

#         kolom_kiri_2, kolom_kanan_2 = st.columns(2)
#         kolom_kiri_2.metric("Win rate", hitung_persen_menang(progres))
#         kolom_kanan_2.metric("Rekor (M/K)", f"{progres.menang}/{progres.kalah}")

#         st.divider()

#         warna_pengaturan = (
#             "primary"
#             if st.session_state["halaman_aktif"] == NAMA_MENU_PENGATURAN
#             else "secondary"
#         )
#         st.button(
#             NAMA_MENU_PENGATURAN,
#             width="stretch",
#             on_click=pindah_ke_halaman,
#             args=(NAMA_MENU_PENGATURAN,),
#             type=warna_pengaturan,
#         )

#         if st.button("Keluar", width="stretch"):
#             st.session_state.clear()
#             st.rerun()


# --- Alur Utama Aplikasi ---

def jalankan_aplikasi() -> None:
    """Menjalankan alur utama aplikasi dari awal hingga akhir."""
    theme.pasang_tema_tampilan()

    # Jika belum login, tampilkan halaman Login lalu hentikan eksekusi
    if "user" not in st.session_state:
        login.tampilkan_halaman(GudangAkun())
        st.stop()

    # Muat data progres pemain
    # nama_pemain = st.session_state["user"]
    # lokasi_simpan = cari_file_simpanan_pemain(nama_pemain)
    # if "progres" not in st.session_state:
    #     st.session_state["progres"] = ProgresPemain.muat_dari_file(lokasi_simpan)
    # progres = st.session_state["progres"]

    # Pastikan halaman aktif selalu valid (default: Beranda)
    if st.session_state.get("halaman_aktif") not in SEMUA_HALAMAN:
        st.session_state["halaman_aktif"] = HALAMAN_DEFAULT

    # Tampilkan navigasi atas dan isi halaman yang dipilih
    tampilkan_menu_atas()

    # katalog_kartu, catatan = muat_katalog_kartu()
    # data_aplikasi = DataAplikasi(
    #     katalog_kartu=katalog_kartu,
    #     progres=progres,
    #     catatan=catatan,
    #     lokasi_simpan=lokasi_simpan,
    # )
    # SEMUA_HALAMAN[st.session_state["halaman_aktif"]].tampilkan_halaman(data_aplikasi)

    # # Tampilkan panel kiri di akhir agar angka koin & rekor selalu terbaru
    # tampilkan_panel_kiri(nama_pemain, progres)


jalankan_aplikasi()
