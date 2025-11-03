import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings("ignore")

try:
    df_cleaned_combined = pd.read_csv('data-cleaned/cleaned_hotel_combined.csv')
    df_cleaned_combined['Checkin Date'] = pd.to_datetime(df_cleaned_combined['Checkin Date'])
    df_cleaned_combined['Checkout Date'] = pd.to_datetime(df_cleaned_combined['Checkout Date'])
except FileNotFoundError:
    print("File 'cleaned_hotel_combined.csv' not found.")
    exit()


# CUSTOMIZE: Filter Analysis, adjust the city & check-in date
city_target = 'Surabaya'
date_target = pd.to_datetime('2025-10-22') 

print(f"=== Clustering for: {city_target}, {date_target.strftime('%Y-%m-%d')} ===")
# Make a new copy according to the specified filters 
df_analisis = df_cleaned_combined[
    (df_cleaned_combined['City'] == city_target) &
    (df_cleaned_combined['Checkin Date'] == date_target)
].copy()

if df_analisis.empty:
    print(f"No data for specified filters.")
else:
    # Parameters used for clustering
    features = ['Price', 'Hotel Star', 'Guest Rating']
    df_cluster_input = df_analisis[features].dropna()
    df_cluster_input = df_cluster_input[
        (df_cluster_input['Hotel Star'] > 0) & 
        (df_cluster_input['Guest Rating'] > 0)
    ]
    print(f"Total {len(df_cluster_input)} valid hotels will be clustered")

    if len(df_cluster_input) >= 3:
        # Scaling: to make sure all features have similar scale to be compared fairly   
        scaler = StandardScaler()
        df_scaled = scaler.fit_transform(df_cluster_input)

        # CLUSTERING with KMeans k=3
        kmeans_final = KMeans(n_clusters=3, random_state=42)
        kmeans_final.fit(df_scaled)
        # Labelling with (0, 1, 2)
        labels = kmeans_final.labels_
        
        # Put the labels as a new column
        df_cluster_input['Cluster'] = labels
        df_result = df_analisis.loc[df_cluster_input.index].copy()
        df_result['Cluster'] = labels

        # --- Investigation ---
        print("\n=== Cluster Characteristics ===")
        cluster_summary = df_result.groupby('Cluster')[features].mean().round(2)
        print(cluster_summary)

        # Labeling for each segmentation (based on the characteristics)
        segmentation_map = {
            0: 'Best Value',
            1: 'Luxury',
            2: 'Budget'
        }
        
        df_result['Segmentation'] = df_result['Cluster'].map(segmentation_map)

        # Example of Clustering Result Visualization 
        print("\n=== Clustering Results ===")
        print(df_result[['Hotel Name', 'Price', 'Segmentation']])
        print(f"Total: {len(df_result)} hotels")
        # print(df_result)

        # Print results for each segmentation
        for segment in segmentation_map.values():
            print(f"\n--- SEGMENTATION: '{segment}' ---")
            section_data = df_result[df_result['Segmentation'] == segment]
            print(section_data[['Hotel Name', 'Price', 'Hotel Star', 'Guest Rating']])
            # print(section_data)

        # Save results as csv
        folder_name = 'data_clustered/'
        file_name = f'hotel_clustered_{city_target}_{date_target.strftime("%Y%m%d")}.csv'
        file_path = folder_name+ file_name
        df_result.to_csv(file_path, index=False)
        print(f"Successfully saved as {file_name}")
        
    else:
        print("Insufficient data for clustering (less than 3 data).")