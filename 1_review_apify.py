from pathlib import Path
import re
import pandas as pd
from playwright.sync_api import sync_playwright

# ==========================================
# 1. PARAMETER FILTER DAN KOMPLAIN
# ==========================================
KEYWORDS_KOMPLAIN = [
    # --- MASALAH KECEPATAN & ANTRIAN ---
    "nunggu lama", "menunggu lama", "antre lama", "antrian lama", "antri lama", "ngantri lama", "uantrinyaa lama",
    "pelayanan lama", "proses lama", "penyajian lama", "pesanan lama", "kasir lama", "pelayanan lama", "penyajian makan terlalu lama"
    "makanan keluar lama", "datang lama", "penyajian telat", "pesanan telat", "penyajian minum terlalu lama", "penyajian minum lama", "penyajian makan lama"
    "nunggu 30 menit", "nunggu 45 menit", "nunggu 1 jam", "nunggu berjam-jam", "penyajian cukup lama", "nunggu makananya 1 jam", "kelupaan 1"
    "menunggu berjam", "lama tak dipanggil", "belum dipanggil",
    "datang duluan", "datang belakangan dilayani", "didahulukan", "disela",
    "padahal sepi", "gak ada antrian tapi", "gk ada antrian tapi",
    
    # --- MASALAH SISTEM & AKURASI PESANAN ---
    "sistem antrian kacau", "sistem pemesanan", "manajemen kacau",
    "kertas pesanan", "pesanan hilang", "belum pesan", "dilempar-lempar",
    "salah pesanan", "salah menu", "salah input", "salah harga", "salah hitung",
    "pesanan tertukar", "pesanan keliru", "kurang pesanan", "pesanan tidak sesuai",
    "nota salah", "struk salah", "kasir lambat", "kasir lelet", "sistem error",
    
    # --- MASALAH PELAYANAN UMUM & STOK ---
    "pelayanan buruk", "pelayanan mengecewakan", "pelayanan kurang baik", "pelayanan lelet",
    "stok habis", "menu habis", "bahan habis", "menu kosong", "banyak yang kosong", "sold out", "luama", "lelet", "suwe", "suwi",

    # 🔥 --- AMUNISI JUALAN AI POS (PRODUCT KNOWLEDGE & UPSELLING) --- 🔥
    "kasir tidak tahu menu", "kasir bingung", "kurang paham menu", "gatau menu",
    "ditanya menu bingung", "ditanya rekomendasi bingung", "tidak bisa merekomendasikan",
    "tidak tahu best seller", "kasir kurang edukasi", "pelayan tidak hafal menu", 
    "waitress bingung", "tidak paham menu", "kasir kurang paham", "kasirnya gatau",
    "sistem kasir", "mesin kasir"
]

BATAS_BERHENTI = [
    "4 month", "5 month", "6 month", "7 month", "8 month", "9 month", "year",
    "4 bulan", "5 bulan", "6 bulan", "7 bulan", "8 bulan", "9 bulan", "tahun", "setahun",
    "4 bln", "5 bln", "6 bln", "7 bln", "8 bln", "9 bln", "thn"
]

KATEGORI_MENENGAH = [
    "2 month", "3 month", "2 bulan", "3 bulan", "2 bln", "3 bln"
]

