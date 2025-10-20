import pandas as pd
import numpy as np

# FUNCTION for hotel star column validation
def clean_hotel_star(df, dataset_name, column_name='Hotel Star'):
    print(f"--- Checking hotel star column of {dataset_name} ---")
    
    # Define the valid star values
    valid_stars = [1, 2, 3, 4, 5, 1.0, 2.0, 3.0, 4.0, 5.0]
    # Replace the non-valid values to null
    df.loc[~df[column_name].isin(valid_stars), column_name] = np.nan

    # Fill the null values of "Hotel Star" with the mode value
    if not df[column_name].isnull().all(): # Check if the column is completely empty
        mode_star = df[column_name].mode()[0]   # find the mode value of Hotel Star
        df[column_name].fillna(mode_star, inplace=True)
        
    # Change the data type to integer
    df[column_name] = df[column_name].astype(int)
    
    # print("--------\n")
    return df


# FUNCTION for guest rating column validation
def clean_guest_rating(df, dataset_name, column_name='Guest Rating'):
    print(f"--- Checking guest rating column for {dataset_name} ---")
    
    # Data type must be numeric, others will replaced by null
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
   # Limit the value between 0 until 10
    df[column_name] = df[column_name].clip(lower=0, upper=10)

    #  Fill the null values of "Guest Rating" with the median value
    if not df[column_name].isnull().all():
        median_rating = df[column_name].median()
        df[column_name].fillna(median_rating, inplace=True)

    # Round the values to one decimal place
    df[column_name] = df[column_name].round(1)
    
    # print("--- Proses Selesai --- \n")
    return df


# Load dataset
df1 = pd.read_excel('data-scraping\hotel\hotel_agoda_20250926_10days.xlsx')
df2 = pd.read_excel('data-scraping\hotel\hotel_traveloka_20250926_10days.xlsx')

# Drop columns that are not needed
drop_columns = ['Hotel_ID', 'Scraped Timestamp', 'Source URL']
# Determine the required columns (remove any row if one of these columns is null)
required_columns = ['Hotel Name', 'Price', 'Checkin Date', 'Checkout Date']
df_agoda = df1.drop(drop_columns, axis=1).dropna(subset=required_columns)
df_traveloka = df2.drop(drop_columns, axis=1).dropna(subset=required_columns)

# Check validation for Agoda
print("\n--- Validating columns of Agoda ---")
df_agoda = clean_hotel_star(df_agoda, 'Agoda')
df_agoda = clean_guest_rating(df_agoda, 'Agoda')

# Check validation for Traveloka
print("\n--- Validating columns of Traveloka ---")
df_traveloka = clean_hotel_star(df_traveloka, 'Traveloka')
df_traveloka = clean_guest_rating(df_traveloka, 'Traveloka')

# Check the null-values on each column
print("\nNull values on each column of Agoda:")
print(df_agoda.isnull().sum())
print("\nNull values on each column of Traveloka:")
print(df_traveloka.isnull().sum())

# Print rows
print("Hotels listed on Agoda:")
print(df_agoda)
print("Hotels listed on Traveloka:")
print(df_traveloka)
