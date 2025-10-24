import pandas as pd
import numpy as np
import re

pd.set_option("future.no_silent_downcasting", True)

def clean_dataframe(df, drop_cols=None, dropna_cols=None, clean_baggage=True):
    # full copy to avoid SettingWithCopyWarning
    df = df.copy()

    # Drop unnecessary columns if they exist
    if drop_cols:
        df = df.drop(columns=drop_cols, errors="ignore")

    # Drop rows with missing critical columns
    if dropna_cols:
        df = df.dropna(subset=dropna_cols).copy()

    # --- CLEAN ORIGIN, DESTINATION, SEAT CLASS ---
    df.loc[:, "origin"] = df["origin"].astype(str).str.split().str[0]
    df.loc[:, "destination"] = df["destination"].astype(str).str.split().str[0]

    def clean_seat_class(value):
        if pd.isna(value):
            return np.nan
        text = value.lower().strip()
        text = re.sub(r"\bclass\b", "", text).strip()           # remove 'class'
        text = re.sub(r"\s*/\s*", " / ", text)                  # normalize slashes
        text = " / ".join([w.strip().capitalize() for w in text.split("/")])
        return text.strip()

    df.loc[:, "seat_class"] = df["seat_class"].astype(str).apply(clean_seat_class)

    # --- CLEAN TRANSIT ---
    if "transit" in df.columns:
        df.loc[:, "transit"] = (
            df["transit"]
            .astype(str)
            .str.extract(r"(\d+)")[0]
            .replace([None, np.nan], 0)
            .fillna(0)
            .astype(int)
        )

 
   # --- CLEAN BAGGAGE ---
    if clean_baggage and "baggage" in df.columns:
        df.loc[:, "baggage"] = (
            df["baggage"]
            .astype(str)
            .str.extract(r"(\d+)")[0]
            .astype(float)
        )

        avg_baggage = df.groupby("airline")["baggage"].transform("mean")

    # Fill missing with airline avg, then overall mean
        df.loc[:, "baggage"] = df["baggage"].fillna(avg_baggage)
        df.loc[:, "baggage"] = df["baggage"].fillna(df["baggage"].mean())

    # Explicit type inference to silence warning
        df.loc[:, "baggage"] = df["baggage"].infer_objects(copy=False)

    # Final rounding and conversion
        df.loc[:, "baggage"] = df["baggage"].round().astype(int)


    # Columns to fix
    time_columns = ["departure_time", "arrival_time"]

    for col in time_columns:
        if col in df.columns:
            # Convert all separators to ':', strip whitespace
            df[col] = df[col].astype(str).str.strip().str.replace(".", ":", regex=False)
            
            # Try to parse to datetime safely
            df[col] = pd.to_datetime(df[col], format="%H:%M:%S", errors="coerce").fillna(
                pd.to_datetime(df[col], format="%H:%M", errors="coerce")
            )
            
            # Drop seconds, keep only hour:minute
            df[col] = df[col].dt.strftime("%H:%M")

    
    return df


# --- LOAD FILES ---
df_trip = pd.read_excel("data-scraping/flight/flight_trip.xlsx")
df_traveloka = pd.read_excel("data-scraping/flight/flight_traveloka.xlsx")
df_booking = pd.read_excel("data-scraping/flight/flight_booking.xlsx")
df_tiket = pd.read_excel("data-scraping/flight/flight_tiket.xlsx")
#df_agoda = pd.read_excel("data-scraping/flight/flights_agoda.xlsx")

# CHANGE COLUMN NAME
df_trip = df_trip.rename(columns={
    "fare_type": "seat_class",
    "baggage_value": "baggage"
})

# UNIFY DATE FORMAT
def normalize_date_column(df, column="date"):
    # text and normalize separators
    df[column] = (
        df[column]
        .astype(str)
        .str.strip()
        .str.replace("-", "/", regex=False)
    )

    # common formats
    possible_formats = ["%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d", "%m/%d/%Y"]

    parsed = None
    for fmt in possible_formats:
        parsed = pd.to_datetime(df[column], format=fmt, errors="coerce", dayfirst=True)
        if parsed.notna().any():
            df[column] = parsed
            break

    # fallback for anythinG else
    if df[column].isna().any():
        fallback = pd.to_datetime(df[column], errors="coerce", dayfirst=True)
        df[column] = fallback.combine_first(df[column])

    # final uniform format
    df[column] = df[column].dt.strftime("%d/%m/%y")

    return df


df_trip = normalize_date_column(df_trip, "date")
df_traveloka = normalize_date_column(df_traveloka, "date")
df_booking = normalize_date_column(df_booking, "date")
df_tiket = normalize_date_column(df_tiket, "date")
#df_agoda = normalize_date_column(df_agoda, "date")

# parameters to drop if null
dropna_cols = ["date", "airline", "departure_time", "arrival_time", "price", "origin", "destination", "seat_class"]

# clean
df_trip = clean_dataframe(df_trip, drop_cols=None, dropna_cols=dropna_cols)
df_traveloka = clean_dataframe(df_traveloka, drop_cols=None, dropna_cols=dropna_cols)
df_booking = clean_dataframe(df_trip, drop_cols=None, dropna_cols=dropna_cols)
df_tiket = clean_dataframe(df_trip, drop_cols=None, dropna_cols=dropna_cols)
df_agoda = clean_dataframe(df_trip, drop_cols=None, dropna_cols=dropna_cols)

# --- CHECK RESULTS ---
print("Missing values in df trip:")
print(df_trip.isnull().sum())
print("\nMissing values in df traveloka:")
print(df_traveloka.isnull().sum())
print("\nMissing values in df booking:")
print(df_booking.isnull().sum())
print("\nMissing values in df tiket:")
print(df_tiket.isnull().sum())
print("\nMissing values in df agoda:")
print(df_agoda.isnull().sum())

print("trip")
print(df_trip)
print("traveloka")
print(df_traveloka)
print("booking")
print(df_booking)
print("tiket")
print(df_tiket)
print("agoda")
print(df_agoda)

print(df_trip.dtypes)
print(df_traveloka.dtypes)
print(df_booking.dtypes)
print(df_tiket.dtypes)
print(df_agoda.dtypes)