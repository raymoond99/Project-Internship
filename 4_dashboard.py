import re
import math
from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Dashboard Leads F&B — Sora Seventh",
    layout="wide",
    initial_sidebar_state="collapsed",
)

OFFICE_LAT, OFFICE_LON = -7.5876601, 110.8122981
OFFICE_NAME = "Kantor Sora Seventh"
DATA_PATH = Path(__file__).parent / "Data" / "Skor_Final_V2.xlsx"
if not DATA_PATH.exists():
    DATA_PATH = Path(__file__).parent / "Skor_Final_V2.xlsx"

# ==========================================
# PALET WARNA (DOMINAN HIJAU SORA SEVENTH)
# ==========================================
UI_COLORS = {
    "darkest": "#1B4332",   
    "dark": "#2D6A4F",      
    "mid": "#40916C",       
    "bg": "#F4FAF6",        
    "card": "#FFFFFF",      
    "text": "#1B2B22"       
}

PRIORITY_COLORS = {
    "HOT LEADS": "#F59E0B",   
    "WARM LEADS": "#2D6A4F",  
    "COLD LEADS": "#028090"   
}
PRIORITY_ORDER = ["HOT LEADS", "WARM LEADS", "COLD LEADS"]

# ==========================================
# CSS KUSTOM
# ==========================================
st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {UI_COLORS['bg']}; }}
    #MainMenu, footer {{visibility: hidden;}}
    
    h1, h2, h3, h4, p, span, label, div {{ font-family: 'Segoe UI', sans-serif; }}

    .hero {{
        background: linear-gradient(135deg, {UI_COLORS['darkest']} 0%, {UI_COLORS['dark']} 60%, #028090 100%);
        padding: 32px 40px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px rgba(27, 67, 50, 0.15);
    }}
    .hero h1 {{ color: #FFFFFF !important; margin: 0 0 8px 0; font-size: 32px; font-weight: 800; letter-spacing: -0.5px; }}
    .hero p {{ color: #D8F3DC !important; margin: 0; font-size: 16px; opacity: 0.95; }}

    div[data-testid="stMetric"] {{
        background: {UI_COLORS['card']};
        border: 1px solid #E5E7EB;
        border-top: 4px solid {UI_COLORS['mid']};
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.08);
    }}
    div[data-testid="stMetricLabel"] {{ color: #4B5563; font-weight: 600; font-size: 13px; text-transform: uppercase; }}
    div[data-testid="stMetricValue"] {{ color: {UI_COLORS['darkest']}; font-size: 34px !important; font-weight: 800; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# UTILITAS & DATA LOADER
# ==========================================
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def make_wa_link(wa):
    wa = str(wa).strip()
    if wa in ['Tidak Ada', 'nan', 'None', '']: return None
    if wa.startswith('0'): wa = '62' + wa[1:]
    return f"https://wa.me/{wa}"

def make_gmaps_link(lat, lon):
    if pd.isna(lat) or pd.isna(lon): return None
    return f"https://www.google.com/maps/dir/?api=1&origin={OFFICE_LAT},{OFFICE_LON}&destination={lat},{lon}"

@st.cache_data(show_spinner=False)
def load_data(file) -> pd.DataFrame:
    df = pd.read_excel(file, dtype={'Nomor_WA': str})
    
    # Hapus emoji bawaan dari Excel agar sesuai dengan label baru
    df['Label_Prioritas'] = df['Label_Prioritas'].replace({
        "HOT LEADS 🔥": "HOT LEADS",
        "WARM LEADS ⭐": "WARM LEADS",
        "COLD LEADS 💡": "COLD LEADS"
    })
    
    # Hitung Jarak
    df["Jarak_Kantor_KM"] = df.apply(
        lambda r: haversine_km(OFFICE_LAT, OFFICE_LON, r["Latitude"], r["Longitude"])
        if pd.notna(r["Latitude"]) and pd.notna(r["Longitude"]) else np.nan, axis=1
    )
    
    # Generate Link
    df["Link_WhatsApp"] = df["Nomor_WA"].apply(make_wa_link)
    df["Link_Maps"] = df.apply(lambda r: make_gmaps_link(r["Latitude"], r["Longitude"]), axis=1)
    
    return df

# ==========================================
# EKSEKUSI UTAMA
# ==========================================
if DATA_PATH.exists():
    df = load_data(DATA_PATH)
else:
    st.error("File 'Skor_Final_V2.xlsx' tidak ditemukan! Pastikan file ada di folder Data.")
    st.stop()

# HERO HEADER
st.markdown(
    f"""
    <div class="hero">
        <h1>Dashboard Leads F&B — Sora Seventh</h1>
        <p>Pemetaan strategis target pasar F&B di sekitar Surakarta, disusun berdasarkan urgensi operasional (komplain) dan kelayakan bisnis.</p>
    </div>
    """, unsafe_allow_html=True
)

# FILTER 
st.markdown("### Filter Target Pasar")
f1, f2, f3, f4 = st.columns([1.2, 1.2, 1, 1.4])
with f1:
    pilihan_prioritas = st.multiselect("Label Prioritas", options=PRIORITY_ORDER, default=PRIORITY_ORDER)
with f2:
    opsi_kat = sorted(df["Kategori"].dropna().unique().tolist())
    pilihan_kategori = st.multiselect("Kategori Usaha", options=opsi_kat, default=opsi_kat)
with f3:
    max_dist = st.slider("Batas Jarak (KM)", min_value=1.0, max_value=float(np.ceil(df["Jarak_Kantor_KM"].max())), value=10.0, step=0.5)
with f4:
    kata_kunci = st.text_input("Cari nama resto", placeholder="mis. kopi, soto, ayam...")

st.markdown("<hr style='border-color: #E5E7EB; margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# APPLY FILTER
mask = (df["Label_Prioritas"].isin(pilihan_prioritas) & df["Kategori"].isin(pilihan_kategori) & (df["Jarak_Kantor_KM"] <= max_dist))
if kata_kunci: mask &= df["Nama_Resto"].str.contains(kata_kunci, case=False, na=False)
df_filtered = df[mask].copy()

# KPI METRICS
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Leads Filter", f"{len(df_filtered)}")
k2.metric("Hot Leads", f"{(df_filtered['Label_Prioritas'] == 'HOT LEADS').sum()}")
k3.metric("Total Kasus Komplain", f"{df_filtered['Total_Indikasi_Komplain_Operasional_Tiga_Bulan'].sum()}")
k4.metric("Jarak Rata-rata", f"{df_filtered['Jarak_Kantor_KM'].mean():.1f} km" if len(df_filtered) else "-")
st.write("")

# GEOSPATIAL MAP & LEADERBOARD
map_col, side_col = st.columns([2.2, 1])

with map_col:
    st.markdown("### Peta Sebaran Leads")
    df_map = df_filtered.dropna(subset=["Latitude", "Longitude"])
    if len(df_map) == 0:
        st.info("Tidak ada data dengan koordinat untuk ditampilkan pada peta.")
    else:
        m = folium.Map(location=[OFFICE_LAT, OFFICE_LON], zoom_start=13, tiles="OpenStreetMap")
        folium.Marker(
            location=[OFFICE_LAT, OFFICE_LON], 
            popup=folium.Popup(f"<b>{OFFICE_NAME}</b>", max_width=220), 
            tooltip=OFFICE_NAME, 
            icon=folium.Icon(color="red", icon="building", prefix="fa")
        ).add_to(m)

        for _, row in df_map.iterrows():
            prio = row["Label_Prioritas"]
            color = PRIORITY_COLORS.get(prio, UI_COLORS["mid"])
            radius = 6 + min(4, row["Total_Skor"] / 40)
            
            popup_html = f"""
            <div style='font-family: Segoe UI, sans-serif; font-size: 13px;'>
                <b>{row['Nama_Resto']}</b><br>
                Kategori: {row['Kategori']}<br>
                Prioritas: <b><span style='color:{color}'>{prio}</span></b><br>
                Skor: {row['Total_Skor']} | Jarak: {row['Jarak_Kantor_KM']:.1f} km<br>
                Komplain: <b>{row['Total_Indikasi_Komplain_Operasional_Tiga_Bulan']} kasus</b>
            </div>
            """
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]], 
                radius=radius, color=color, fill=True, fill_color=color, 
                fill_opacity=0.9, weight=1.5, 
                popup=folium.Popup(popup_html, max_width=260), 
                tooltip=row["Nama_Resto"]
            ).add_to(m)

        st_folium(m, use_container_width=True, height=450, returned_objects=[])

with side_col:
    st.markdown("### Top 10 Klasemen")
    top10 = df_filtered.sort_values("Total_Skor", ascending=False).head(10)
    if len(top10):
        fig_top = px.bar(top10[::-1], x="Total_Skor", y="Nama_Resto", orientation="h", color="Kategori", color_discrete_sequence=px.colors.qualitative.Bold, text="Total_Skor")
        fig_top.update_traces(textposition="outside")
        fig_top.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", 
            height=430, margin=dict(l=0, r=20, t=10, b=0), 
            xaxis_title="Skor Aktual", yaxis_title="", 
            legend_title="Kategori", font=dict(color=UI_COLORS["text"]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_top, use_container_width=True)
    else: st.info("Tidak ada data.")

st.markdown("<br>", unsafe_allow_html=True)

# 3 GRAFIK DISTRIBUSI
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Rasio Prioritas**")
    prio_count = df_filtered["Label_Prioritas"].value_counts().reindex(PRIORITY_ORDER).dropna()
    fig_pie = go.Figure(data=[go.Pie(
        labels=prio_count.index, 
        values=prio_count.values, 
        hole=0.55, 
        sort=False, 
        marker=dict(colors=[PRIORITY_COLORS.get(p) for p in prio_count.index])
    )])
    fig_pie.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), showlegend=True, font=dict(color=UI_COLORS["text"]), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    st.markdown("**Sebaran Kategori Bisnis**")
    kat_count = df_filtered["Kategori"].value_counts().reset_index()
    kat_count.columns = ['Kategori', 'Jumlah']
    fig_kat = px.bar(kat_count, x='Jumlah', y='Kategori', orientation="h", color='Kategori', color_discrete_sequence=px.colors.qualitative.Bold)
    fig_kat.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, xaxis_title="Jumlah Leads", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color=UI_COLORS["text"]))
    st.plotly_chart(fig_kat, use_container_width=True)

with c3:
    st.markdown("**Kepadatan Rating GMaps**")
    fig_hist = px.histogram(df_filtered, x="Rating_GMaps", nbins=12, color_discrete_sequence=[PRIORITY_COLORS["COLD LEADS"]])
    fig_hist.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="Rating Google Maps", yaxis_title="Frekuensi", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color=UI_COLORS["text"]))
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("<hr style='border-color: #E5E7EB;'>", unsafe_allow_html=True)

# TABEL DATA & EXECUTABLE LINKS
st.markdown("### Actionable Data Table (Siap Eksekusi)")

kolom_tampil = [
    "Nama_Resto", "Label_Prioritas", "Total_Skor", "Total_Indikasi_Komplain_Operasional_Tiga_Bulan", 
    "Jarak_Kantor_KM", "Link_WhatsApp", "Link_Maps"
]

st.dataframe(
    df_filtered[kolom_tampil].sort_values("Total_Skor", ascending=False).reset_index(drop=True),
    use_container_width=True, 
    height=400,
    column_config={
        "Nama_Resto": "Nama Restoran",
        "Label_Prioritas": "Kelas",
        "Total_Skor": st.column_config.NumberColumn("Skor", format="%d"),
        "Total_Indikasi_Komplain_Operasional_Tiga_Bulan": st.column_config.NumberColumn("Jml Komplain", format="%d"),
        "Jarak_Kantor_KM": st.column_config.NumberColumn("Jarak", format="%.1f km"),
        "Link_WhatsApp": st.column_config.LinkColumn("Eksekusi Chat", display_text="Chat WA"),
        "Link_Maps": st.column_config.LinkColumn("Navigasi", display_text="Buka Gmaps")
    }
)