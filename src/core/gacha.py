import random

from .algoritma import fisher_yates_shuffle, weighted_random

HARGA_TARIK_1X = 100 
HARGA_TARIK_5X = 450  


def ambil_bobot_rarity(rarity):
    teks = rarity.lower()

    if teks == "legendary":
        return 1

    for kata_super_langka in ("secret", "rainbow", "hyper", "special illustration"):
        if kata_super_langka in teks:
            return 0.5

    for kata_sangat_langka in ("ultra", "illustration", "vmax", "vstar", " ex", " gx", "legend", "radiant"):
        if kata_sangat_langka in teks:
            return 1.5

    if "holo" in teks or "double" in teks:
        return 4
    if "uncommon" in teks:
        return 28
    if "common" in teks:
        return 55
    if "promo" in teks:
        return 5

    return 10


def ambil_peringkat_rarity(rarity):
    bobot = ambil_bobot_rarity(rarity)
    if bobot >= 55:
        return 0
    if bobot >= 28:
        return 1
    if bobot >= 10:
        return 2
    if bobot >= 5:
        return 3
    if bobot >= 1.5:
        return 4
    return 5


def kelompokkan_kartu_per_rarity(daftar_kartu):
    kelompok = {}
    for kartu in daftar_kartu:
        rarity = kartu["rarity"]
        if rarity not in kelompok:
            kelompok[rarity] = []
        kelompok[rarity].append(kartu)
    return kelompok


def tarik_kartu_gacha(daftar_kartu, jumlah_tarik, shuffler=None):
    """
    Menarik sejumlah kartu secara acak:
    Langkah 1: Kelompokkan kartu berdasarkan rarity-nya.
    Langkah 2: Undi dulu rarity mana yang keluar (pakai roda undian berbobot).
    Langkah 3: Kocok semua kartu di rarity terpilih, lalu ambil kartu teratas.
    """
    if not daftar_kartu:
        raise ValueError("Kumpulan kartu untuk gacha masih kosong.")

    if shuffler is None:
        shuffler = random

    kelompok = kelompokkan_kartu_per_rarity(daftar_kartu)
    daftar_rarity = list(kelompok.keys())

    daftar_bobot = []
    for rarity in daftar_rarity:
        daftar_bobot.append(ambil_bobot_rarity(rarity))

    hasil_tarikan = []
    for _ in range(jumlah_tarik):
        rarity_terpilih = weighted_random(daftar_rarity, daftar_bobot, shuffler)
        kartu_di_rarity = kelompok[rarity_terpilih]
        kartu_dikocok = fisher_yates_shuffle(kartu_di_rarity, shuffler)
        hasil_tarikan.append(kartu_dikocok[0])

    return hasil_tarikan


def ambil_persen_peluang(baris):
    return -baris["Peluang (%)"]


def tabel_peluang_gacha(daftar_kartu):
    kelompok = kelompokkan_kartu_per_rarity(daftar_kartu)

    total_bobot = 0.0
    for rarity in kelompok:
        total_bobot = total_bobot + ambil_bobot_rarity(rarity)

    daftar_baris = []
    for nama_rarity, isi_kelompok in kelompok.items():
        bobot = ambil_bobot_rarity(nama_rarity)
        persen = round((bobot / total_bobot) * 100, 1)

        daftar_baris.append({
            "Rarity": nama_rarity,
            "Jumlah kartu": len(isi_kelompok),
            "Peluang (%)": persen,
        })

    daftar_baris.sort(key=ambil_persen_peluang)
    return daftar_baris