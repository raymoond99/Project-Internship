from pathlib import Path
import re
import pandas as pd


class SaringDataManual:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
        
        target_dir = self.base_dir / "Data" / "Manual dan Apify"
        if not target_dir.exists():
            target_dir = self.base_dir / "Manual dan Apify"
        if not target_dir.exists():
            target_dir = self.base_dir

        self.data_dir = target_dir
        self.file_manual = self.data_dir / "raw_data_manual.xlsx"
        self.file_apify1 = self.data_dir / "raw_data_apify_1.csv"
        self.file_apify2 = self.data_dir / "raw_data_apify_2.csv"
        
        self.output_file = self.data_dir / "Target_Manual_Review50.xlsx"

    @staticmethod
    def _bersihkan_angka_ulasan(val):
        if pd.isna(val):
            return 0
        val_str = str(val).strip().lower()

        if '<' in val_str:
            return 0
        if val_str.endswith('.0'):
            val_str = val_str[:-2]
        if '50+' in val_str:
            return 50

        nums = re.findall(r'\d+', val_str)
        if nums:
            return int(nums[0])
        return 0

    @staticmethod
    def _perbaiki_rating_tanggal(val):
        """🔥 Ini obatnya! Ngubah 2026-05-04 balik jadi 4.5"""
        if pd.isna(val):
            return val
            
        # Kalau pandas keburu ngebaca jadi format waktu (Timestamp)
        if isinstance(val, pd.Timestamp) or type(val).__name__ == 'datetime':
            return f"{val.day}.{val.month}"
            
        val_str = str(val).strip()
        
        # Kalau formatnya string '2026-05-04 00:00:00'
        if "00:00:00" in val_str or re.match(r'\d{4}-\d{2}-\d{2}', val_str):
            try:
                parts = val_str.split()[0].split('-')
                # Balik dari YYYY-MM-DD jadi DD.MM (Contoh: 2026-05-04 -> 4.5)
                return f"{int(parts[2])}.{int(parts[1])}"
            except Exception:
                pass
                
        # Kalau ratingnya 5.0 atau 4.0 dibikin bulat aja
        if val_str.endswith(".0") and len(val_str) > 2:
            return val_str[:-2]
            
        return val_str

    @staticmethod
    def _normalisasi_nama(teks):
        return re.sub(r'\s+', ' ', re.sub(r'[^a-zA-Z0-9\s]', '', str(teks).lower())).strip()

    def ambil_peta_url_apify(self):
        if not self.file_apify1.exists() or not self.file_apify2.exists():
            return {}

        df1 = pd.read_csv(self.file_apify1, low_memory=False)
        df2 = pd.read_csv(self.file_apify2, low_memory=False)
        df_apify = pd.concat([df1, df2], ignore_index=True)

        df_clean = df_apify[['title', 'url']].dropna(subset=['url']).drop_duplicates(subset=['title'])

        peta_url = {}
        for _, row in df_clean.iterrows():
            nama_bersih = self._normalisasi_nama(row['title'])
            if len(nama_bersih) >= 3:
                peta_url[nama_bersih] = row['url']

        return peta_url

    def run(self):
        print(f"Membaca berkas manual: {self.file_manual.name}")
        if not self.file_manual.exists():
            return

        df_manual = pd.read_excel(self.file_manual)
        
        # 🔥 Panggil fungsi perbaikannya di sini
        if 'Rating_GMaps' in df_manual.columns:
            print("🔧 Memperbaiki bug tanggal pada Rating_GMaps...")
            df_manual['Rating_GMaps'] = df_manual['Rating_GMaps'].apply(self._perbaiki_rating_tanggal)

        df_manual['Review_3Bulan_Angka'] = df_manual['Review_Tiga_Bulan'].apply(self._bersihkan_angka_ulasan)
        df_filtered = df_manual[df_manual['Review_3Bulan_Angka'] >= 50].copy()

        peta_apify = self.ambil_peta_url_apify()

        df_filtered['URL_Maps_Apify'] = pd.NA
        for idx, row in df_filtered.iterrows():
            nama_clean = self._normalisasi_nama(str(row['Nama_Resto']).strip())

            if nama_clean in peta_apify:
                df_filtered.at[idx, 'URL_Maps_Apify'] = peta_apify[nama_clean]
            else:
                for apify_name, url in peta_apify.items():
                    if len(apify_name) >= 5 and (nama_clean in apify_name or apify_name in nama_clean):
                        df_filtered.at[idx, 'URL_Maps_Apify'] = url
                        break

        df_filtered['Review_Tiga_Bulan'] = df_filtered['Review_3Bulan_Angka']
        df_filtered.drop(columns=['Review_3Bulan_Angka'], inplace=True)

        # Simpan hasil yang sudah waras
        df_filtered.to_excel(self.output_file, index=False)
        print(f"✅ Berhasil! File yang ratingnya udah nggak gila tersimpan di: {self.output_file.name}")


if __name__ == "__main__":
    app = SaringDataManual()
    app.run()