class BotScraperApify:
    def __init__(self, output_filename="Hasil_Scraping_Apify_Lengkap.xlsx"):
        self.base_dir = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
        
        target_dir = self.base_dir / "Data" / "Manual dan Apify"
        if not target_dir.exists():
            target_dir = self.base_dir / "Manual dan Apify"
        if not target_dir.exists():
            target_dir = self.base_dir

        self.data_dir = target_dir
        self.file_apify1 = self.data_dir / "raw_data_apify_1.csv"
        self.file_apify2 = self.data_dir / "raw_data_apify_2.csv"
        self.output_file = self.data_dir / output_filename
        self.profile_path = self.base_dir / "bot_profile"
        self.df = None

    def siapkan_data(self):
        print(f"Mencari berkas di: {self.data_dir}")

        if not self.file_apify1.exists() or not self.file_apify2.exists():
            print(f"Error: Berkas CSV tidak ditemukan di {self.data_dir}")
            return False

        df1 = pd.read_csv(self.file_apify1, low_memory=False)
        df2 = pd.read_csv(self.file_apify2, low_memory=False)
        df_raw = pd.concat([df1, df2], ignore_index=True)

        df_clean = df_raw[['title', 'url', 'reviewsCount', 'totalScore']].dropna(subset=['url']).copy()
        df_clean.rename(columns={
            'title': 'Nama_Resto',
            'url': 'URL_Maps',
            'reviewsCount': 'Total_Review_Apify',
            'totalScore': 'Rating_Apify'
        }, inplace=True)
        df_clean.drop_duplicates(subset=['Nama_Resto'], inplace=True)

        total_awal = len(df_clean)
        self.df = df_clean[df_clean['Total_Review_Apify'] >= 50].copy().reset_index(drop=True)

        # 🔥 TAMBAHAN: Siapkan kolom untuk Nomor WA dan Koordinat
        kolom_baru = ['Review_3_Bulan', 'Komplain_30Hari', 'Komplain_90Hari', 'Kontak_WA', 'Latitude', 'Longitude']
        for col in kolom_baru:
            if col not in self.df.columns:
                self.df[col] = pd.NA

        print(f"Total resto ber-URL     : {total_awal}")
        print(f"Target lolos (>= 50 rev): {len(self.df)} resto")
        return True

    def run(self):
        if not self.siapkan_data():
            return

        with sync_playwright() as p:
            print("\nMenjalankan Playwright...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_path),
                channel="chrome",
                headless=False,
                locale="id-ID",
                no_viewport=True,
                args=['--start-maximized', '--disable-blink-features=AutomationControlled']
            )
            page = context.pages[0]
            total = len(self.df)

            for index, row in self.df.iterrows():
                resto = row['Nama_Resto']
                url = row['URL_Maps']

                print(f"\n[{index + 1}/{total}] Mengorek: {resto}")

                try:
                    page.goto(url, timeout=60000, wait_until="domcontentloaded")
                    page.wait_for_timeout(4000)

                    # ==========================================
                    # 🔥 1. AMBIL KOORDINAT & NOMOR WA 🔥
                    # ==========================================
                    current_url = page.url
                    lat, lon, nomor = pd.NA, pd.NA, pd.NA
                    
                    # Ekstrak Koordinat
                    match_coords = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
                    if not match_coords:
                        match_coords = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', current_url)
                    if match_coords:
                        lat, lon = match_coords.group(1), match_coords.group(2)
                    
                    self.df.at[index, 'Latitude'] = lat
                    self.df.at[index, 'Longitude'] = lon

                    # Ekstrak Nomor HP
                    try:
                        phone_el = page.locator('button[data-item-id^="phone:tel:"], button[aria-label*="Nomor telepon"], button[aria-label*="Phone"]').first
                        phone_el.wait_for(state="attached", timeout=3000)
                        if phone_el.count() > 0:
                            aria = phone_el.get_attribute("aria-label")
                            if aria: nomor = aria.replace("Nomor telepon: ", "").replace("Phone: ", "").strip()
                    except: pass
                    
                    self.df.at[index, 'Kontak_WA'] = nomor
                    # ==========================================

                    # 2. Buka Tab Ulasan
                    try:
                        tab = page.locator('div[role="tab"], button').filter(
                            has_text=re.compile(r"(Reviews|Ulasan)", re.IGNORECASE)
                        ).first
                        tab.wait_for(state="visible", timeout=8000)
                        tab.click()
                        page.wait_for_timeout(2000)

                        # Urutkan Terbaru
                        sort_btn = page.locator('button[aria-label*="Urutkan"], button[data-value="Sort"]').first
                        sort_btn.click(timeout=5000)
                        page.wait_for_timeout(1000)

                        newest_btn = page.locator('div[role="menuitemradio"]').filter(
                            has_text=re.compile(r"(Terbaru|Newest)", re.IGNORECASE)
                        ).first
                        newest_btn.click(timeout=5000)
                        page.wait_for_timeout(2500)
                    except Exception:
                        print("Peringatan: Gagal navigasi tab ulasan / filter terbaru.")
                        self.df.at[index, 'Review_3_Bulan'] = "GAGAL SORTIR"
                        self.df.to_excel(self.output_file, index=False)
                        continue

                    # 3. Ekstraksi ulasan
                    review_unik = set()
                    komp_30, komp_90 = 0, 0
                    target_tercapai = False
                    stuck_counter = 0
                    previous_count = 0

                    while not target_tercapai:
                        reviews_data = page.evaluate(r'''() => {
                            let blocks = document.querySelectorAll('.jftiEf');
                            return Array.from(blocks).map((b) => {
                                let uid = b.getAttribute('data-review-id');
                                let dateEl = b.querySelector('.rsqaWe');
                                let textEl = b.querySelector('.wiI7pd');
                                let starEl = b.querySelector('span[role="img"][aria-label]');

                                let starText = starEl ? starEl.getAttribute('aria-label') : "";
                                let rating = starText ? parseInt((starText.match(/(\d)/) || [0])[0]) : 0;
                                let dateText = dateEl ? dateEl.innerText.toLowerCase().trim() : "";
                                let reviewText = textEl ? textEl.innerText.toLowerCase().trim() : "";

                                if (!uid) {
                                    let rawText = b.innerText || "";
                                    uid = rawText.replace(/\s+/g, '').substring(0, 80);
                                }
                                return { id: uid, date: dateText, text: reviewText, rating: rating };
                            });
                        }''')

                        for rev in reviews_data:
                            date_text = rev['date']
                            if not date_text or not rev['id']:
                                continue

                            if any(batas in date_text for batas in BATAS_BERHENTI):
                                target_tercapai = True
                                break

                            if rev['id'] not in review_unik:
                                review_unik.add(rev['id'])

                                if 0 < rev['rating'] <= 3 and any(kw in rev['text'] for kw in KEYWORDS_KOMPLAIN):
                                    if any(kat in date_text for kat in KATEGORI_MENENGAH):
                                        komp_90 += 1
                                    else:
                                        komp_30 += 1

                        if target_tercapai:
                            break

                        try:
                            page.evaluate("let b = document.querySelectorAll('.jftiEf'); if(b.length>0) b[b.length-1].scrollIntoView();")
                        except Exception:
                            pass
                        page.wait_for_timeout(2500)

                        current_count = len(review_unik)
                        if current_count == previous_count:
                            stuck_counter += 1
                            try:
                                page.mouse.wheel(0, 300)
                            except Exception:
                                pass
                        else:
                            stuck_counter = 0

                        if stuck_counter >= 5:
                            break
                        previous_count = current_count

                    self.df.at[index, 'Review_3_Bulan'] = len(review_unik)
                    self.df.at[index, 'Komplain_30Hari'] = komp_30
                    self.df.at[index, 'Komplain_90Hari'] = komp_90

                    print(f"Hasil: Review={len(review_unik)} | Komplain={komp_30 + komp_90} | WA={nomor}")
                    self.df.to_excel(self.output_file, index=False)

                except Exception as e:
                    print(f"Error pada {resto}: {e}")
                    self.df.at[index, 'Review_3_Bulan'] = "ERROR"
                    self.df.to_excel(self.output_file, index=False)

            context.close()
            print(f"\nProses selesai. Berkas tersimpan di: {self.output_file}")


if __name__ == "__main__":
    bot = BotScraperApify()
    bot.run()