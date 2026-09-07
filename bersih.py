import pandas as pd
import re
from pathlib import Path

class DataCleaner:
    def __init__(self, input_file="Rekomendasi Target.xlsx", output_file="Master_Rekomendasi_Clean.xlsx"):
        # Deteksi otomatis lokasi skrip berjalan
        self.base_dir = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
        
        # Mengunci direktori ke folder 'Data'
        self.data_dir = self.base_dir / "Data"
        if not self.data_dir.exists():
            self.data_dir = self.base_dir  # Fallback jika dijalankan langsung dari dalam Data
            
        self.input_path = self.data_dir / input_file
        self.output_path = self.data_dir / output_file
        self.df = None

    def load_data(self):
        print(f"📥 Membaca data dari: {self.input_path}...")
        try:
            self.df = pd.read_excel(self.input_path)
            return True
        except FileNotFoundError:
            print(f"❌ Error: Berkas {self.input_path.name} tidak ditemukan di folder Data!")
            return False

    def _bersihkan_data(self):
        print("🧹 Membersihkan ranjau data...")

        # 1. CLEANING NAMA RESTO (Buang enter \n dan spasi depan-belakang)
        self.df['Nama_Resto'] = self.df['Nama_Resto'].astype(str).str.replace('\n', '').str.strip()

        # 2. CLEANING RANGE HARGA
        def bersihkan_harga(harga):
            if pd.isna(harga) or harga == 'nan':
                return "Tidak Diketahui"
            
            harga_str = str(harga).lower()
            
            # Ambil semua angka murni dari teks
            angka_ditemukan = re.findall(r'\d+', harga_str.replace('.', ''))
            
            # Jika ditemukan minimal 2 angka (min dan max)
            if len(angka_ditemukan) >= 2:
                min_h = int(angka_ditemukan[0])
                max_h = int(angka_ditemukan[-1]) # Ambil angka terakhir jika formatnya aneh
                
                # Perbaikan untuk anomali "1-25.000" jadi "1000-25000"
                if min_h < 100:  
                    min_h *= 1000
                    
                # Format ulang menjadi rapi dan standar
                return f"Rp{min_h:,.0f} - Rp{max_h:,.0f}".replace(',', '.')
            return str(harga)

        self.df['Range_Harga'] = self.df['Range_Harga'].apply(bersihkan_harga)

        # 3. CLEANING NOMOR WHATSAPP (Sisakan Angka Murni)
        self.df['Nomor_WA'] = self.df['Nomor_WA'].astype(str).str.replace(r'\D', '', regex=True)
        self.df['Nomor_WA'] = self.df['Nomor_WA'].replace('', 'Tidak Ada')

        # 4. HANDLE MISSING VALUES (Nilai Kosong)
        cols_to_fill = ['IG_Aktif_Promo', 'Tiktok_Aktif_Promo', 'Total_Indikasi_Komplain_Operasional_Tiga_Bulan']
        for col in cols_to_fill:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna(0)

        # 5. STANDARISASI KATEGORI (Hapus spasi gaib)
        self.df['Kategori'] = self.df['Kategori'].astype(str).str.strip()
        
        print("✨ Data berhasil dicuci bersih!")

    def proses_bersih(self):
        self._bersihkan_data()
        # Simpan hasilnya kembali ke folder Data
        self.df.to_excel(self.output_path, index=False)
        print(f"✅ Data bersih matang tersimpan di: {self.output_path}")

if __name__ == "__main__":
    cleaner = DataCleaner()
    if cleaner.load_data():
        cleaner.proses_bersih()