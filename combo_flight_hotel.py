import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")
# --- 1. Buat "Kamus Penerjemah" (WAJIB) ---
# (Taruh ini di atas fungsi Anda)

AIRPORT_TO_CITY_MAP = {
    "CGK": "Jakarta",
    "DPS": "Bali",
    "HLP": "Jakarta",
    "JKT": "Jakarta",
    "SIN": "Singapura",
    "SRG": "Semarang",
    "SUB": "Surabaya"
}

try:
    # PERBAIKAN 4: Muat file HASIL CLEANING (bukan clustering)
    # Anda bisa pakai file 4.000 baris atau 33.000 baris,
    # tapi file 4.000 baris (deduplikasi) lebih efisien.
    df_hotels = pd.read_csv('data_cleaned/cleaned_hotel_combined.csv') 
    # PERBAIKAN 1: Hapus 'dayfirst=True'
    df_hotels['Checkin Date'] = pd.to_datetime(df_hotels['Checkin Date'], errors='coerce')
    df_hotels['Checkout Date'] = pd.to_datetime(df_hotels['Checkout Date'], errors='coerce')


    # PERBAIKAN 4: Muat file CLEANING pesawat
    df_flights = pd.read_csv('data_cleaned/cleaned_flights_combined.csv') 
    # PERBAIKAN 1 & 2: Hapus 'dayfirst' dan samakan nama kolom
    df_flights['Flight_Date'] = pd.to_datetime(df_flights['date'], errors='coerce') 

except FileNotFoundError:
    print("ERROR: File 'cleaned_hotel_combined_new.csv' atau 'cleaned_flights_combined.csv' tidak ditemukan.")
    exit()


def cari_combo_budget_dasar(
    # --- Filter Dasar (Input User) ---
    user_origin, 
    user_destination, 
    user_date,
    max_total_budget # <-- HANYA FILTER DASAR
):
    
    # --- 2. LANGKAH PENERJEMAHAN ---
    # Terjemahkan kode bandara 'CGK' menjadi nama kota 'Jakarta'
    try:
        target_hotel_city = AIRPORT_TO_CITY_MAP[user_destination]
    except KeyError:
        # Pengaman jika kodenya tidak ada di kamus
        print(f"ERROR: Kode bandara '{user_destination}' tidak ditemukan di kamus.")
        return
    # --- BATAS LANGKAH BARU ---

    
    print(f"--- Mencari SEMUA combo di bawah Rp {max_total_budget:,.0f} ---")
    print(f"Filter: {user_origin} -> {user_destination} pada {user_date.date()}")

    # ============================================
    # 1. SARING (FILTER) DATABASE HOTEL
    # ============================================
    hotels_cocok = df_hotels.copy()
    hotels_cocok = hotels_cocok[
        (hotels_cocok['City'] == target_hotel_city) &
        (hotels_cocok['Checkin Date'] == user_date)
    ]
    
    print(df_flights['Flight_Date'].head())
    print(df_hotels['Checkin Date'].head())
    # --- BLOK FILTER CERDAS DIHAPUS ---
    
    # Ganti nama kolom agar tidak bentrok
    # (Kita hapus 'Segmentasi' karena tidak dipakai)
    hotels_to_merge = hotels_cocok[['Hotel Name', 'City', 'Price']].add_suffix('_hotel')

    # ============================================
    # 2. SARING (FILTER) DATABASE PESAWAT
    # ============================================
    flights_cocok = df_flights.copy()
    flights_cocok = flights_cocok[
        (flights_cocok['origin'] == user_origin) &
        (flights_cocok['destination'] == user_destination) &
        # PERBAIKAN 2: Samakan nama kolom
        (flights_cocok['Flight_Date'] == user_date) 
    ]
    
    # --- BLOK FILTER CERDAS DIHAPUS ---
    
    # Ganti nama kolom agar tidak bentrok
    flights_to_merge = flights_cocok[['airline', 'price']].add_suffix('_flight')

    # ============================================
    # 3. BUAT SEMUA KEMUNGKINAN COMBO (CROSS JOIN)
    # ============================================
    
    if hotels_to_merge.empty or flights_to_merge.empty:
        print("Kombinasi paket tidak ditemukan untuk filter dasar tersebut.")
        return

    print(f"Menemukan {len(hotels_to_merge)} hotel dan {len(flights_to_merge)} pesawat. Membuat combo...")
    df_combos = pd.merge(hotels_to_merge, flights_to_merge, how='cross')
    df_combos['Total_Price'] = df_combos['Price_hotel'] + df_combos['price_flight']

    # ============================================
    # 4. TERAPKAN FILTER BUDGET ANDA
    # ============================================
    
    df_final_combos = df_combos[
        df_combos['Total_Price'] <= max_total_budget
    ]
    df_final_combos = df_final_combos.sort_values(by='Total_Price', ascending=True)

    # ============================================
    # 5. TAMPILKAN HASILNYA
    # ============================================
    
    if df_final_combos.empty:
        print(f"Tidak ada combo yang ditemukan di bawah budget Rp {max_total_budget:,.0f}.")
    else:
        print(f"\n--- Menampilkan {len(df_final_combos)} Paket Combo di Bawah Rp {max_total_budget:,.0f} ---")
        print(df_final_combos.head(10)) # Tampilkan 10 combo termurah


# ===================================================================
# CARA MENGGUNAKAN (VERSI SEDERHANA)
# ===================================================================

print("\n" + "="*50)
print("SKENARIO 1: Cari paket apa saja ke Surabaya, budget 2 Juta")
print("="*50)
cari_combo_budget_dasar(
    user_origin='SUB',
    user_destination='CGK',
    user_date=pd.to_datetime('2025-10-31'),
    max_total_budget=2000000 
)