# F&B Leads Analytics & Geospatial Dashboard

Repositori ini memuat *end-to-end data pipeline* dan *dashboard* analitik interaktif yang dikembangkan untuk mengotomatisasi proses kualifikasi prospek bisnis (B2B *Leads Generation*) di sektor Food & Beverage (F&B) untuk **Sora Seventh**.

Sistem ini didesain khusus untuk mencari, memfilter, dan menyusun basis data target pasar UMKM F&B skala menengah (Kafe, Restoran Keluarga, Cloud Kitchen) yang berpeluang besar mengadopsi sistem POS Sora Seventh, terutama mereka yang membutuhkan efisiensi Harga Pokok Penjualan (HPP) dan manajemen loyalitas pelanggan (CRM).

---

## Fitur Utama

* **Automated Intelligence:** Implementasi bot *scraper* berbasis Playwright untuk mengekstraksi koordinat spasial, nomor WhatsApp, dan mendeteksi sentimen keluhan pelanggan secara otomatis dari ulasan publik.
* **Dynamic Lead Scoring Engine:** Sistem pembobotan algoritmik kustom yang memprioritaskan restoran dengan tingkat keramaian tinggi namun memiliki celah operasional yang kritis (sasaran akuisisi ideal).
* **Executive Actionable Dashboard:** Antarmuka visual menggunakan Streamlit dan Folium, dilengkapi fitur eksekusi langsung (*Direct WhatsApp & Gmaps Navigation*) untuk mempercepat respons tim lapangan.

---

## Metodologi & Alur Kerja (4-Week Sprint)

Pengembangan proyek ini dieksekusi melalui metodologi empat fase (sprint 4 minggu) yang menyelaraskan rekayasa data dengan strategi akuisisi klien:

### Minggu 1: Pemetaan Kriteria Target (ICP Mapping)

Menganalisis 16 fitur unggulan POS Sora Seventh dan mencocokkannya dengan *pain points* UMKM. Menetapkan parameter *Ideal Customer Profile* (ICP), seperti: ketersediaan fasilitas *dine-in* (untuk fitur *e-menu*), variasi menu yang kompleks (untuk fitur gramasi/HPP), dan pembatasan target pada non-franchise raksasa.

### Minggu 2: Pengumpulan Data (Data Scraping & Mining)

Mengumpulkan data UMKM kuliner di wilayah Surakarta dari berbagai platform digital ke dalam satu basis data terpusat.

* **Pembersihan Awal (SaringDataManual.py):** Standarisasi format data dan membuang resto dengan ulasan di bawah 50 (validasi keramaian).
* **Automasi Web (bot_manual.py):** Mengerahkan bot *headless* Playwright untuk mengekstrak titik koordinat, kontak aktif, dan mendeteksi kata kunci keluhan operasional di ulasan (misal: "antre lama", "salah pesanan").
* **Konsolidasi (PenggabungFinal.py):** Deduplikasi data menggunakan logika normalisasi *string* untuk menyusun *Master Database*.

### Minggu 3: Lead Scoring & Analisis Kecocokan

Membangun *Scoring Engine* (scoring_final.py) untuk memberikan skor kecocokan (prioritas) pada setiap prospek berdasarkan metrik bisnis:

* **Kesesuaian Profil (Maks. 50 Poin):** Evaluasi fasilitas operasional, keaktifan kampanye digital (Instagram/TikTok), dan kesesuaian target pasar (rentang harga menengah).
* **Urgensi Operasional (Multiplier):** Penambahan 25 poin secara eksponensial untuk setiap keluhan pelanggan yang terdeteksi.
* **Klasifikasi Akhir:** Pembagian kelas menjadi HOT LEADS, WARM LEADS, dan COLD LEADS.

### Minggu 4: Finalisasi & Strategi Pendekatan (Outreach Strategy)

Membangun *Executive Dashboard* (app.py) menggunakan **Streamlit**. Dasbor ini merapikan basis data final menjadi format siap eksekusi bagi tim *Sales*. Tabel terintegrasi dengan tautan eksekusi (WhatsApp & Gmaps) yang memungkinkan tim pemasaran melakukan *pitching* spesifik (misal: menawarkan fitur notifikasi stok & HPP gramasi untuk resto yang sering kehabisan bahan baku).

---

## Instalasi & Penggunaan

### Prasyarat

Pastikan sistem Anda telah terinstal Python 3.9+.

### 1. Clone Repository

git clone [https://github.com/username/sora-seventh-leads-analytics.git](https://github.com/username/sora-seventh-leads-analytics.git)
cd sora-seventh-leads-analytics

### 2. Instalasi Dependensi

Jalankan perintah berikut untuk memasang seluruh pustaka yang dibutuhkan:

pip install -r requirements.txt

*(Catatan: Jika Anda berencana mengeksekusi ulang bot_manual.py, pastikan Anda mengonfigurasi mesin browser dengan menjalankan perintah playwright install).*

### 3. Menjalankan Dashboard

Pastikan berkas basis data master (Skor_Final_V2.xlsx) berada pada direktori /Data. Jalankan server lokal dengan perintah:

streamlit run 4_dashboard.py

Aplikasi akan otomatis berjalan dan dapat diakses melalui peramban pada http://localhost:8501.

---

## Tentang Pengembang

Proyek ini dikembangkan oleh **Raymundus Ariel Abas**, mahasiswa Sains Data di Telkom University, sebagai bagian dari inisiatif pemodelan profil pelanggan ideal (Ideal Customer Profiling) dan modernisasi strategi *inbound marketing* B2B. Pendekatan ini mendemonstrasikan integrasi antara rekayasa data, automasi web, dan intelijen bisnis untuk menghasilkan *Return on Investment* (ROI) yang terukur bagi tim pemasaran.
