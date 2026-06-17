import streamlit as st
import folium
from streamlit_folium import st_folium
import math

# Set Page Config untuk Web
st.set_page_config(page_title="Pencarian Masjid Terdekat - KD-Tree", layout="wide")

# ==========================================
# 1. DATA MASJID & TITIK ACUAN
# ==========================================
data_masjid = [
    {"nama": "Masjid Mahasiswa Valencia", "lat": -1.6095532, "lon": 103.5048731, "rating": 4.5},
    {"nama": "Masjid Nurul Islam FEB", "lat": -1.6114873, "lon": 103.5083581, "rating": 4.6},
    {"nama": "Masjid Nurul Ilmi Fakultas Hukum", "lat": -1.6142519, "lon": 103.5070829, "rating": 5.0},
    {"nama": "Masjid Al-Ijtihad FKIP", "lat": -1.6164552, "lon": 103.5144302, "rating": 4.4},
    {"nama": "Masjid Fakultas Pertanian", "lat": -1.6131701, "lon": 103.5100749, "rating": 5.0},
    {"nama": "Masjid Baitul Hikmah", "lat": -1.6119630, "lon": 103.5126574, "rating": 4.9},
    {"nama": "Masjid At-Taqwa", "lat": -1.6091876, "lon": 103.5138310, "rating": 4.7},
    {"nama": "Jamiussalam Mosque", "lat": -1.6182978, "lon": 103.5097090, "rating": 4.8},
    {"nama": "Masjid Al-Huda", "lat": -1.6120323, "lon": 103.5155760, "rating": 4.8}
]

lokasi_acuan = {
    "Laboratorium FKIP": (-1.6151815, 103.5159274),
    "Fakultas Ekonomi dan Bisnis": (-1.6122916, 103.5143817),
    "Fakultas Hukum": (-1.6137992, 103.5142608),
    "Fakultas Pertanian": (-1.6133604, 103.5161803),
    "Fakultas Peternakan": (-1.6145809, 103.5158917),
    "Fakultas Sains dan Teknologi": (-1.6148696, 103.5172501),
    "Balairung Universitas Jambi": (-1.6111297, 103.5173980)
}

# ==========================================
# 2. STRUKTUR DATA & PEMBUATAN KD-TREE
# ==========================================
class Node:
    def __init__(self, point, nama, rating, left=None, right=None, axis=0):
        self.point = point
        self.nama = nama
        self.rating = rating
        self.left = left
        self.right = right
        self.axis = axis

def build_kdtree(data, depth=0):
    if not data:
        return None
    axis = depth % 2
    data.sort(key=lambda x: x["point"][axis])
    median = len(data) // 2
    return Node(
        point=data[median]["point"],
        nama=data[median]["nama"],
        rating=data[median]["rating"],
        left=build_kdtree(data[:median], depth + 1),
        right=build_kdtree(data[median+1:], depth + 1),
        axis=axis
    )

# Konversi dan bangun KD-Tree root
data_kd = [{"point": (item["lat"], item["lon"]), "nama": item["nama"], "rating": item["rating"]} for item in data_masjid]
kd_tree_root = build_kdtree(data_kd)

# ==========================================
# 3. FUNGSI HAVERSINE & RANGE SEARCH
# ==========================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius bumi dalam meter
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def range_search_kdtree(node, query_lat, query_lon, radius, rating_min, hasil):
    if node is None:
        return
    jarak = haversine(query_lat, query_lon, node.point[0], node.point[1])
    if jarak <= radius and node.rating >= rating_min:
        skor = node.rating / jarak
        hasil.append({
            "nama": node.nama,
            "rating": node.rating,
            "jarak": jarak,
            "skor": skor,
            "lat": node.point[0],
            "lon": node.point[1]
        })
    range_search_kdtree(node.left, query_lat, query_lon, radius, rating_min, hasil)
    range_search_kdtree(node.right, query_lat, query_lon, radius, rating_min, hasil)

# ==========================================
# 4. ANTARMUKA WEB (STREAMLIT UI)
# ==========================================
st.title("🕋 Sistem Pencarian & Rekomendasi Masjid Terdekat")
st.write("Aplikasi web pencarian masjid berbasis spasial menggunakan algoritma **KD-Tree**.")

