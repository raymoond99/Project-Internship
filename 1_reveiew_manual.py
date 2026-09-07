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

class BotScraperManual:
    def __init__(self, input_filename="Target_Manual_Review50.xlsx", output_filename="Hasil_Scraping_Manual_Lengkap.xlsx"):
        self.base_dir = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
        
        # Penentuan folder yang aman
        target_dir = self.base_dir / "Data" / "Manual dan Apify"
        if not target_dir.exists():
            target_dir = self.base_dir / "Data"
        if not target_dir.exists():
            target_dir = self.base_dir

        self.data_dir = target_dir
        self.input_file = self.data_dir / input_filename
        
        # Fallback kalau namanya pakai 'Plus' dari versi sebelumnya
        if not self.input_file.exists():
            self.input_file = self.data_dir / "Target_Manual_Review50Plus.xlsx"

        self.output_file = self.data_dir / output_filename
        self.profile_path = self.base_dir / "bot_profile"
        self.df = None

    def siapkan_data(self):
        print(f"Mencari data target di: {self.input_file}")

        if not self.input_file.exists():
            print(f"❌ Error: Berkas tidak ditemukan!")
            return False

        self.df = pd.read_excel(self.input_file)

        # Cek ketersediaan kolom URL (hasil dari proses matcher sebelumnya)
        kolom_url = 'URL_Maps_Apify' if 'URL_Maps_Apify' in self.df.columns else 'URL_Maps'
        if kolom_url not in self.df.columns:
            print(f"❌ Gawat, kolom link ({kolom_url}) tidak ada!")
            return False
            
        self.kolom_url = kolom_url

        # Tambahkan kolom penampung hasil jika belum ada
        kolom_baru = ['Review_3_Bulan_Asli', 'Komplain_30Hari', 'Komplain_90Hari', 'Kontak_WA', 'Latitude', 'Longitude']
        for col in kolom_baru:
            if col not in self.df.columns:
                self.df[col] = pd.NA

        print(f"✅ Total target manual siap tempur: {len(self.df)} resto")
        return True

    def run(self):
        if not self.siapkan_data():
            return

        with sync_playwright() as p:
            print("\n🤖 Mesin Playwright Aktif. Mulai Pengerukan...")
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
                url = row[self.kolom_url]

                # Lewati kalau tidak ada link
                if pd.isna(url) or str(url).strip() == "":
                    print(f"\n[{index + 1}/{total}] ⏭️ Melewati {resto} (Link Maps Kosong)")
                    continue

                print(f"\n[{index + 1}/{total}] 🕵️ Mengorek intelijen: {resto}")

                try:
                    page.goto(url, timeout=60000, wait_until="domcontentloaded")
                    page.wait_for_timeout(4000)

                    # ==========================================
                    # 🔥 1. AMBIL KOORDINAT & NOMOR WA 🔥
                    # ==========================================
                    current_url = page.url
                    lat, lon, nomor = pd.NA, pd.NA, pd.NA
                    
                    match_coords = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', current_url)
                    if not match_coords:
                        match_coords = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', current_url)
                    if match_coords:
                        lat, lon = match_coords.group(1), match_coords.group(2)
                    
                    self.df.at[index, 'Latitude'] = lat
                    self.df.at[index, 'Longitude'] = lon

                    try:
                        phone_el = page.locator('button[data-item-id^="phone:tel:"], button[aria-label*="Nomor telepon"], button[aria-label*="Phone"]').first
                        phone_el.wait_for(state="attached", timeout=3000)
                        if phone_el.count() > 0:
                            aria = phone_el.get_attribute("aria-label")
                            if aria: nomor = aria.replace("Nomor telepon: ", "").replace("Phone: ", "").strip()
                    except: pass
                    
                    self.df.at[index, 'Kontak_WA'] = nomor

                    # ==========================================
                    # 🔥 2. BUKA ULASAN DAN SORTIR 🔥
                    # ==========================================
                    try:
                        tab = page.locator('div[role="tab"], button').filter(
                            has_text=re.compile(r"(Reviews|Ulasan)", re.IGNORECASE)
                        ).first
                        tab.wait_for(state="visible", timeout=8000)
                        tab.click()
                        page.wait_for_timeout(2000)

                        sort_btn = page.locator('button[aria-label*="Urutkan"], button[data-value="Sort"]').first
                        sort_btn.click(timeout=5000)
                        page.wait_for_timeout(1000)

                        newest_btn = page.locator('div[role="menuitemradio"]').filter(
                            has_text=re.compile(r"(Terbaru|Newest)", re.IGNORECASE)
                        ).first
                        newest_btn.click(timeout=5000)
                        page.wait_for_timeout(2500)
                    except Exception:
                        print("⚠️ Peringatan: Gagal navigasi tab ulasan / filter terbaru.")
                        self.df.at[index, 'Review_3_Bulan_Asli'] = "GAGAL SORTIR"
                        self.df.to_excel(self.output_file, index=False)
                        continue

                    # ==========================================
                    # 🔥 3. EKSTRAKSI ULASAN & KOMPLAIN 🔥
                    # ==========================================
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
                            try: page.mouse.wheel(0, 300)
                            except Exception: pass
                        else:
                            stuck_counter = 0

                        if stuck_counter >= 5:
                            break
                        previous_count = current_count

                    self.df.at[index, 'Review_3_Bulan_Asli'] = len(review_unik)
                    self.df.at[index, 'Komplain_30Hari'] = komp_30
                    self.df.at[index, 'Komplain_90Hari'] = komp_90

                    print(f"✅ Data Ditarik: Ulasan Asli = {len(review_unik)} | Komplain = {komp_30 + komp_90} | WA = {nomor}")
                    
                    # AUTOSAVE SETIAP RESTO SELESAI
                    self.df.to_excel(self.output_file, index=False)

                except Exception as e:
                    print(f"❌ Error sistem pada {resto}: {e}")
                    self.df.at[index, 'Review_3_Bulan_Asli'] = "ERROR"
                    self.df.to_excel(self.output_file, index=False)

            context.close()
            print(f"\n🎉 Proses Selesai! Data Manual (Lengkap) tersimpan di: {self.output_file.name}")


if __name__ == "__main__":
    bot = BotScraperManual()
    bot.run()