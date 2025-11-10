import pandas as pd
import numpy as np
import warnings

AIRPORT_TO_CITY_MAP = {
    "CGK": "Jakarta",
    "DPS": "Bali",
    "HLP": "Jakarta",
    "JKT": "Jakarta",
    "SIN": "Singapura",
    "SRG": "Semarang",
    "SUB": "Surabaya"
}

def search_combo (
    origin,
    destination,
    checkin_date,
    # Optional filters:
    min_total_price = None,
    max_total_price = None,
    airline = None,
    hotel_name = None,
    cluster = None
):
    
    # --- 2. LANGKAH PENERJEMAHAN ---
    # Terjemahkan kode bandara 'CGK' menjadi nama kota 'Jakarta'
    try:
        target_hotel_city = AIRPORT_TO_CITY_MAP[destination]
    except KeyError:
        # Pengaman jika kodenya tidak ada di kamus
        print(f"ERROR: Kode bandara '{destination}' tidak ditemukan di kamus.")
        return
    # --- BATAS LANGKAH BARU ---

    df = pd.read_csv("data_clustered/flight_hotel_clustered.csv")
    df_result = df.copy()

    # Date format
    df_result["date"] = pd.to_datetime(df_result['date'], errors='coerce')
    df_result['Checkin Date'] = pd.to_datetime(df_result['Checkin Date'], errors='coerce')
    # df['Checkout Date'] = pd.to_datetime(df['Checkout Date'], errors='coerce')

    # --- FLIGHT ---
    if origin:
        df_result = df_result[df_result["origin"] == origin.upper()]

    if destination:
        df_result = df_result[df_result["destination"] == destination.upper()]

    if airline:
        df_result = df_result[df_result["airline"].str.contains(airline, case=False, na=False)]
    
    # --- HOTEL ---
    checkin_date = pd.to_datetime(checkin_date)
            
    df_result = df_result[
            (df_result["City"] == target_hotel_city) &
            (df_result["Checkin Date"] == checkin_date)
        ]
    
    # Filter total price
    if min_total_price is not None:
        df_result = df_result[df_result["total_price"] >= min_total_price]
    if max_total_price is not None:
        df_result = df_result[df_result["total_price"] <= max_total_price]

    if hotel_name:
        df_result = df_result[df_result['Hotel Name'].str.contains(hotel_name, case=False)]
    
    if cluster:    # frontend: dropdown
        df_result = df_result[df_result['cluster'] == cluster]

    if df_result.empty:
        return "No combo found with the specified filters."
    # else:
    #     print(f"--- RESULT: {len(df_result)} combos found ---")
    #     show_columns = ["date", "airline", "origin", "destination", "City", "Hotel Name", "total_price", "cluster"]
    #     print(df_result.sort_values(by='total_price')[show_columns].head())
    df_result.to_csv("data_clustered/coba.csv", index=False)

    return df_result


# SIMULATION --> ganti di front end
target_origin = "CGK"
target_destination = "SUB"
target_checkin_date = "2025-11-05"
# target_min_price = 1000000
# target_max_price = 1100000
target_cluster = "Budget"


filtered_result = search_combo(
    origin=target_origin,
    destination=target_destination,
    checkin_date=target_checkin_date,
    # min_total_price=target_min_price,
    # max_total_price=target_max_price,
    cluster=target_cluster
)

print(filtered_result)
