import pandas as pd
import numpy as np
import warnings

filepath = "data_clustered/hotel_clustered_global.csv"

def search_hotels(
    filepath,
    city,
    checkin_date,
    checkout_date,
    # Optional filters:
    min_total_price = None,
    max_total_price = None,
    hotel_name = None,
    hotel_star = None,
    guest_rating = None,
    segmentation = None 
):

    df_file = pd.read_csv(filepath)
    df = df_file.copy()

    # Date format
    df['Checkin Date'] = pd.to_datetime(df['Checkin Date'], errors='coerce')
    df['Checkout Date'] = pd.to_datetime(df['Checkout Date'], errors='coerce')

    # --- 1. Konversi & Hitung Durasi ---
    checkin_date = pd.to_datetime(checkin_date)
    checkout_date = pd.to_datetime(checkout_date)
    # Count total nights
    duration_in_days = (checkout_date - checkin_date).days
    
    if duration_in_days <= 0:
        print("The check-out date must be after the check-in date.")
        return
    
    date_range = pd.date_range(start=checkin_date, periods=duration_in_days, freq='D')
            
    df_filtered = df[
            (df["City"] == city) &
            (df["Checkin Date"].isin(date_range))
        ]
    
    # Check availability
    df_count = df_filtered.groupby('Hotel Name')['Checkin Date'].count().reset_index(name='Nights Available')
    avail_hotels = df_count[df_count['Nights Available'] == duration_in_days]
    # Filter available hotels
    df_avail = df_filtered[df_filtered['Hotel Name'].isin(avail_hotels['Hotel Name'])]
    # Sum the prices to get the total price based on duration
    df_total_price = df_avail.groupby('Hotel Name')['Price'].sum().reset_index(name='Total Price')

    # Merge all infos
    df_info = df_avail.drop_duplicates(subset=['Hotel Name'], keep='first')
    df_result = pd.merge(df_total_price, 
                         df_info.drop(columns=['Price', 'Checkin Date', 'Checkout Date', 'Platform', 'Cleaned Name'], errors="ignore"), # Buang kolom yg tidak relevan
                        on='Hotel Name')
    
    df_result['Checkin Date'] = checkin_date
    df_result['Checkout Date'] = checkout_date

    # Filter total price
    if min_total_price is not None:
        df_result = df_result[df_result["Total Price"] >= min_total_price]
    if max_total_price is not None:
        df_result = df_result[df_result["Total Price"] <= max_total_price]

    if hotel_name:
        df_result = df_result[df_result['Hotel Name'].str.contains(hotel_name, case=False)]

    if hotel_star:      # frontend: checkbox
        if isinstance(hotel_star, list): # if choose more than one
            df_result = df_result[df_result['Hotel Star'].isin(hotel_star)]
        else:           # if only choose one
            df_result = df_result[df_result['Hotel Star'] == hotel_star]

    if guest_rating is not None:    # frontend: slider
        df_result = df_result[df_result['Guest Rating'] >= guest_rating]

    if segmentation:    # frontend: dropdown
        df_result = df_result[df_result['Segmentation'] == segmentation]

    df_result = df_result[df_result["Total Price"] <= 50000000]
    
    if df_result.empty:
        return "No hotel found with the specified filters."
    
    return df_result

# SIMULATION --> ganti di front end
target_city = "Surabaya"
target_checkin_date = "2025-12-08"
target_checkout_date = "2025-12-10"
target_min_price = 1000000
target_max_price = 3000000
# target_star = 3
# target_rating = 9

if __name__ == "__main__":
    filtered_result = search_hotels(
        filepath=filepath,
        city=target_city,
        checkin_date=target_checkin_date,
        checkout_date=target_checkout_date,
        min_total_price=target_min_price,
        max_total_price=target_max_price,
        # hotel_star=target_star,
        # guest_rating=target_rating
    )

    print(filtered_result)
