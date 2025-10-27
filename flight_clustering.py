import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import re


df = pd.read_csv("data-cleaned/cleaned_flights_combined.csv")

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
print(summary)

print(df.groupby("cluster")["seat_class"].value_counts(normalize=True))

cluster_labels = {
    0: "Budget Flight",
    1: "Mid-range Flight",
    2: "High-end Flight"
}
df["cluster_label"] = df["cluster"].map(cluster_labels)

# USER INPUT
user_budget = 1_000_000
user_class = "Economy"

# closest cluster to user preferences
cluster_pref = (
    df.groupby("cluster")[["price"]].mean()
    .assign(diff=lambda x: abs(x["price"] - user_budget))
    .sort_values("diff")
    .index[0]
)

# recommend top 10 flights from that cluster and seat class
recommendations = df[(df["cluster"] == cluster_pref) & (df["seat_class"] == user_class)].head(10)

print("Recommended flights for user:")
print(recommendations[["airline", "price", "departure_time", "arrival_time","duration", "origin", "destination","seat_class", "cluster_label"]])

df.to_csv("data-cleaned/cleaned_flights_clustered.csv", index=False)


# JUST PLOTTT
plt.scatter(df["price"], df["duration_minutes"], c=df["cluster"], cmap="viridis")
plt.xlabel("Price (IDR)")
plt.ylabel("Duration (minutes)")
plt.title("Flight Clusters by Price & Duration")
plt.show()

# TO DO-> CLUSTER WITH MORE INPUTS, AUTOMATE CLUSTER NAMING
