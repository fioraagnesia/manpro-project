import pandas as pd

# 2. Database pesawat (HASIL CLUSTERING PESAWAT ANDA)
df_flights = pd.read_csv('data_cleaned/cleaned_flights_combined.csv')
df_flights['Flight Date'] = pd.to_datetime(df_flights['date'], dayfirst=True)

# 1. Database hotel (HASIL CLUSTERING GLOBAL ANDA)
df_hotels = pd.read_csv('data_cleaned/cleaned_hotel_combined.csv')
df_hotels['Checkin Date'] = pd.to_datetime(df_hotels['Checkin Date'], dayfirst=True)

def cari_combo_budget(
    # --- Filter Dasar (Input User) ---
    user_origin, 
    user_destination, 
    user_date,
    max_total_budget, # <-- INI INPUT BARU ANDA
    
    # --- Filter Cerdas (Opsional) ---
    target_hotel_segment=None,
    target_flight_segment=None
):
    
    print(f"--- Mencari SEMUA combo di bawah Rp {max_total_budget:,.0f} ---")
    print(f"Filter: {user_origin} -> {user_destination} pada {user_date.date()}")

    # ============================================
    # 1. SARING (FILTER) DATABASE HOTEL
    # ============================================
    
    # Salin data hotel untuk disaring
    hotels_cocok = df_hotels.copy()
    
    # Terapkan Filter Dasar
    hotels_cocok = hotels_cocok[
        (hotels_cocok['City'] == user_destination) &
        (hotels_cocok['Checkin Date'] == user_date)
    ]
    
    # Terapkan Filter Cerdas (HANYA JIKA DIPILIH USER)
    if target_hotel_segment:
        hotels_cocok = hotels_cocok[
            hotels_cocok['Segmentasi'] == target_hotel_segment
        ]
    
    # Ganti nama kolom agar tidak bentrok
    hotels_to_merge = hotels_cocok[['Hotel Name', 'City', 'Price']].add_suffix('_hotel')


    # ============================================
    # 2. SARING (FILTER) DATABASE PESAWAT
    # ============================================
    
    flights_cocok = df_flights.copy()
    
    # Terapkan Filter Dasar
    flights_cocok = flights_cocok[
        (flights_cocok['Origin'] == user_origin) &
        (flights_cocok['Destination'] == user_destination) &
        (flights_cocok['Flight_Date'] == user_date)
    ]
    
    # Terapkan Filter Cerdas (HANYA JIKA DIPILIH USER)
    if target_flight_segment:
        flights_cocok = flights_cocok[
            flights_cocok['Segmentasi'] == target_flight_segment
        ]
    
    # Ganti nama kolom agar tidak bentrok
    flights_to_merge = flights_cocok[['Airline', 'Price', 'Segmentasi']].add_suffix('_flight')

    # ============================================
    # 3. BUAT SEMUA KEMUNGKINAN COMBO (CROSS JOIN)
    # ============================================
    
    if hotels_to_merge.empty or flights_to_merge.empty:
        print("Kombinasi paket tidak ditemukan untuk filter dasar tersebut.")
        return

    # 'how='cross'' akan menjodohkan SETIAP hotel dengan SETIAP pesawat
    print(f"Menemukan {len(hotels_to_merge)} hotel dan {len(flights_to_merge)} pesawat. Membuat combo...")
    df_combos = pd.merge(hotels_to_merge, flights_to_merge, how='cross')

    # Hitung total harga untuk SETIAP combo
    df_combos['Total_Price'] = df_combos['Price_hotel'] + df_combos['Price_flight']

    # ============================================
    # 4. TERAPKAN FILTER BUDGET ANDA
    # ============================================
    
    df_final_combos = df_combos[
        df_combos['Total_Price'] <= max_total_budget
    ]

    # Urutkan dari yang termurah
    df_final_combos = df_final_combos.sort_values(by='Total_Price', ascending=True)

    # ============================================
    # 5. TAMPILKAN HASILNYA
    # ============================================
    
    if df_final_combos.empty:
        print(f"Tidak ada combo yang ditemukan di bawah budget Rp {max_total_budget:,.0f}.")
    else:
        print(f"\n--- Menampilkan {len(df_final_combos)} Paket Combo di Bawah Rp {max_total_budget:,.0f} ---")
        print(df_final_combos.head(10)) # Tampilkan 10 combo termurah


print("\n" + "="*50)
print("SKENARIO 1: Cari paket apa saja ke Surabaya, budget 2 Juta")
print("="*50)
cari_combo_budget(
    user_origin='Jakarta',
    user_destination='Surabaya',
    user_date=pd.to_datetime('2025-10-27'),
    max_total_budget=2000000 
)