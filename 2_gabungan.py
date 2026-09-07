import pandas as pd
import re
from pathlib import Path

class PenggabungFinal:
    def __init__(self):
        # Deteksi otomatis folder kerja
        self.base_dir = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
        
        target_dir = self.base_dir / "Data" / "Manual dan Apify"
        if not target_dir.exists():
            target_dir = self.base_dir / "Data"
        if not target_dir.exists():
            target_dir = self.base_dir

        # Nama file sesuai yang kamu berikan
        self.file_manual = target_dir / "Hasil_Scraping_Manual_Lengkap.xlsx"
        self.file_apify = target_dir / "Apify_Bersih.xlsx"
        self.output_file = target_dir / "Rekomendasi_Target_Final.xlsx"
        
        # Urutan kolom mutlak sesuai permintaan
        self.kolom_wajib = [
            'ID_Lead', 'Nama_Resto', 'Jumlah_Outlet', 'IG_Aktif_Promo', 'Rating_GMaps', 
            'Jumlah_Review', 'Review_Tiga_Bulan', 'Tiktok_Aktif_Promo', 'Kategori', 
            'Franchise', 'URL_Maps_Apify', 'Review_3_Bulan_Asli', 'Komplain_30Hari', 
            'Komplain_90Hari', 'Kontak_WA', 'Latitude', 'Longitude'
        ]

    @staticmethod
    def _normalisasi_nama(nama):
        """Membuang karakter aneh dan spasi agar pencarian duplikat 100% akurat"""
        return re.sub(r'[^a-zA-Z0-9]', '', str(nama).lower())

    def proses(self):
        print("🚀 Membaca file Manual dan Apify...")
        
        if not self.file_manual.exists():
            print(f"❌ Error: {self.file_manual.name} tidak ditemukan!")
            return
        if not self.file_apify.exists():
            print(f"❌ Error: {self.file_apify.name} tidak ditemukan!")
            return

        # 1. Baca Data
        df_manual = pd.read_excel(self.file_manual)
        df_apify = pd.read_excel(self.file_apify)
        
        print(f"Data Manual : {len(df_manual)} baris")
        print(f"Data Apify  : {len(df_apify)} baris")

        # 2. Selaraskan nama kolom Apify agar sama dengan Manual
        rename_api = {
            'URL_Maps': 'URL_Maps_Apify',
            'Total_Review_Apify': 'Jumlah_Review',
            'Rating_Apify': 'Rating_GMaps'
        }
        df_apify.rename(columns=rename_api, inplace=True, errors='ignore')

        # 3. Buat kunci pencarian untuk deteksi duplikat
        df_manual['Key_Nama'] = df_manual['Nama_Resto'].apply(self._normalisasi_nama)
        df_apify['Key_Nama'] = df_apify['Nama_Resto'].apply(self._normalisasi_nama)

        # 4. Cari Irisan (Duplikat)
        set_manual = set(df_manual['Key_Nama'].dropna())
        set_apify = set(df_apify['Key_Nama'].dropna())
        irisan = set_manual.intersection(set_apify)

        print("\n" + "="*50)
        print(f"🔍 DITEMUKAN {len(irisan)} RESTORAN DUPLIKAT (ADA DI KEDUA FILE):")
        print("="*50)
        
        if len(irisan) > 0:
            nama_duplikat = df_manual[df_manual['Key_Nama'].isin(irisan)]['Nama_Resto'].unique()
            for idx, nama in enumerate(nama_duplikat, 1):
                print(f"{idx}. {nama}")
            print("\n*Catatan: Data duplikat dari Apify akan dihapus, prioritas pakai data Manual.*")
        else:
            print("Semua data unik, tidak ada yang tumpang tindih.")

        # 5. GABUNGKAN DATA (The Grand Merge)
        print("\n🔗 Menyatukan kedua file...")
        df_gabungan = pd.concat([df_manual, df_apify], ignore_index=True)
        
        # Buang duplikat, pertahankan data pertama (Manual)
        df_gabungan.drop_duplicates(subset=['Key_Nama'], keep='first', inplace=True)

        # 6. Pastikan 17 kolom wajib tersedia (isi Kosong / NaN kalau belum ada)
        for col in self.kolom_wajib:
            if col not in df_gabungan.columns:
                df_gabungan[col] = pd.NA
                
        # Potong dan urutkan hanya kolom yang direquest
        df_final = df_gabungan[self.kolom_wajib].copy()
        
        # 7. Simpan ke Excel
        df_final.to_excel(self.output_file, index=False)
        
        print("\n" + "="*50)
        print("🎉 PROSES PENGGABUNGAN SELESAI 🎉")
        print("="*50)
        print(f"Total Master Target Tergabung : {len(df_final)} restoran")
        print(f"Format Kolom                  : Tepat {len(self.kolom_wajib)} kolom")
        print(f"✅ File hasil tersimpan di    : {self.output_file.name}")


if __name__ == "__main__":
    app = PenggabungFinal()
    app.proses()