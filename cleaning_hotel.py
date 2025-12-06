import pandas as pd
import numpy as np
import warnings
import re

warnings.filterwarnings("ignore")

# FUNCTION for hotel star column validation
def clean_hotel_star(df, dataset_name, column_name='Hotel Star'):
    print(f"--- Checking hotel star column of {dataset_name} ---")
    
    # Define the valid star values
    valid_stars = [1, 2, 3, 4, 5, 1.0, 2.0, 3.0, 4.0, 5.0]
    # Replace the non-valid values to null
    df.loc[~df[column_name].isin(valid_stars), column_name] = np.nan

    # Fill the null values of "Hotel Star" with the mode value
    if not df[column_name].isnull().all():
        # Replace null values with the mode value of Hotel Star
        mode_star = df[column_name].mode()[0] 
        df[column_name] = df[column_name].fillna(mode_star)     
        # Change the data type to integer
        df[column_name] = df[column_name].astype(int)
        
    return df


# FUNCTION for guest rating column validation
def clean_guest_rating(df, dataset_name, column_name='Guest Rating'):
    print(f"--- Checking guest rating column for {dataset_name} ---")
    
    # Replace the decimals with . (from ,)
    df[column_name] = df[column_name].astype(str).str.replace(',', '.')
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')

    # If the guest rating value is out of 5, then it must be multiplied by 2 to make it out of 10
    if (df[column_name].max() <= 5):
        df[column_name] = df[column_name] * 2

    # Data type must be numeric, others will replaced by null
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
   # Limit the value between 0 until 10
    df[column_name] = df[column_name].clip(lower=0, upper=10)

    #  Fill the null values of "Guest Rating" with the median value
    median_rating = df[column_name].median()
    df[column_name] = df[column_name].fillna(median_rating)

    # Round the values to one decimal place
    df[column_name] = df[column_name].round(1)
    
    return df


# FUNCTION for converting date
def date_format(df, dataset_name):
    date_cols = ['Checkin Date', 'Checkout Date']
    
    for col in date_cols:
        if col in df.columns:
            # convert to string
            df[col] = df[col].astype(str).str.strip()
            
            # special case: Traveloka (date format: dd-mm-yyyy)
            if 'Traveloka' in dataset_name:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
            else:
                df[col] = pd.to_datetime(df[col], dayfirst=False, errors='coerce')

    # Hapus data yang gagal dikonversi (NaT)
    df.dropna(subset=[c for c in date_cols if c in df.columns], inplace=True)

    # print(f"--- Formatting dates for '{dataset_name}' to dd/mm/yyyy ---")
    
    # # Change the data type to datetime
    # if 'Checkin Date' in df.columns:
    #     df['Checkin Date'] = pd.to_datetime(df['Checkin Date'], errors='coerce', dayfirst=True)
    # if 'Checkout Date' in df.columns:
    #     df['Checkout Date'] = pd.to_datetime(df['Checkout Date'], errors='coerce', dayfirst=True)
    # df.dropna(subset=['Checkin Date', 'Checkout Date'], inplace=True)

    return df

# FUNCTION for normalizing name
def normalize_name(name):
    name = str(name).lower()
    name = re.sub(r'[^\w\s]', '', name)
    stop_words = ['hotel', 'resort', 'inn', 'guesthouse']
    words = name.split()
    filtered_words = [word for word in words if word not in stop_words]
    filtered_words.sort()
    name = " ".join(filtered_words).strip()
    return name


# DATA SCRAPING PATHS
dataset_folder = 'data_scraping/hotel/'
dataset_files = [
    'hotel_agoda.xlsx',
    'hotel_traveloka.xlsx',
    'hotel_tiketcom.xlsx',
    'hotel_tripcom.xlsx',
    'hotel_bookingcom.xlsx'
]

# DATA CLEANING on each datasets
cleaned_df = {}
for dataset in dataset_files:
    try:
        # Access the data
        path = dataset_folder + dataset
        # df_raw = pd.read_excel(path)
        df_raw = pd.read_excel(path, dtype={'Checkin Date': str, 'Checkout Date': str})
        dataset_name = dataset.split('_')[1].split('.')[0].title()

        # Drop columns that are not needed
        drop_columns = ['Hotel_ID', 'Scraped Timestamp', 'Source URL']
        # Determine the required columns (remove any row if one of these columns is null)
        required_columns = ['Hotel Name', 'Price', 'Checkin Date', 'Checkout Date']
        df = df_raw.drop(drop_columns, axis=1, errors='ignore').dropna(subset=required_columns)

        # Check validation for all datasets
        print(f"\n--- Validating columns of {dataset_name} ---")
        df = clean_hotel_star(df, dataset_name)
        df = clean_guest_rating(df, dataset_name)
        df = date_format(df, dataset_name)

        # Save it in a new dict
        cleaned_df[dataset_name.lower()] = df
    
    except FileNotFoundError:
        print(f"FAILED: File not found in {path}.")
    except Exception as e:
        print(f"FAILED: processing file {path}. Error: {e}")


# Check the null-values on each column
for name, df in cleaned_df.items():
    print(f"\nNull values on each column of {name.title()}:")
    print(df.isnull().sum())


# Print the results (in rows)
for name, df in cleaned_df.items():
    print(f"Hotels listed on {name.title()}:")
    print(df)

# Merge data from all platforms
print("\n--- Merge data from all platforms... ---")
df_all_multi = pd.concat(cleaned_df)
df_all = df_all_multi.reset_index()
df_all = df_all.rename(columns={'level_0': 'Platform'})
df_all = df_all.drop(columns=['level_1'], errors='ignore') 

# Skip if the price is below 100.000 (considered not valid)
# df_all = df_all[df_all['Price'] > 100000].copy() 

# Normalize the hotel names
print("--- Normalizing hotel names... ---")
df_all['Cleaned Name'] = df_all['Hotel Name'].apply(normalize_name)

# Find the best price for a hotel from across the platforms (deduplication)
print(f"--- Finding the best price for each hotel... ---")
# 1. Sort price by ascending to get the cheapest price
df_sorted = df_all.sort_values(by='Price', ascending=True)
# 2. Compare the unique columns
unique_cols = ['Cleaned Name', 'City', 'Country', 'Checkin Date', 'Checkout Date'] 
# 3. Remove duplicates (with the same unique cols) and save the cheapest price
df_best_price = df_sorted.drop_duplicates(subset=unique_cols, keep='first')

print(f"Data after deduplication: {len(df_best_price)} rows")

# Make sure a hotel has the same hotel star and guest rating for each entry
print("Standardizing hotel stars and guest rating...")
# Standardizing hotel star with the maximum value
df_best_price['Hotel Star'] = df_best_price.groupby('Hotel Name')['Hotel Star'].transform('max')
# Standardizing guest rating with the maximum value
df_best_price['Guest Rating'] = df_best_price.groupby('Hotel Name')['Guest Rating'].transform('max')

# Convert to the date format
print("Formatting dates to yyyy-mm-dd...")
if 'Checkin Date' in df_best_price.columns:
    df_best_price['Checkin Date'] = df_best_price['Checkin Date'].dt.strftime('%Y-%m-%d')

if 'Checkout Date' in df_best_price.columns:
    df_best_price['Checkout Date'] = df_best_price['Checkout Date'].dt.strftime('%Y-%m-%d')

# Save as csv
file_name = 'data_cleaned/cleaned_hotel_combined.csv'
df_best_price.to_csv(file_name, index=False)
print(f"Successfully saved as {file_name}")