import pandas as pd
import numpy as np
import re

pd.set_option("future.no_silent_downcasting", True)

# map airline names
airline_map = {
    "airasia berhad (malaysia)": "AirAsia",
    "airasia indonesia": "AirAsia",
    "indonesia airasia": "AirAsia",
    "pt indonesia airasia": "AirAsia",
    "air asia": "AirAsia",
    "batik air indonesia": "Batik Air",
    "batik air malaysia": "Batik Air",
    "batik air": "Batik Air",
    "lion air": "Lion Air",
    "lion airlines": "Lion Air",
    "thai lion air": "Lion Air",
    "super air jet": "Super Air Jet",
    "wings air": "Wings Air",
    "citilink": "Citilink",
    "garuda indonesia": "Garuda Indonesia",
    "malaysia airlines": "Malaysia Airlines",
    "pelita air": "Pelita Air",
    "scoot": "Scoot",
    "singapore airlines": "Singapore Airlines",
    "cathay pacific": "Cathay Pacific",
    "thai airways": "Thai Airways",
    "transnusa": "TransNusa",
    "transnusa aviation": "TransNusa",
    "klm" : "Koninklijke Luchtvaart Maatschappij",
}

# normalize airline names to same names
def normalize_airline(value):
    if pd.isna(value):
        return np.nan
    value = str(value).lower().strip()

    # split klo transit
    parts = re.split(r"[,+/]", value)
    parts = [p.strip() for p in parts if p.strip()]

    normalized = []
    for p in parts:
        normalized.append(airline_map.get(p, p.title()))

    return " , ".join(sorted(set(normalized)))

# function cleaning data
def clean_dataframe(df, drop_cols=None, dropna_cols=None, clean_baggage=True):
    df = df.copy()

    # drop unnecessary cols
    if drop_cols:
        df = df.drop(columns=drop_cols, errors="ignore")

    # drop rows yg missing critical cols
    if dropna_cols:
        df = df.dropna(subset=dropna_cols).copy()

    # clean origin, destination
    df.loc[:, "origin"] = df["origin"].astype(str).str.split().str[0]
    df.loc[:, "destination"] = df["destination"].astype(str).str.split().str[0]

    # map destination city
    city_map = {
    "CGK": "Jakarta",
    "DPS": "Bali",
    "HLP": "Jakarta",
    "JKT": "Jakarta",
    "SIN": "Singapura",
    "SRG": "Semarang",
    "SUB": "Surabaya"
    }
    df["city"] = df["destination"].map(city_map)
    
    # clean seat class
    def clean_seat_class(value):
        if pd.isna(value):
            return np.nan
        text = value.lower().strip()
        text = re.sub(r"\bclass\b", "", text).strip()
        text = re.sub(r"\s*/\s*", " / ", text)
        text = " / ".join([w.strip().capitalize() for w in text.split("/")])
        return text.strip()

    df.loc[:, "seat_class"] = df["seat_class"].astype(str).apply(clean_seat_class)

    # clean airline
    if "airline" in df.columns:
        df["airline"] = df["airline"].astype(str).apply(normalize_airline)

    # clean transit
    if "transit" in df.columns:
        df.loc[:, "transit"] = (
            df["transit"]
            .astype(str)
            .str.extract(r"(\d+)")[0]
            .replace([None, np.nan], 0)
            .fillna(0)
            .astype(int)
        )

 
   # clean baggage
    if clean_baggage and "baggage" in df.columns:
    # Extract numeric baggage and convert to float early
        df["baggage"] = (
            df["baggage"]
            .astype(str)
            .str.extract(r"(\d+)")[0]
            .astype(float)
        )

    # most frequent non-zero baggage per airline if null
        def airline_mode(series):
            non_zero = series[series > 0]
            if non_zero.empty:
                return np.nan
            return non_zero.mode().iloc[0] if not non_zero.mode().empty else np.nan

        mode_baggage = df.groupby("airline")["baggage"].transform(airline_mode)

        # to float
        df["baggage"] = df["baggage"].astype(float)
        mode_baggage = mode_baggage.astype(float)

        df["baggage"] = np.where(
            df["baggage"].isna() | (df["baggage"] == 0),
            mode_baggage,
            df["baggage"]
        )

        # fill with overall most frequent non-zero baggage if still null
        global_mode = df.loc[df["baggage"] > 0, "baggage"].mode()
        if not global_mode.empty:
            df["baggage"] = df["baggage"].fillna(global_mode.iloc[0])

        # convert to nullable Int64 to avoid dtype error
        df["baggage"] = df["baggage"].round().astype("Int64")


    # normalize time
    time_columns = ["departure_time", "arrival_time"]

    for col in time_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.replace(".", ":", regex=False)
            
            df[col] = pd.to_datetime(df[col], format="%H:%M:%S", errors="coerce").fillna(
                pd.to_datetime(df[col], format="%H:%M", errors="coerce")
            )

            df[col] = df[col].dt.strftime("%H:%M")

    return df


