# import csv
# import io
import json

BATAS_KARTU_DECK = 6  # Maksimal 6 kartu di dalam 1 deck
KOIN_AWAL = 500

class ProgresPemain:
    """Menyimpan dan mengelola seluruh data kemajuan satu orang pemain."""

    def __init__(
        self,
        koin=KOIN_AWAL,
        koleksi=None,
        deck=None,
        riwayat_gacha=None,
        menang=0,
        kalah=0,
    ):
        self.koin = koin
        self.koleksi = koleksi if koleksi is not None else {}
        self.deck = deck if deck is not None else []
        self.riwayat_gacha = riwayat_gacha if riwayat_gacha is not None else []
        self.menang = menang
        self.kalah = kalah

    def tambah_kartu_hasil_gacha(self, daftar_kartu):
        """
        Memasukkan kartu hasil gacha ke koleksi pemain.
        Mengembalikan daftar berisi True/False:
        - True  artinya kartu itu baru pertama kali dimiliki pemain.
        - False artinya kartu itu sudah pernah dimiliki (duplikat).
        """
        daftar_status_baru = []

        for kartu in daftar_kartu:
            id_kartu = kartu["id"]
            apakah_baru = id_kartu not in self.koleksi
            daftar_status_baru.append(apakah_baru)

            jumlah_lama = self.koleksi.get(id_kartu, 0)
            self.koleksi[id_kartu] = jumlah_lama + 1
            self.riwayat_gacha.append(kartu["rarity"])

        return daftar_status_baru

    def hitung_jumlah_dimiliki(self, id_kartu):
        """Mengecek berapa lembar kartu tertentu yang dimiliki pemain."""
        return self.koleksi.get(id_kartu, 0)

    def cek_boleh_masuk_deck(self, id_kartu):
        """Mengecek apakah kartu ini masih boleh dimasukkan ke dalam deck."""
        if len(self.deck) >= BATAS_KARTU_DECK:
            return False, f"Deck penuh (maks {BATAS_KARTU_DECK} kartu)."

        sudah_dipakai = self.deck.count(id_kartu)
        jumlah_punya = self.hitung_jumlah_dimiliki(id_kartu)

        if sudah_dipakai >= jumlah_punya:
            return False, "Kamu tidak punya salinan lagi dari kartu ini."

        return True, ""

    def tambah_ke_deck(self, id_kartu):
        """Memasukkan 1 kartu ke deck jika syaratnya terpenuhi."""
        boleh, pesan = self.cek_boleh_masuk_deck(id_kartu)
        if boleh:
            self.deck.append(id_kartu)
        return boleh, pesan

    def hapus_dari_deck(self, nomor_urut):
        """Mengeluarkan kartu dari deck berdasarkan nomor urutannya."""
        if 0 <= nomor_urut < len(self.deck):
            self.deck.pop(nomor_urut)

    def ganti_seluruh_deck(self, daftar_id_kartu):
        """
        Mengganti seluruh isi deck sekaligus (misal dari rekomendasi AI atau impor file).
        Jika ada kartu yang tidak dimiliki atau melebihi batas 6 kartu, kartu itu dilewati.
        Mengembalikan daftar catatan kartu mana saja yang dilewati.
        """
        deck_baru = []
        daftar_dilewati = []

        for id_kartu in daftar_id_kartu:
            if len(deck_baru) >= BATAS_KARTU_DECK:
                daftar_dilewati.append(f"{id_kartu}: melebihi batas {BATAS_KARTU_DECK} kartu")
            elif deck_baru.count(id_kartu) >= self.hitung_jumlah_dimiliki(id_kartu):
                daftar_dilewati.append(f"{id_kartu}: tidak ada di koleksi")
            else:
                deck_baru.append(id_kartu)

        self.deck = deck_baru
        return daftar_dilewati

    def simpan_ke_file(self, lokasi_file):
        """Menyimpan seluruh data pemain ke dalam file JSON di komputer."""
        lokasi_file.parent.mkdir(parents=True, exist_ok=True)

        # Nama kunci JSON dipertahankan dalam bahasa Inggris agar file save lama tetap terbaca
        data_simpan = {
            "coins": self.koin,
            "collection": self.koleksi,
            "deck": self.deck,
            "pull_log": self.riwayat_gacha,
            "wins": self.menang,
            "losses": self.kalah,
        }
        teks_json = json.dumps(data_simpan, ensure_ascii=False, indent=2)
        lokasi_file.write_text(teks_json, encoding="utf-8")

    @classmethod
    def muat_dari_file(cls, lokasi_file):
        """Membaca data pemain dari file JSON. Jika belum ada file, buat progres baru."""
        try:
            isi_teks = lokasi_file.read_text(encoding="utf-8")
            data = json.loads(isi_teks)

            koleksi_rapi = {}
            for kunci, jumlah in data.get("collection", {}).items():
                koleksi_rapi[str(kunci)] = int(jumlah)

            deck_rapi = []
            for id_kartu in data.get("deck", [])[:BATAS_KARTU_DECK]:
                deck_rapi.append(str(id_kartu))

            riwayat_rapi = []
            for rarity in data.get("pull_log", []):
                riwayat_rapi.append(str(rarity))

            return cls(
                koin=int(data.get("coins", KOIN_AWAL)),
                koleksi=koleksi_rapi,
                deck=deck_rapi,
                riwayat_gacha=riwayat_rapi,
                menang=int(data.get("wins", 0)),
                kalah=int(data.get("losses", 0)),
            )
        except (OSError, ValueError, TypeError, AttributeError):
            # Jika file belum ada atau rusak, mulai progres baru dengan modal awal
            return cls()
