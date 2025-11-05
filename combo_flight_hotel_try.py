import pandas as pd
import os

# === BACA FILE ===
hotel_df = pd.read_csv("data_cleaned/cleaned_hotel_combined.csv")
flight_df = pd.read_csv("data_cleaned/cleaned_flights_combined.csv")

print("============================================================")
print("MENGGABUNGKAN HOTEL × FLIGHT BERDASARKAN CITY YANG SAMA")
print("============================================================")

# hotel_df.rename(columns={"Checkin Date":"date", "City":"city"}, inplace=True)
# Pastikan kolom 'city' ada di kedua dataset
# if 'city' not in hotel_df.columns or 'city' not in flight_df.columns:
#     raise ValueError("Pastikan kedua file memiliki kolom 'city'.")
# if 'date' not in hotel_df.columns or 'date' not in flight_df.columns:
#     raise ValueError("Pastikan kedua file memiliki kolom 'date'.")
hotel_df['date'] = pd.to_datetime(hotel_df['date'])
flight_df['date'] = pd.to_datetime(flight_df['date'])
hotel_df = hotel_df.rename(columns={"city": "city_hotel"})
flight_df = flight_df.rename(columns={"city": "city_flight"})

df_all_combos = pd.merge(
    hotel_df,
    flight_df,
    left_on=["city_hotel", "Checkin Date"],
    right_on=["city_flight", "date"],
    how="inner",
    suffixes=("_hotel", "_flight")
)

# === GABUNGKAN BERDASARKAN CITY & DATE ===
# df_all_combos = pd.merge(hotel_df, flight_df, on=["city","date"], how="inner")

# # === SIMPAN OUTPUT ===
# output_dir = "data_output"
# os.makedirs(output_dir, exist_ok=True)

output_path = "combo_flight_hotel_citymatch new.csv"
df_all_combos.to_csv(output_path, index=False)

print(f"Selesai! Total kombinasi: {len(df_all_combos)}")
print(f"File disimpan di: {output_path}")
