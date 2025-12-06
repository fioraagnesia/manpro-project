import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings("ignore")

try:
    df_cleaned_combined = pd.read_csv('data_cleaned/cleaned_hotel_combined.csv')
    df_cleaned_combined['Checkin Date'] = pd.to_datetime(df_cleaned_combined['Checkin Date'], format='%Y-%m-%d', errors='coerce')
    df_cleaned_combined['Checkout Date'] = pd.to_datetime(df_cleaned_combined['Checkout Date'], format='%Y-%m-%d', errors='coerce')
except FileNotFoundError:
    print("File 'cleaned_hotel_combined.csv' not found.")
    exit()


print(f"=== Global Clustering for all hotels ===")
df_analisis = df_cleaned_combined.copy()

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
        print("\n=== Cluster Characteristics based on Weighted Score ===")
        cluster_stats = df_result.groupby('Cluster')[features].mean().round(2)

        ranked = pd.DataFrame()
        ranked['R_Price'] = cluster_stats['Price'].rank(ascending=True)
        ranked['R_Star'] = cluster_stats['Hotel Star'].rank(ascending=True)
        ranked['R_Rating'] = cluster_stats['Guest Rating'].rank(ascending=True)
        
        # Give weight to each aspects
        weight_price = 0.6
        weight_star = 0.3
        weight_rating = 0.1
        # Count the weighted values
        cluster_stats['Weighted Score'] = (
            (ranked['R_Price'] * weight_price) + 
            (ranked['R_Star'] * weight_star) + 
            (ranked['R_Rating'] * weight_rating)
        )
        # Sort based on the highest score
        cluster_summary = cluster_stats.sort_values('Weighted Score')
        print(cluster_summary)

        # Labeling for each segmentation
        segment_names = ['Budget',      # cheapest, lowest star and rating
                         'Mid-Range',   # mid price, mid star and rating
                         'Luxury']      # most expensive, highest star and rating
        segmentation_map = {}
        
        for i, cluster_id in enumerate(cluster_summary.index):
            assigned_name = segment_names[i]
            segmentation_map[cluster_id] = assigned_name
        
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
            print(section_data[['Hotel Name', 'City', 'Country', 'Price', 'Hotel Star', 'Guest Rating']])
            # print(section_data)
            print(f"Total for '{segment}' segmentation: {len(section_data)} hotels")

        # Save results as csv
        folder_name = 'data_clustered/'
        file_name = f'hotel_clustered_global new.csv'
        file_path = folder_name+ file_name
        df_result.to_csv(file_path, index=False)
        print(f"Successfully saved as {file_name}")
        
    else:
        print("Insufficient data for clustering (less than 3 data).")