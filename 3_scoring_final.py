import pandas as pd
import re
from pathlib import Path

class ScoringLeadsFinal:
    def __init__(self, input_file="Master_Rekomendasi_Clean.xlsx", output_file="Skor_Final_V2.xlsx"):
        # Deteksi otomatis folder 'Data'
        self.base_dir = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
        self.data_dir = self.base_dir / "Data"
        if not self.data_dir.exists():
            self.data_dir = self.base_dir 
            
        self.input_path = self.data_dir / input_file
        self.output_path = self.data_dir / output_file
        self.df = None

    def load_data(self):
        print(f"🚀 Membaca data bersih dari: {self.input_path.name}...")
        try:
            # dtype string mencegah WA berubah jadi desimal/float
            self.df = pd.read_excel(self.input_path, dtype={'Nomor_WA': str})
            return True
        except FileNotFoundError:
            print(f"❌ Error: Berkas {self.input_path.name} tidak ditemukan di folder Data!")
            return False

    def _kalkulasi_skor(self, row):
        skor = 0
        
        # 1. Target Skala (1-5 Outlet & Bukan Franchise)
        if (1 <= row.get('Jumlah_Outlet', 0) <= 5) and (row.get('Franchise', 0) == 0):
            skor += 15
            
        # 2. Range Harga (Irisan dengan Rp 15.000 - 80.000)
        harga_str = str(row.get('Range_Harga', ''))
        angka = [int(x) for x in re.findall(r'\d+', harga_str.replace('.', ''))]
        if len(angka) >= 2:
            min_h, max_h = angka[0], angka[-1]
            if not (max_h < 15000 or min_h > 80000):
                skor += 10
                
        # 3. Operasional & Fasilitas Kompleks
        if row.get('Ada_Meja_DineIn', 0) == 1: 
            skor += 7.5
        if '>15' in str(row.get('Jumlah_Varian_Menu', '')): 
            skor += 7.5
            
        # 4. Aktivitas Digital
        if row.get('IG_Aktif_Promo', 0) == 1: skor += 5
        if row.get('Tiktok_Aktif_Promo', 0) == 1: skor += 5
            
        # 5. Urgensi / Pain Point (Sang Penentu Prioritas)
        komplain = pd.to_numeric(row.get('Total_Indikasi_Komplain_Operasional_Tiga_Bulan', 0), errors='coerce')
        if pd.notna(komplain) and komplain > 0:
            skor += (komplain * 25)
            
        return skor

    def _tentukan_label(self, skor):
        if skor >= 70: return "HOT LEADS 🔥"
        elif skor >= 40: return "WARM LEADS ⭐"
        else: return "COLD LEADS 💡"

    def proses(self):
        print("⚙️ Menerapkan Algoritma Scoring Tingkat Lanjut...")
        
        self.df['Total_Skor'] = self.df.apply(self._kalkulasi_skor, axis=1)
        self.df['Label_Prioritas'] = self.df['Total_Skor'].apply(self._tentukan_label)
        
        # Mapping urutan untuk sorting absolut
        sort_map = {"HOT LEADS 🔥": 1, "WARM LEADS ⭐": 2, "COLD LEADS 💡": 3}
        self.df['Urutan'] = self.df['Label_Prioritas'].map(sort_map)
        
        # Pengurutan Final: Label -> Skor -> Komplain -> Review
        self.df = self.df.sort_values(
            by=['Urutan', 'Total_Skor', 'Total_Indikasi_Komplain_Operasional_Tiga_Bulan', 'Review_Tiga_Bulan'], 
            ascending=[True, False, False, False]
        )
        self.df.drop(columns=['Urutan'], inplace=True, errors='ignore')
        
        # Geser kolom Label dan Skor ke depan supaya langsung terlihat oleh Sales
        cols = self.df.columns.tolist()
        cols.insert(2, cols.pop(cols.index('Label_Prioritas')))
        cols.insert(3, cols.pop(cols.index('Total_Skor')))
        self.df = self.df[cols]
        
        self.df.to_excel(self.output_path, index=False)
        
        print("\n" + "="*50)
        print("📊 LAPORAN DISTRIBUSI LEADS FINAL")
        print("="*50)
        print(self.df['Label_Prioritas'].value_counts().to_string())
        print("="*50)
        print(f"\n✅ File matang siap masuk Dashboard! Tersimpan di: {self.output_path.name}")

if __name__ == "__main__":
    bot = ScoringLeadsFinal()
    if bot.load_data():
        bot.proses()