import pandas as pd
from pathlib import Path

class PembersihDataApify:
    def __init__(self):
        # Jalur pintar: nyari file di mana pun kamu naruhnya (di root atau di folder Data)
        self.base_dir = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
        
        target_dir = self.base_dir / "Data" / "Manual dan Apify"
        if not target_dir.exists():
            target_dir = self.base_dir / "Data"
        if not target_dir.exists():
            target_dir = self.base_dir

        self.input_file = target_dir / "Hasil_Scraping_Apify_Lengkap.xlsx"
        self.output_file = target_dir / "Apify_Bersih.xlsx"

    def proses(self):
        print(f"🚀 Membaca data kotor dari: {self.input_file.name}")
        if not self.input_file.exists():
            print("❌ Waduh, file-nya nggak ketemu! Pastikan namanya udah bener ya.")
            return

        # 1. BACA DATA
        df = pd.read_excel(self.input_file)
        total_awal = len(df)
        print(f"Total data awal: {total_awal} restoran")

        # 2. BERSIHKAN ANGKA (Jaga-jaga ada teks 'ERROR' atau 'GAGAL SORTIR')
        kolom_rev = 'Review_3_Bulan_Asli' if 'Review_3_Bulan_Asli' in df.columns else 'Review_3_Bulan'
        df['Review_Num'] = pd.to_numeric(df[kolom_rev], errors='coerce').fillna(0)
        df['Komp_30_Num'] = pd.to_numeric(df['Komplain_30Hari'], errors='coerce').fillna(0)
        df['Komp_90_Num'] = pd.to_numeric(df['Komplain_90Hari'], errors='coerce').fillna(0)
        
        df['Total_Komplain'] = df['Komp_30_Num'] + df['Komp_90_Num']

        # 3. KASIH SKOR/LABEL
        def beri_label(baris):
            rev = baris['Review_Num']
            komp = baris['Total_Komplain']
            if rev >= 50 and komp >= 2: return "SANGAT SESUAI 🔥"
            elif rev >= 50 and komp == 1: return "SESUAI ⭐"
            elif rev >= 50 and komp == 0: return "POTENSIAL 💡"
            else: return "KURANG SESUAI 👎"

        df['Label_Prioritas'] = df.apply(beri_label, axis=1)

        # ========================================================
        # 4. EKSEKUSI PEMBANTAIAN DATA SAMPAH (DROP)
        # ========================================================
        print("\n🔪 Membuang data yang 'KURANG SESUAI 👎' ...")
        df_bersih = df[df['Label_Prioritas'] != "KURANG SESUAI 👎"].copy()
        
        total_akhir = len(df_bersih)
        total_dibuang = total_awal - total_akhir

        # 5. URUTKAN YANG PALING HOT DI ATAS
        sort_map = {"SANGAT SESUAI 🔥": 1, "SESUAI ⭐": 2, "POTENSIAL 💡": 3}
        df_bersih['Urutan'] = df_bersih['Label_Prioritas'].map(sort_map)
        df_bersih = df_bersih.sort_values(by=['Urutan', 'Total_Komplain', 'Review_Num'], ascending=[True, False, False])

        # 6. RAPIKAN KOLOM
        kolom_hapus = ['Review_Num', 'Komp_30_Num', 'Komp_90_Num', 'Urutan']
        df_bersih.drop(columns=kolom_hapus, inplace=True, errors='ignore')

        cols = df_bersih.columns.tolist()
        for col in ['Total_Komplain', 'Label_Prioritas', 'Kontak_WA']:
            if col in cols:
                cols.insert(2, cols.pop(cols.index(col)))

        # 7. SIMPAN HASIL BERSIH
        df_bersih.to_excel(self.output_file, index=False)

        print("="*50)
        print("🎉 LAPORAN CUCI GUDANG APIFY 🎉")
        print("="*50)
        print(f"🗑️ Data yang berhasil dibuang : {total_dibuang} restoran rongsok")
        print(f"💎 Sisa data berlian          : {total_akhir} target valid")
        print("\nDistribusi Sisa Data:")
        print(df_bersih['Label_Prioritas'].value_counts().to_string())
        print("="*50)
        print(f"✅ Mantap! File bersih disimpan di: {self.output_file.name}")

if __name__ == "__main__":
    app = PembersihDataApify()
    app.proses()