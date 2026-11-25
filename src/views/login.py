"""
Halaman Masuk (Login) & Daftar Akun Baru (UI).

Halaman pertama yang muncul sebelum pemain login, terdiri dari 2 tab:
1. Tab 'Masuk'  -> untuk pemain yang sudah punya akun.
2. Tab 'Daftar' -> untuk pemain baru yang ingin membuat akun.
"""

import streamlit as st

from src.core.autentikasi import ErrorAutentikasi, maks_password_len
from theme import ambil_ikon_untuk_html


def tampilkan_halaman(gudang_akun) -> None:
    """Menampilkan halaman login dan pendaftaran di tengah layar."""
    _, kolom_tengah, _ = st.columns([1, 2, 1])

    with kolom_tengah:
        _tampilkan_header()

        tab_masuk, tab_daftar = st.tabs(["Masuk", "Daftar"])
        with tab_masuk:
            _tampilkan_form_masuk(gudang_akun)
        with tab_daftar:
            _tampilkan_form_daftar(gudang_akun)


# --- Komponen Halaman ---

def _tampilkan_header() -> None:
    """Menampilkan logo, judul, dan deskripsi singkat aplikasi."""
    ikon_html = ambil_ikon_untuk_html()
    st.markdown(
        f"""
        <div style="text-align: center;">
            <img src="{ikon_html}" width="130">
            <h1 style="text-align: center; padding-top: 0.3rem;">TCG Card Battle</h1>
            <p>
                Kumpulkan kartu, susun deck, dan latih battle melawan bot.
                Masuk dulu supaya progresmu tersimpan.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _tampilkan_form_masuk(gudang_akun) -> None:
    """Formulir login untuk pemain yang sudah memiliki akun."""
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        tombol_masuk = st.form_submit_button("Masuk", type="primary", width="stretch")

    if not tombol_masuk:
        return

    try:
        nama_sah = gudang_akun.masuk_akun(username, password)
    except ErrorAutentikasi as pesan_error:
        st.error(str(pesan_error))
    else:
        _mulai_sesi(nama_sah)


def _tampilkan_form_daftar(gudang_akun) -> None:
    """Formulir pendaftaran untuk pemain baru."""
    with st.form("register_form"):
        username_baru = st.text_input(
            "Username baru",
            help="3-20 karakter: huruf kecil, angka, underscore",
        )
        password_baru = st.text_input(
            f"Password (minimal {maks_password_len} karakter)",
            type="password",
        )
        ulangi_password = st.text_input("Ulangi password", type="password")
        tombol_buat = st.form_submit_button("Buat akun", type="primary", width="stretch")

    if not tombol_buat:
        return

    try:
        nama_baru = gudang_akun.daftar_akun_baru(
            username_baru,
            password_baru,
            ulangi_password,
        )
    except ErrorAutentikasi as pesan_error:
        st.error(str(pesan_error))
    else:
        _mulai_sesi(nama_baru)


def _mulai_sesi(username: str) -> None:
    """Simpan username ke session state lalu muat ulang halaman."""
    st.session_state["user"] = username
    st.rerun()