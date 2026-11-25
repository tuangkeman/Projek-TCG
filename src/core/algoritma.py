import random

def weighted_random(daftar_pilihan, daftar_bobot, shuffler=None):
    if not daftar_pilihan or len(daftar_pilihan) != len(daftar_bobot):
        raise ValueError("Daftar pilihan dan bobot harus sama panjang dan tidak boleh kosong.")

    if shuffler is None:
        shuffler = random

    garis_batas = []
    total_bobot = 0.0
    for bobot in daftar_bobot:
        if bobot < 0:
            raise ValueError("Bobot peluang tidak boleh bernilai negatif.")
        total_bobot = total_bobot + bobot
        garis_batas.append(total_bobot)

    if total_bobot <= 0:
        raise ValueError("Total semua bobot harus lebih besar dari 0.")

    random_num = shuffler.random() * total_bobot

    kiri = 0
    kanan = len(garis_batas) - 1
    while kiri < kanan:
        tengah = (kiri + kanan) // 2
        if garis_batas[tengah] > random_num:
            kanan = tengah
        else:
            kiri = tengah + 1

    return daftar_pilihan[kiri]


def fisher_yates_shuffle(daftar_data, shuffler=None):
    if shuffler is None:
        shuffler = random

    hasil_shuffle = list(daftar_data)

    for kartu_belakang in range(len(hasil_shuffle) - 1, 0, -1):
        posisi_acak = shuffler.randint(0, kartu_belakang)

        temp = hasil_shuffle[kartu_belakang]
        hasil_shuffle[kartu_belakang] = hasil_shuffle[posisi_acak]
        hasil_shuffle[posisi_acak] = temp


    return hasil_shuffle