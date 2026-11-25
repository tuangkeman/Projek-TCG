import random

def weighted_random(daftar_pilihan, daftar_bobot, pengacak=None):
    """
    Memilih 1 item secara acak sesuai besar bobot peluangnya.

    Analogi sehari-hari:
    Seperti roda undian (wheel of fortune) yang ukuran potongannya beda-beda.
    Rarity 'Common' punya potongan roda sangat lebar, sedangkan 'Legendary'
    potongannya sangat sempit sehingga jarang terkena jarum undian.
    """
    if not daftar_pilihan or len(daftar_pilihan) != len(daftar_bobot):
        raise ValueError("Daftar pilihan dan bobot harus sama panjang dan tidak boleh kosong.")

    if pengacak is None:
        pengacak = random

    # Langkah 1: Jumlahkan bobot secara bertahap untuk membuat garis batas tiap potongan
    # Contoh: bobot [10, 30, 60] -> batas [10, 40, 100]
    garis_batas = []
    total_bobot = 0.0
    for bobot in daftar_bobot:
        if bobot < 0:
            raise ValueError("Bobot peluang tidak boleh bernilai negatif.")
        total_bobot = total_bobot + bobot
        garis_batas.append(total_bobot)

    if total_bobot <= 0:
        raise ValueError("Total semua bobot harus lebih besar dari 0.")

    # Langkah 2: Putar roda undian (ambil angka acak antara 0 sampai total_bobot)
    jarum_undian = pengacak.random() * total_bobot

    # Langkah 3: Cari di potongan mana jarum mendarat menggunakan Binary Search
    kiri = 0
    kanan = len(garis_batas) - 1
    while kiri < kanan:
        tengah = (kiri + kanan) // 2
        if garis_batas[tengah] > jarum_undian:
            kanan = tengah
        else:
            kiri = tengah + 1

    return daftar_pilihan[kiri]


def fisher_yates_shuffle(daftar_data, pengacak=None):
    """
    Mengocok urutan daftar secara acak dan adil (algoritma Fisher-Yates).

    Analogi sehari-hari:
    Berjalan dari kartu paling belakang ke depan. Untuk setiap posisi,
    pilih satu kartu acak dari sisa kartu di depannya lalu tukar tempatnya.
    Daftar aslinya tidak rusak karena yang dikocok adalah salinannya.
    """
    if pengacak is None:
        pengacak = random

    hasil_kocok = list(daftar_data)

    for posisi_belakang in range(len(hasil_kocok) - 1, 0, -1):
        posisi_acak = pengacak.randint(0, posisi_belakang)

        # Tukar posisi kedua kartu
        sementara = hasil_kocok[posisi_belakang]
        hasil_kocok[posisi_belakang] = hasil_kocok[posisi_acak]
        hasil_kocok[posisi_acak] = sementara

    return hasil_kocok