# load file
df_trip = pd.read_excel("data_scraping/flight/flight_trip.xlsx")
df_traveloka = pd.read_excel("data_scraping/flight/flight_traveloka.xlsx")
df_booking = pd.read_excel("data_scraping/flight/flight_booking.xlsx")
df_tiket = pd.read_excel("data_scraping/flight/flight_tiket.xlsx")
df_agoda = pd.read_excel("data_scraping/flight/flight_agoda.xlsx")

# cut last 2 nums in price
df_booking['price'] = (
    df_booking['price']
    .astype(str)           
    .str.replace(r'[^\d]', '', regex=True)
    .astype(float)
)
df_booking.loc[df_booking['price'] > 99999999, 'price'] = (
    df_booking.loc[df_booking['price'] > 99999999, 'price'] // 100
)

# col name change
df_trip = df_trip.rename(columns={
    "fare_type": "seat_class",
    "baggage_value": "baggage",
    "Baggage": "baggage"
})
df_agoda = df_agoda.rename(columns={
    "Baggage": "baggage"
})

# normalize date
def normalize_date_column(df, column="date"):
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

    # fallback for anything else
    if df[column].isna().any():
        fallback = pd.to_datetime(df[column], errors="coerce", dayfirst=True)
        df[column] = fallback.combine_first(df[column])

    df[column] = df[column].dt.strftime("%d/%m/%y")

    return df

df_trip = normalize_date_column(df_trip, "date")
df_traveloka = normalize_date_column(df_traveloka, "date")
df_booking = normalize_date_column(df_booking, "date")
df_tiket = normalize_date_column(df_tiket, "date")
df_agoda = normalize_date_column(df_agoda, "date")

# parameters to drop if null
dropna_cols = ["date", "airline", "departure_time", "arrival_time", "price", "origin", "destination", "seat_class"]

# clean
df_trip = clean_dataframe(df_trip, drop_cols=None, dropna_cols=dropna_cols)
df_traveloka = clean_dataframe(df_traveloka, drop_cols=None, dropna_cols=dropna_cols)
df_booking = clean_dataframe(df_booking, drop_cols=None, dropna_cols=dropna_cols)
df_tiket = clean_dataframe(df_tiket, drop_cols=None, dropna_cols=dropna_cols)
df_agoda = clean_dataframe(df_agoda, drop_cols=None, dropna_cols=dropna_cols)

# check
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

# combine cleaned data
frames = [df_trip, df_traveloka, df_booking, df_tiket, df_agoda]
df_all = pd.concat(frames, ignore_index=True)

# normalize cols
df_all['airline'] = df_all['airline'].str.strip()
df_all['origin'] = df_all['origin'].str.strip().str.upper()
df_all['destination'] = df_all['destination'].str.strip().str.upper()

# identify same flights
group_cols = ["date", "airline", "departure_time", "origin", "destination"]

# choose cheapest from the data if same flight
def pick_best(group):
    group['non_nulls'] = group.notna().sum(axis=1)
    return group.sort_values(by=['non_nulls', 'price'], ascending=[False, True]).iloc[0]

clean_df = df_all.groupby(group_cols, as_index=False, group_keys=False).apply(pick_best).reset_index(drop=True)

clean_df = clean_df.drop(columns=['non_nulls'], errors='ignore')

# drop if seat class unknown
clean_df = clean_df[~clean_df['seat_class'].isin(['Unknown', 'unknown', '', None, np.nan])]

print("Final combined data shape:", clean_df.shape)
print("Example records:")
print(clean_df.head())

# INI BUAT ALL AIRLINE NAMES
# Combine all airline names into a single Series
all_airlines = pd.concat([
    df_trip["airline"],
    df_traveloka["airline"],
    df_booking["airline"],
    df_tiket["airline"],
    df_agoda["airline"]
])

# Drop missing and normalize casing
all_airlines = all_airlines.dropna().str.strip().str.title()

# Get unique names sorted alphabetically
unique_airlines = sorted(all_airlines.unique())

# Display
print(f"Total unique airlines found: {len(unique_airlines)}")
for a in unique_airlines:
    print(a)
# END OF ALL AIRLINES NAMES

# INI BUAT ALL BANDARA NAMES
# Combine all airline names into a single Series
all_airport_des = pd.concat([
    df_trip["destination"],
    df_traveloka["destination"],
    df_booking["destination"],
    df_tiket["destination"],
    df_agoda["destination"]
])

# Drop missing and normalize casing
all_airport_des = all_airport_des.dropna().str.strip().str.title()

# Get unique names sorted alphabetically
unique_airport_des = sorted(all_airport_des.unique())

# Display
print(f"Total unique airlines found: {len(unique_airlines)}")
for a in unique_airport_des:
    print(a)

clean_df.to_csv("data_cleaned/cleaned_flights_combined.csv", index=False)
print("Saved combined clean data to data/cleaned_flights_combined.csv")
