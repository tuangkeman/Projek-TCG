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
from .config import SETKARTUREK, FOLDER_CACHE, ErrorKonfigurasi, ambil_alamat_api_kartu #ini nanti ambil dari config trus ambil fungsinya

JUMTHEARD = 32 #jumlah theard pararel maks

simpananKonek = threading.local() #Penyimpanan koneksi internet per pekerja supaya koneksi bisa dipakai berulang kali


"""
Mengambil (atau membuat baru) koneksi HTTP untuk mengunduh data dari internet
Kalau belum punya koneksi internet, buat dulu. Kalau sudah punya, pakai yang lama.
agar menghemat waktu saat unduh ribuan kartu
"""
def ambil_sesi_internet():
    sesi = getattr(simpananKonek, "sesi", None) #cek udah punya sesi?
    if sesi is None: #jika belum buat baru
        sesi = requests.Session() #nanti ini buat
        pengatur_koneksi = HTTPAdapter( #cara sesi mengelola koneksinya
            pool_connections=4,
            pool_maxsize=JUMTHEARD,
            max_retries=0,
        )
        sesi.mount("https://", pengatur_koneksi)
        sesi.mount("http://", pengatur_koneksi)
        sesi.headers.update({ #keterangan yang ikut terkirim di setiap permintaan
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "tcg-card-battle/0.1",
        })
        simpananKonek.sesi = sesi #sesinya disimpan
    return sesi 


"""
ambil data dari tcgdex kalo berhasil mengembalikan datanya
kalau alamat tidak ada (404), mengembalikan None
kalau gagal karena jaringan, mencoba ulang sampai 3 kali dengan jeda makin lama, 
lalu menyerah dengan RuntimeError
"""
def ambil_json_dari_internet(jalur, jumlah_coba_ulang=2):
    try:
        alamatAPII = ambil_alamat_api_kartu()
    except ErrorKonfigurasi as error:
        raise RuntimeError(str(error)) from error

    alamtLengkap = f"{alamatAPII}/{jalur}"

    for isi in range(jumlah_coba_ulang + 1):
        try:
            respon = ambil_sesi_internet().get(alamtLengkap, timeout=(5, 30))
            if respon.status_code == 404:
                return None
            respon.raise_for_status()
            return respon.json()
        except (requests.RequestException, ValueError) as error:
            if isi == jumlah_coba_ulang:
                raise RuntimeError(f"Gagal menghubungi TCGdex ({jalur}): {error}") from error
            time.sleep(0.8 * (isi + 1))
#-------------------------------------------
#bagian bawah ini nanti cache
"""Membuat nama file cache di komputer untuk sebuah set kartu."""
def lokasi_file_cache(id_set):
    namaSafe = re.sub(r"[^A-Za-z0-9._-]", "_", id_set)
    return FOLDER_CACHE / f"set_{namaSafe}.json"


"""Membaca daftar kartu satu set dari komputer. Mengembalikan None jika belum ada."""
def baca_cache_set(id_set):
    try:
        isiTek = lokasi_file_cache(id_set).read_text(encoding="utf-8")
        daftarKart = json.loads(isiTek)
    except (OSError, ValueError):
        return None

    if not isinstance(daftarKart, list):
        return None

    # sort kartu hanya pakai kartu yang ada gambarnya dan kelangkaannya diizinkan
    kartuSort = []
    for kartu in daftarKart:
        if kartu.get("image") and apakah_rarity_diizinkan(kartu.get("rarity")):
            kartuSort.append(kartu)
    return kartuSort


"""Menyimpan daftar kartu satu set ke file cache secara aman."""
def simpan_cache_set(id_set, daftar_kartu):
    lok = lokasi_file_cache(id_set)
    lok.parent.mkdir(parents=True, exist_ok=True)

    fileSem = lok.with_suffix(".tmp")
    teksJso = json.dumps(daftar_kartu, ensure_ascii=False, separators=(",", ":"))
    fileSem.write_text(teksJso, encoding="utf-8")
    fileSem.replace(lok)

