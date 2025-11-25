import pandas as pd

def search_flights(
    filepath,
    origin=None,
    destination=None,
    min_price=None,
    max_price=None,
    airline=None,
    date=None,
    cluster_label=None
):
    # Load file
    df = pd.read_csv(filepath)

    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%y", errors="coerce")

    # Normalize
    df["origin"] = df["origin"].astype(str).str.upper()
    df["destination"] = df["destination"].astype(str).str.upper()
    df["airline"] = df["airline"].astype(str).str.title()
    df["cluster_label"] = df["cluster_label"].astype(str).str.title()

    result = df.copy()

    # Filter with input user
    if origin:
        result = result[result["origin"] == origin.upper()]

    if destination:
        result = result[result["destination"] == destination.upper()]

    if airline:
        result = result[result["airline"].str.contains(airline, case=False, na=False)]

    if min_price is not None:
        result = result[result["price"] >= min_price]

    if max_price is not None:
        result = result[result["price"] <= max_price]

    if date:
        date = pd.to_datetime(date, dayfirst=True, errors="coerce")
        result = result[result["date"] == date]
    
    if cluster_label:
        result = result[result["cluster_label"] == cluster_label.title()]

    if result.empty:
        return "No flights found with the specified filters."

    return result

file_path = "data_clustered/cleaned_flights_clustered.csv"

# GANTI INPUT OLEH FRONT END
if __name__ == "__main__":

    filtered = search_flights(
        file_path,
        origin="SIN",
        destination="CGK",
        min_price=1000000,
        max_price=3000000,
        airline="AirAsia",
        date="01/11/2025",
        cluster_label="" #Budget Flight, Mid-range Flight, High-end flight
    )
# contoh search 01/11/25,AirAsia,07:40,13:00,6h 20m,1,2191927,SIN,CGK,Business,40,Jakarta
    print(filtered)