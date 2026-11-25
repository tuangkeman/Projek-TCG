"""
Data kartu Pokemon berasal dari TCGdex ges
biar ga nunggu proses tiap kali buka game
kartu selesai diunduh disimpan dikomputer
nanti di folder cache json
saat game dibuka nanti kalo ada cache app baca dari file cache biar lebih cepat 
"""

import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed #ini theard pool biar bisa banyak req sekaligus, memberi hasil begitu tiap req selesai
from urllib.parse import quote #encode id agar aman di url ges
import requests
from requests.adapters import HTTPAdapter #library http
from .cards import apakah_rarity_diizinkan, rapikan_data_kartu #ini nanti ambil dari card trus ambil fungsinya
from .config import DAFTAR_SET_KARTU, FOLDER_CACHE, ErrorKonfigurasi, ambil_alamat_api_kartu #ini nanti ambil dari config trus ambil fungsinya

JUMLAH_PEKERJA = 32 #jumlah theard pararel maks

penyimpanan_koneksi = threading.local() #Penyimpanan koneksi internet per pekerja supaya koneksi bisa dipakai berulang kali


"""
Mengambil (atau membuat baru) koneksi HTTP untuk mengunduh data dari internet
Kalau belum punya koneksi internet, buat dulu. Kalau sudah punya, pakai yang lama.
agar menghemat waktu saat unduh ribuan kartu
"""
def ambil_sesi_internet():
    sesi = getattr(penyimpanan_koneksi, "sesi", None) #cek udah punya sesi?
    if sesi is None: #jika belum buat baru
        sesi = requests.Session() #nanti ini buat
        pengatur_koneksi = HTTPAdapter( #cara sesi mengelola koneksinya
            pool_connections=4,
            pool_maxsize=JUMLAH_PEKERJA,
            max_retries=0,
        )
        sesi.mount("https://", pengatur_koneksi)
        sesi.mount("http://", pengatur_koneksi)
        sesi.headers.update({ #keterangan yang ikut terkirim di setiap permintaan
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "tcg-card-battle/0.1",
        })
        penyimpanan_koneksi.sesi = sesi #sesinya disimpan
    return sesi 


"""
ambil data dari tcgdex kalo berhasil mengembalikan datanya
kalau alamat tidak ada (404), mengembalikan None
kalau gagal karena jaringan, mencoba ulang sampai 3 kali dengan jeda makin lama, 
lalu menyerah dengan RuntimeError
"""
def ambil_json_dari_internet(jalur, jumlah_coba_ulang=2):
    try:
        alamat_dasar = ambil_alamat_api_kartu()
    except ErrorKonfigurasi as error:
        raise RuntimeError(str(error)) from error

    alamat_lengkap = f"{alamat_dasar}/{jalur}"

    for percobaan in range(jumlah_coba_ulang + 1):
        try:
            respon = ambil_sesi_internet().get(alamat_lengkap, timeout=(5, 30))
            if respon.status_code == 404:
                return None
            respon.raise_for_status()
            return respon.json()
        except (requests.RequestException, ValueError) as error:
            if percobaan == jumlah_coba_ulang:
                raise RuntimeError(f"Gagal menghubungi TCGdex ({jalur}): {error}") from error
            time.sleep(0.8 * (percobaan + 1))
#-------------------------------------------
#bagian bawah ini nanti cache
"""Membuat nama file cache di komputer untuk sebuah set kartu."""
def lokasi_file_cache(id_set):
    nama_aman = re.sub(r"[^A-Za-z0-9._-]", "_", id_set)
    return FOLDER_CACHE / f"set_{nama_aman}.json"


"""Membaca daftar kartu satu set dari komputer. Mengembalikan None jika belum ada."""
def baca_cache_set(id_set):
    try:
        isi_teks = lokasi_file_cache(id_set).read_text(encoding="utf-8")
        daftar_kartu = json.loads(isi_teks)
    except (OSError, ValueError):
        return None

    if not isinstance(daftar_kartu, list):
        return None

    # Saring lagi: hanya pakai kartu yang ada gambarnya dan kelangkaannya diizinkan
    kartu_layak = []
    for kartu in daftar_kartu:
        if kartu.get("image") and apakah_rarity_diizinkan(kartu.get("rarity")):
            kartu_layak.append(kartu)
    return kartu_layak


"""Menyimpan daftar kartu satu set ke file cache secara aman."""
def simpan_cache_set(id_set, daftar_kartu):
    lokasi = lokasi_file_cache(id_set)
    lokasi.parent.mkdir(parents=True, exist_ok=True)

    file_sementara = lokasi.with_suffix(".tmp")
    teks_json = json.dumps(daftar_kartu, ensure_ascii=False, separators=(",", ":"))
    file_sementara.write_text(teks_json, encoding="utf-8")
    file_sementara.replace(lokasi)

