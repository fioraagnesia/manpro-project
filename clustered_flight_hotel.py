import pandas as pd
import numpy as np
from kmodes.kprototypes import KPrototypes

# Load data
df_f = pd.read_csv("data_cleaned/cleaned_flights_combined.csv")  
df_h = pd.read_csv("data_cleaned/cleaned_hotel_combined.csv") 


#datetime format check
df_f["date"] = pd.to_datetime(df_f["date"], dayfirst=True, errors="coerce")
# checkin date check
if "Checkin Date" in df_h.columns:
    df_h["Checkin Date"] = pd.to_datetime(df_h["Checkin Date"], dayfirst=True, errors="coerce")
else:
    possible = [c for c in df_h.columns if "checkin" in c.lower()]
    if possible:
        df_h[possible[0]] = pd.to_datetime(df_h[possible[0]], dayfirst=True, errors="coerce")
        df_h.rename(columns={possible[0]: "Checkin Date"}, inplace=True)
    else:
        raise ValueError("Kolom Checkin Date tidak ditemukan di file hotels")


# Normalisasi kota hotel (case)
df_h["city"] = df_h["City"].astype(str).str.strip().str.title()
df_h["city"] = df_h["City"].str.strip().str.title()


# Pre-clean col price should be numeric
df_f["price"] = pd.to_numeric(df_f["price"], errors="coerce")
if "Price" in df_h.columns:
    df_h["Price"] = pd.to_numeric(df_h["Price"], errors="coerce")
else:
    raise ValueError("Col Price is not found in file hotels")

for col in ["baggage", "transit"]:
    if col in df_f.columns:
        df_f[col] = pd.to_numeric(df_f[col], errors="coerce")
    else:
        df_f[col] = np.nan

# seat_class string for categorical
if "seat_class" in df_f.columns:
    df_f["seat_class"] = df_f["seat_class"].astype(str).str.strip().replace({"nan": None})
else:
    df_f["seat_class"] = None

# hotel star and guest rating numeric
for col in ["Hotel Star", "Guest Rating"]:
    if col in df_h.columns:
        df_h[col] = pd.to_numeric(df_h[col], errors="coerce")
    else:
        df_h[col] = np.nan

# MERGE
df_f["city"] = df_f["city"].astype(str).str.title()

# Merge inner date, city need to be same
df_merged = pd.merge(
    df_f,
    df_h,
    left_on=["city", "date"],
    right_on=["city", "Checkin Date"],
    how="inner",
    suffixes=("_flight", "_hotel")
)

print("Matching flight and hotel:", len(df_merged))

# count total price
df_merged["total_price"] = df_merged["price"] + df_merged["Price"]

# rename flight price and hotel price cols
df_merged.rename(columns={"price": "flight_price", "Price": "hotel_price"}, inplace=True)


# prepare features for clustering -> use "flight_price", "hotel_price", "Hotel Star", "Guest Rating", "baggage", "transit", "seat_class"
features_num = ["flight_price", "hotel_price", "Hotel Star", "Guest Rating", "baggage", "transit"]
features_cat = ["seat_class"] 

# check so no col is missing
for c in features_num:
    if c not in df_merged.columns:
        df_merged[c] = np.nan

for c in features_cat:
    if c not in df_merged.columns:
        df_merged[c] = "Unknown"

# Fill missing: numeric -> median, categorical -> "Unknown"
for c in features_num:
    med = df_merged[c].median(skipna=True)
    df_merged[c] = df_merged[c].fillna(med)

for c in features_cat:
    df_merged[c] = df_merged[c].fillna("Unknown").astype(str)

# Assign data for K-Prototypes: all col to array (numeric then categorical)
X_num = df_merged[features_num].to_numpy(dtype=float)
X_cat = df_merged[features_cat].astype(str).to_numpy()

#Merge
X_all = np.hstack([X_num, X_cat])

# Index col categorical (0-based)
cat_cols_idx = list(range(X_num.shape[1], X_num.shape[1] + X_cat.shape[1]))

# K-PROTOTYPES CLUSTERING
k = 3  # Budget, Mid-range, Luxury
kproto = KPrototypes(n_clusters=k, init='Cao', verbose=1, random_state=42)

# Note: fit_predict expects numpy array with object dtype for categorical columns
# Convert entire X_all ke object
X_all_obj = X_all.astype(object)

clusters = kproto.fit_predict(X_all_obj, categorical=cat_cols_idx)

df_merged["cluster_raw"] = clusters

# Map cluster number -> label (berdasarkan median total_price)
cluster_price_median = df_merged.groupby("cluster_raw")["total_price"].median().sort_values()
# cluster_price_median is Series sorted ascending -> lowest = Budget
sorted_clusters = list(cluster_price_median.index)

label_map = {}
labels = ["Budget", "Mid-range", "Luxury"]
for i, cluster_id in enumerate(sorted_clusters):
    if i < len(labels):
        label_map[cluster_id] = labels[i]
    else:
        label_map[cluster_id] = f"Cluster_{i}"

df_merged["cluster"] = df_merged["cluster_raw"].map(label_map)

out_fp = "data_clustered/flight_hotel_clustered.csv"
df_merged.to_csv(out_fp, index=False)
print("Saved clustered results to:", out_fp)

# Summary cluster
summary = df_merged.groupby("cluster").agg(
    count_pairs=("total_price", "count"),
    median_total=("total_price", "median"),
    median_flight=("flight_price", "median"),
    median_hotel=("hotel_price", "median"),
    avg_hotel_star=("Hotel Star", "median"),
    avg_guest_rating=("Guest Rating", "median")
).reset_index()

print(summary)

# TRY SHOW
for lbl in labels:
    print(f"\nSample for cluster: {lbl}")
    display = df_merged[df_merged["cluster"] == lbl].head(5)[
        ["city", "date", "flight_price", "hotel_price", "total_price", "airline", "origin", "destination", "seat_class", "Hotel Name", "cluster"]
    ]
    print(display.to_string(index=False))