# Membuat layout kolom untuk Sidebar Input dan Map Utama
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("⚙️ Parameter Pencarian")
    
    # Widget Pilihan Titik Acuan
    pilihan_lokasi = st.selectbox("Pilih Titik Acuan :", list(lokasi_acuan.keys()))
    
    # Widget Slider Radius (Meter)
    pilihan_radius = st.slider("Radius Pencarian (Meter) :", min_value=100, max_value=2000, value=500, step=50)
    
    # Widget Slider Rating Minimum
    pilihan_rating = st.slider("Rating Minimum :", min_value=0.0, max_value=5.0, value=4.5, step=0.1)
    
    # Proses Pencarian Lokasi Acuan
    lat_acuan, lon_acuan = lokasi_acuan[pilihan_lokasi]
    
    # Eksekusi Range Search dengan KD-Tree
    hasil_pencarian = []
    range_search_kdtree(kd_tree_root, lat_acuan, lon_acuan, pilihan_radius, pilihan_rating, hasil_pencarian)
    
    # Tampilkan list hasil rekomendasi di bawah input sidebar
    st.subheader("📋 Hasil Rekomendasi Terbaik")
    if len(hasil_pencarian) == 0:
        st.warning("Tidak ada masjid yang memenuhi kriteria di dalam radius.")
    else:
        # Urutkan berdasarkan skor tertinggi (Rating / Jarak)
        hasil_pencarian.sort(key=lambda x: x["skor"], reverse=True)
        for i, item in enumerate(hasil_pencarian, start=1):
            st.markdown(f"**{i}. {item['nama']}**")
            st.caption(f"⭐ Rating: {item['rating']} | 📐 Jarak: {round(item['jarak'], 2)} meter")

with col2:
    st.subheader("🗺️ Peta Lokasi Interaktif")
    
    # Inisialisasi Peta Folium
    peta_web = folium.Map(location=[lat_acuan, lon_acuan], zoom_start=16, tiles="OpenStreetMap")
    
    # Tambahkan Marker Titik Acuan (Oranye)
    folium.Marker(
        location=[lat_acuan, lon_acuan],
        popup=pilihan_lokasi,
        tooltip=pilihan_lokasi,
        icon=folium.Icon(color="orange", icon="home")
    ).add_to(peta_web)
    
    # Tambahkan Lingkaran Radius (Biru)
    folium.Circle(
        location=[lat_acuan, lon_acuan],
        radius=pilihan_radius,
        color="blue",
        fill=True,
        fill_opacity=0.1
    ).add_to(peta_web)
    
    # Plotting Semua Masjid (Default Biru, Hasil Pencarian Merah)
    for item in data_masjid:
        # Periksa apakah masjid ini masuk ke dalam daftar hasil pencarian
        is_hasil = any(h["nama"] == item["nama"] for h in hasil_pencarian)
        
        if is_hasil:
            # Cari data detail jarak untuk popup
            detail = next(h for h in hasil_pencarian if h["nama"] == item["nama"])
            popup_text = f"<b>{item['nama']}</b><br>Rating: {item['rating']}<br>Jarak: {round(detail['jarak'], 2)} m"
            marker_color = "red"
        else:
            popup_text = f"<b>{item['nama']}</b><br>Rating: {item['rating']}"
            marker_color = "blue"
            
        folium.Marker(
            location=[item["lat"], item["lon"]],
            popup=popup_text,
            tooltip=item["nama"],
            icon=folium.Icon(color=marker_color, icon="info-sign")
        ).add_to(peta_web)
        
    # Tambahkan Legenda Keterangan Peta
    legend_html = '''
    <div style="position: fixed; bottom: 30px; left: 30px; width: 180px; height: 100px; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:12px; padding:8px;">
    <b>Keterangan:</b><br>
    🟠 Titik Acuan<br>
    🔴 Masjid (Sesuai Kriteria)<br>
    🔵 Masjid Lainnya
    </div>
    '''
    peta_web.get_root().html.add_child(folium.Element(legend_html))
    
    # Tampilkan peta di dalam layout Streamlit
    st_folium(peta_web, width="100%", height=550)