#------------------------------
#bagian bawah ini nanti unduh 
"""
Mengunduh semua kartu dari beberapa set sekaligus menggunakan banyak pekerja paralel.
Mengembalikan 3 hal:
hasil_per_set  : kamus {kode_set: [daftar_kartu]}
tidak_ketemu   : daftar kode set yang tidak ada di situs TCGdex
gagal_sebagian : daftar kode set yang sebagian kartunya gagal diunduh
"""
def unduh_banyak_set_kartu(daftar_id_set, fungsi_progres=None):
    hasil_per_set = {}
    tidak_ketemu = []
    gagal_sebagian = set()

    with ThreadPoolExecutor(max_workers=JUMLAH_PEKERJA) as tim_pekerja:
        # Langkah 1: Minta daftar ID kartu yang ada di tiap set
        daftar_tugas_set = {}
        for id_set in daftar_id_set:
            tugas = tim_pekerja.submit(ambil_json_dari_internet, f"sets/{quote(id_set)}")
            daftar_tugas_set[tugas] = id_set

        asal_set_kartu = {}  # Mencatat setiap ID kartu berasal dari set mana

        for tugas in as_completed(daftar_tugas_set):
            id_set = daftar_tugas_set[tugas]
            info_set = tugas.result()

            if not info_set or not info_set.get("cards"):
                tidak_ketemu.append(id_set)
                continue

            hasil_per_set[id_set] = []
            for kartu_ringkas in info_set["cards"]:
                asal_set_kartu[kartu_ringkas["id"]] = id_set

        # Langkah 2: Unduh detail lengkap setiap kartu secara bersamaan
        daftar_tugas_kartu = {}
        for id_kartu in asal_set_kartu:
            tugas = tim_pekerja.submit(ambil_json_dari_internet, f"cards/{quote(id_kartu)}")
            daftar_tugas_kartu[tugas] = id_kartu

        total_kartu = len(daftar_tugas_kartu)
        jumlah_selesai = 0

        for tugas in as_completed(daftar_tugas_kartu):
            id_kartu = daftar_tugas_kartu[tugas]
            id_set = asal_set_kartu[id_kartu]
            jumlah_selesai = jumlah_selesai + 1

            # Perbarui batang kemajuan (progress bar) setiap 50 kartu
            if fungsi_progres and jumlah_selesai % 50 == 0:
                fungsi_progres(jumlah_selesai, total_kartu, f"kartu {jumlah_selesai}/{total_kartu}")

            try:
                data_mentah = tugas.result()
            except RuntimeError:
                gagal_sebagian.add(id_set)
                continue

            if data_mentah:
                kartu_bersih = rapikan_data_kartu(data_mentah)
                if kartu_bersih:
                    hasil_per_set[id_set].append(kartu_bersih)

    return hasil_per_set, tidak_ketemu, sorted(gagal_sebagian)

"""
Memuat semua kartu dari daftar yang diconfig
Set yang sudah ada di file cache langsung dibaca dari komputer
Set yang belum ada akan diunduh dari internet lalu disimpan ke cache
"""
def muat_semua_kartu(fungsi_progres=None):
    semua_kartu = {}
    set_perlu_diunduh = []

    # Langkah 1: Cek satu per satu apakah sudah tersimpan di cache komputer
    for id_set in DAFTAR_SET_KARTU:
        kartu_dari_cache = baca_cache_set(id_set)
        if kartu_dari_cache is None:
            set_perlu_diunduh.append(id_set)
        else:
            for kartu in kartu_dari_cache:
                semua_kartu[kartu["id"]] = kartu

    # Langkah 2: Jika ada set yang belum punya cache, unduh dari internet
    catatan = []
    if set_perlu_diunduh:
        hasil_unduh, tidak_ketemu, gagal_sebagian = unduh_banyak_set_kartu(
            set_perlu_diunduh,
            fungsi_progres,
        )

        for id_set, daftar_kartu in hasil_unduh.items():
            for kartu in daftar_kartu:
                semua_kartu[kartu["id"]] = kartu

            # Hanya simpan ke cache kalau tidak ada kartu yang gagal diunduh
            if id_set not in gagal_sebagian:
                simpan_cache_set(id_set, daftar_kartu)

        jumlah_sukses = len(set_perlu_diunduh) - len(tidak_ketemu)
        catatan.append(f"{jumlah_sukses} set baru diambil dari API.")

        if tidak_ketemu:
            catatan.append("Set tidak ditemukan di TCGdex: " + ", ".join(tidak_ketemu))
        if gagal_sebagian:
            catatan.append(
                "Sebagian kartu gagal diambil (dicoba lagi nanti): " + ", ".join(gagal_sebagian)
            )

    if not semua_kartu:
        raise RuntimeError(
            "Tidak ada kartu yang berhasil dimuat. Periksa koneksi internet, CARD_API_URL, dan CARD_SETS."
        )

    catatan.insert(0, f"{len(semua_kartu)} kartu dari {len(DAFTAR_SET_KARTU)} set.")
    return semua_kartu, catatan

