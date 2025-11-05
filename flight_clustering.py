import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import re


df = pd.read_csv("data_cleaned/cleaned_flights_combined.csv")

# convert duration to mins
def duration_to_minutes(x):
    if not isinstance(x, str):
        return np.nan
    
    h = re.search(r"(\d+)\s*h", x)
    m = re.search(r"(\d+)\s*m", x)
    
    hours = int(h.group(1)) if h else 0
    minutes = int(m.group(1)) if m else 0
    
    return hours * 60 + minutes

df["duration_minutes"] = df["duration"].apply(duration_to_minutes)

le_airline = LabelEncoder()
le_class = LabelEncoder()

df["airline_encoded"] = le_airline.fit_transform(df["airline"])
df["seat_class_encoded"] = le_class.fit_transform(df["seat_class"])

# select numeric features for clustering
X = df[["price", "duration_minutes", "baggage", "seat_class_encoded"]]

# normalize
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=3, random_state=42)
df["cluster"] = kmeans.fit_predict(X_scaled)

# average characteristics per cluster
summary = df.groupby("cluster")[["price", "duration_minutes", "baggage"]].mean()
seat_dist = df.groupby(["cluster", "seat_class"]).size().groupby(level=0).apply(lambda x: x / x.sum())

print("\nCluster Summary:")
print(summary)
print("\nSeat Class Distribution:")
print(seat_dist)

# dynamic naming cluster
sorted_clusters = summary["price"].sort_values().index.tolist()

# map
top_classes = (
    df.groupby("cluster")["seat_class"]
    .agg(lambda x: x.value_counts().index[0])
)

if np.issubdtype(top_classes.dtype, np.number):
    top_classes = pd.Series(
        le_class.inverse_transform(top_classes.astype(int)),
        index=top_classes.index
    )

# mean
summary = df.groupby("cluster")[["price", "duration_minutes", "baggage"]].mean()

# score weight
weights = {
    "price": 0.5,           
    "duration_minutes": 0.2,
    "baggage": 0.1,
    "seat_class": 0.2      
}

seat_class_rank = {"Economy": 1, "Premium Economy": 2, "Business": 3, "First": 4}
top_class_score = top_classes.map(lambda c: seat_class_rank.get(c, 0))

summary_norm = (summary - summary.min()) / (summary.max() - summary.min())
summary_norm["seat_class_score"] = top_class_score

# total score
summary_norm["score"] = (
    summary_norm["price"] * weights["price"] +
    summary_norm["duration_minutes"] * weights["duration_minutes"] +
    summary_norm["baggage"] * weights["baggage"] +
    summary_norm["seat_class_score"] * weights["seat_class"]
)

# sort
ranked_clusters = summary_norm["score"].sort_values()

# label flights
labels = ["Budget Flight", "Mid-range Flight", "High-end Flight"]
cluster_labels = {
    cluster_id: labels[i] for i, cluster_id in enumerate(ranked_clusters.index)
}

df["cluster_label"] = df["cluster"].map(cluster_labels)

print("\n Assigned Cluster Labels Automatically:")
for cid, label in cluster_labels.items():
    print(f"Cluster {cid}: {label}")

df.to_csv("data_clustered/cleaned_flights_clustered.csv", index=False)


# JUST PLOTTT
plt.scatter(df["price"], df["duration_minutes"], c=df["cluster"], cmap="viridis")
plt.xlabel("Price (IDR)")
plt.ylabel("Duration (minutes)")
plt.title("Flight Clusters by Price & Duration")
plt.show()

# check label
print("\nFinal cluster labels mapping:")
for cluster_id, name in cluster_labels.items():
    print(f"Cluster {cluster_id} → {name}")