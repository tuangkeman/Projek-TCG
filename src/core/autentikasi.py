"""
sistem autentikasi
- Password dienkripsi.
- Data akun akan disimpan di `data/users.json`.
- Akun akan terkunci selama 60 detik jika salah memasukkan password 5 kali berturut-turut.
"""

import hashlib
import hmac
import json
import os
import re
import secrets
import time
from pathlib import Path

from .config import FOLDER_DATA

# --- Konfigurasi ---
LOKASI_FILE_AKUN = FOLDER_DATA / "users.json"
FOLDER_SIMPANAN = FOLDER_DATA / "saves"

JUMLAH_PUTARAN_ACAK = 200_000
username_allowed = re.compile(r"^[a-z0-9_]{3,20}$")
maks_password_len = 6
batas_password_salah = 5
countdown_salah_password = 60
pesanError = "Username atau password salah."


class ErrorAutentikasi(Exception):
    """Error terkait akun yang pesannya aman ditampilkan langsung ke pemain."""


# --- Fungsi Pembantu (Helper) ---

def rapikan_username(teks_mentah: str) -> str:
    """Ubah username ke huruf kecil dan pastikan formatnya valid."""
    nama = (teks_mentah or "").strip().lower()
    if not username_allowed.match(nama):
        raise ErrorAutentikasi(
            "Username 3-20 karakter, hanya huruf, angka, dan underscore (_)."
        )
    return nama


def _validasi_password(password: str, konfirmasi: str | None = None, label: str = "Password") -> None:
    """Cek panjang minimal password dan kecocokan dengan konfirmasi."""
    if len(password) < maks_password_len:
        raise ErrorAutentikasi(f"{label} minimal {maks_password_len} karakter.")
    if konfirmasi is not None and password != konfirmasi:
        raise ErrorAutentikasi(f"Konfirmasi {label.lower()} tidak sama.")


def acak_password(
    password: str,
    garam: bytes | None = None,
    jumlah_putaran: int = JUMLAH_PUTARAN_ACAK,
) -> dict:
    """Ubah password teks biasa menjadi hash acak + salt."""
    garam = garam or secrets.token_bytes(16)
    kode_acak = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        garam,
        jumlah_putaran,
    )
    return {
        "salt": garam.hex(),
        "hash": kode_acak.hex(),
        "iter": jumlah_putaran,
    }


def cocokkan_password(password: str, data_tersimpan: dict) -> bool:
    """Bandingkan password input dengan hash yang tersimpan secara aman."""
    garam = bytes.fromhex(data_tersimpan["salt"])
    jumlah_putaran = int(data_tersimpan["iter"])

    kode_dicek = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        garam,
        jumlah_putaran,
    )
    return hmac.compare_digest(kode_dicek.hex(), data_tersimpan["hash"])


def cari_file_simpanan_pemain(username: str) -> Path:
    """Kembalikan lokasi file save progres milik pemain."""
    nama_bersih = rapikan_username(username)
    return FOLDER_SIMPANAN / f"{nama_bersih}.json"


# --- Pengelola Akun ---

class GudangAkun:
    """Mengelola baca/tulis akun, pendaftaran, login, dan ganti password."""

    def __init__(self, lokasi_file: Path | None = None):
        self.lokasi_file = lokasi_file or LOKASI_FILE_AKUN

    def baca_semua_akun(self) -> dict:
        """Baca seluruh akun dari file JSON. Kembalikan dict kosong jika gagal."""
        try:
            data = json.loads(self.lokasi_file.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def simpan_semua_akun(self, semua_akun: dict) -> None:
        """Simpan akun ke file sementara dulu, lalu timpa file asli (anti-korup)."""
        self.lokasi_file.parent.mkdir(parents=True, exist_ok=True)
        file_sementara = self.lokasi_file.with_suffix(".tmp")
        file_sementara.write_text(json.dumps(semua_akun, indent=2), encoding="utf-8")
        os.replace(file_sementara, self.lokasi_file)

    def daftar_akun_baru(self, username: str, password: str, konfirmasi: str | None = None) -> str:
        """Daftarkan akun baru setelah semua syarat terpenuhi."""
        nama = rapikan_username(username)
        _validasi_password(password, konfirmasi)

        semua_akun = self.baca_semua_akun()
        if nama in semua_akun:
            raise ErrorAutentikasi("Username sudah dipakai.")

        semua_akun[nama] = {
            "password": acak_password(password),
            "created": int(time.time()),
            "fails": 0,
            "locked_until": 0,
        }
        self.simpan_semua_akun(semua_akun)
        return nama

    def masuk_akun(self, username: str, password: str) -> str:
        """Verifikasi login pemain dan tangani penguncian jika salah berulang."""
        try:
            nama = rapikan_username(username)
        except ErrorAutentikasi:
            raise ErrorAutentikasi(pesanError) from None

        semua_akun = self.baca_semua_akun()
        akun = semua_akun.get(nama)

        # Jika akun tidak ada, tetap jalankan hash palsu agar waktu respon sama
        if akun is None:
            acak_password(password)
            raise ErrorAutentikasi(pesanError)

        self._cek_status_kunci(akun)

        if cocokkan_password(password, akun["password"]):
            akun["fails"] = 0
            akun["locked_until"] = 0
            self.simpan_semua_akun(semua_akun)
            return nama

        self._catat_login_gagal(akun)
        self.simpan_semua_akun(semua_akun)
        raise ErrorAutentikasi(pesanError)

    def ganti_password(
        self,
        username: str,
        password_lama: str,
        password_baru: str,
        konfirmasi: str | None = None,
    ) -> None:
        """Verifikasi password lama, lalu simpan password baru."""
        try:
            nama = self.masuk_akun(username, password_lama)
        except ErrorAutentikasi as error:
            if str(error) == pesanError:
                raise ErrorAutentikasi("Password lama salah.") from None
            raise

        _validasi_password(password_baru, konfirmasi, label="Password baru")
        if password_baru == password_lama:
            raise ErrorAutentikasi("Password baru harus berbeda dari password lama.")

        semua_akun = self.baca_semua_akun()
        semua_akun[nama]["password"] = acak_password(password_baru)
        self.simpan_semua_akun(semua_akun)

    # --- Helper Internal ---

    def _cek_status_kunci(self, akun: dict) -> None:
        """Tolak login jika akun masih dalam masa kunci sementara."""
        waktu_sekarang = time.time()
        terkunci_sampai = akun.get("locked_until", 0)
        if terkunci_sampai > waktu_sekarang:
            sisa_detik = int(terkunci_sampai - waktu_sekarang) + 1
            raise ErrorAutentikasi(
                f"Terlalu banyak percobaan salah. Coba lagi dalam {sisa_detik} detik."
            )

    def _catat_login_gagal(self, akun: dict) -> None:
        """Tambah hitungan gagal; kunci akun bila mencapai batas."""
        jumlah_salah = akun.get("fails", 0) + 1
        if jumlah_salah >= batas_password_salah:
            akun["fails"] = 0
            akun["locked_until"] = time.time() + countdown_salah_password
        else:
            akun["fails"] = jumlah_salah