#------------------------------
#bagian bawah ini nanti unduh 
"""
Mengunduh semua kartu dari beberapa set sekaligus menggunakan banyak pekerja paralel.
Mengembalikan 3 hal:
hasilSet : kamus {kode_set: [daftar_kartu]}
tidakKetemu   : daftar kode set yang tidak ada di situs TCGdex
gagal: daftar kode set yang sebagian kartunya gagal diunduh
"""
def unduh_banyak_set_kartu(daftar_id_set, fungsi_progres=None):
    hasilSet = {}
    tidakKetemu = []
    gagal = set()

    with ThreadPoolExecutor(max_workers=JUMTHEARD) as theardKerja:
        # Langkah 1: Minta daftar ID kartu yang ada di tiap set
        daftarTSET = {}
        for idSet in daftar_id_set:
            tugas = theardKerja.submit(ambil_json_dari_internet, f"sets/{quote(idSet)}")
            daftarTSET[tugas] = idSet

        catatAsalID = {}  # Mencatat setiap ID kartu berasal dari set mana

        for tugas in as_completed(daftarTSET):
            idSet = daftarTSET[tugas]
            inforSET = tugas.result()

            if not inforSET or not inforSET.get("cards"):
                tidakKetemu.append(idSet)
                continue

            hasilSet[idSet] = []
            for ringkasKart in inforSET["cards"]:
                catatAsalID[ringkasKart["id"]] = idSet

        # Langkah 2: Unduh detail lengkap setiap kartu secara bersamaan
        daftarTugasKartu = {}
        for idKartu in catatAsalID:
            tugas = theardKerja.submit(ambil_json_dari_internet, f"cards/{quote(idKartu)}")
            daftarTugasKartu[tugas] = idKartu

        totalKartu = len(daftarTugasKartu)
        jumlahSelesai = 0

        for tugas in as_completed(daftarTugasKartu):
            idKartu = daftarTugasKartu[tugas]
            idSet = catatAsalID[idKartu]
            jumlahSelesai = jumlahSelesai + 1

            # Perbarui batang kemajuan (progress bar) setiap 50 kartu
            if fungsi_progres and jumlahSelesai % 50 == 0:
                fungsi_progres(jumlahSelesai, totalKartu, f"kartu {jumlahSelesai}/{totalKartu}")

            try:
                dataMentah = tugas.result()
            except RuntimeError:
                gagal.add(idSet)
                continue

            if dataMentah:
                kartuBersih = rapikan_data_kartu(dataMentah)
                if kartuBersih:
                    hasilSet[idSet].append(kartuBersih)

    return hasilSet, tidakKetemu, sorted(gagal)

"""
Memuat semua kartu dari daftar yang diconfig
Set yang sudah ada di file cache langsung dibaca dari komputer
Set yang belum ada akan diunduh dari internet lalu disimpan ke cache
"""
def muat_semua_kartu(fungsi_progres=None):
    semuaKartu = {}
    setPerluDiunduh = []

    # Langkah 1: Cek satu per satu apakah sudah tersimpan di cache komputer
    for idSet in SETKARTUREK:
        kartuDariCache = baca_cache_set(idSet)
        if kartuDariCache is None:
            setPerluDiunduh.append(idSet)
        else:
            for kartu in kartuDariCache:
                semuaKartu[kartu["id"]] = kartu

    # Langkah 2: Jika ada set yang belum punya cache, unduh dari internet
    catatan = []
    if setPerluDiunduh:
        hasilUnduh, tidakKetemu, gagal = unduh_banyak_set_kartu(
            setPerluDiunduh,
            fungsi_progres,
        )

        for idSet, daftarKartu in hasilUnduh.items():
            for kartu in daftarKartu:
                semuaKartu[kartu["id"]] = kartu

            # Hanya simpan ke cache kalau tidak ada kartu yang gagal diunduh
            if idSet not in gagal:
                simpan_cache_set(idSet, daftarKartu)

        jumlahSukses = len(setPerluDiunduh) - len(tidakKetemu)
        catatan.append(f"{jumlahSukses} set baru diambil dari API.")

        if tidakKetemu:
            catatan.append("Set tidak ditemukan di TCGdex: " + ", ".join(tidakKetemu))
        if gagal:
            catatan.append(
                "Sebagian kartu gagal diambil (dicoba lagi nanti): " + ", ".join(gagal)
            )

    if not semuaKartu:
        raise RuntimeError(
            "Tidak ada kartu yang berhasil dimuat. Periksa koneksi internet, CARD_API_URL, dan CARD_SETS."
        )

    catatan.insert(0, f"{len(semuaKartu)} kartu dari {len(SETKARTUREK)} set.")
    return semuaKartu, catatan

