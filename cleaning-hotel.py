import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")

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


# FUNCTION for converting date to dd/mm/yyyy format
def date_format(df, dataset_name):
    print(f"--- Formatting dates for '{dataset_name}' to dd/mm/yyyy ---")
    
    # Change the data type to datetime
    if 'Checkin Date' in df.columns:
        df['Checkin Date'] = pd.to_datetime(df['Checkin Date'], errors='coerce')
    if 'Checkout Date' in df.columns:
        df['Checkout Date'] = pd.to_datetime(df['Checkout Date'], errors='coerce')
    df.dropna(subset=['Checkin Date', 'Checkout Date'], inplace=True)

    # 3. Change the date format to dd/mm/yyyy
    if 'Checkin Date' in df.columns:
        df['Checkin Date'] = df['Checkin Date'].dt.strftime('%d/%m/%Y')
    if 'Checkout Date' in df.columns:
        df['Checkout Date'] = df['Checkout Date'].dt.strftime('%d/%m/%Y')

    return df


# DATA SCRAPING PATHS
dataset_paths = [
    'data-scraping/hotel/hotel_agoda_20250926_10days.xlsx',
    'data-scraping/hotel/hotel_traveloka_20250926_10days.xlsx',
    'data-scraping/hotel/hotel_tiketcom_(13 Oktober 2025 - 24 Oktober 2025).xlsx',
    'data-scraping/hotel/hotel_tripcom_(12 Oktober 2025 - 23 Oktober 2025).xlsx',
    'data-scraping/hotel/hotel_bookingcom_data_(27 Oktober 2025 - 6 November 2025).xlsx'
]

# DATA CLEANING on each datasets
cleaned_df = {}
for path in dataset_paths:
    try:
        # Access the data
        df_raw = pd.read_excel(path)
        dataset_name = path.split('_')[1].split('(')[0].title()

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