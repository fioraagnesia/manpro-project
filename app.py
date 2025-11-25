import pandas as pd
from flask import Flask, render_template, request, jsonify
import sys
from concurrent.futures import ThreadPoolExecutor
from duckduckgo_search import DDGS
from functools import lru_cache

# Impor fungsi pencarian
from search_flight import search_flights
from search_hotel import search_hotels
from search_combo import search_combo

app = Flask(__name__)

# --- FUNGSI HELPER & IMAGE SEARCH ---

def to_float(value):
    if not value:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# Cache sederhana untuk menyimpan URL gambar agar tidak perlu search ulang
image_cache = {}

def search_image_ddg(query):
    """Mencari 1 gambar eksterior hotel menggunakan DuckDuckGo"""
    # Cek cache dulu
    if query in image_cache:
        return image_cache[query]
    
    try:
        # Mencari gambar dengan keyword spesifik
        with DDGS() as ddgs:
            # Cari gambar 'query', ambil 1 saja
            results = list(ddgs.images(query, max_results=1))
            if results:
                img_url = results[0]['image']
                image_cache[query] = img_url
                return img_url
    except Exception as e:
        print(f"Gagal mencari gambar untuk {query}: {e}")
    
    # Gambar placeholder jika gagal
    return "https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=400&auto=format&fit=crop"

def add_images_to_results(df):
    """Menambahkan kolom 'image_url' ke DataFrame menggunakan Threading (Paralel)"""
    if df.empty:
        return df
    
    # Batasi pencarian gambar hanya untuk 15 hotel teratas agar tidak terlalu lama
    # Sisanya pakai placeholder
    top_n = 15
    df_top = df.head(top_n).copy()
    df_rest = df.iloc[top_n:].copy()
    
    # Siapkan list query pencarian (cth: "Luminor Hotel Surabaya exterior building")
    queries = [f"{row['Hotel Name']} {row['City']} hotel exterior building" for index, row in df_top.iterrows()]
    
    # Jalankan pencarian secara paralel (biar cepat)
    with ThreadPoolExecutor(max_workers=10) as executor:
        image_urls = list(executor.map(search_image_ddg, queries))
    
    df_top['image_url'] = image_urls
    
    # Untuk sisanya (jika hasil > 15), beri gambar default agar cepat
    if not df_rest.empty:
        df_rest['image_url'] = "https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=400&auto=format&fit=crop"
        
    return pd.concat([df_top, df_rest])

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search-flights', methods=['POST'])
def api_search_flights():
    try:
        data = request.json
        date_val = None
        if data.get('date'):
            date_val = pd.to_datetime(data['date']).strftime('%d/%m/%Y')
            
        result = search_flights(
            filepath="data_clustered/cleaned_flights_clustered.csv",
            origin=data.get('origin'),
            destination=data.get('destination'),
            min_price=to_float(data.get('min_price')),
            max_price=to_float(data.get('max_price')),
            date=date_val,
            airline=data.get('airline'),
            cluster_label=data.get('cluster_label')
        )
        
        if isinstance(result, pd.DataFrame):
            result_json = result.to_json(orient='records')
            return jsonify({'success': True, 'data': result_json})
        else:
            return jsonify({'success': False, 'message': str(result)})
            
    except Exception as e:
        print(f"Error Flight: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/search-hotels', methods=['POST'])
def api_search_hotels():
    try:
        data = request.json
        city = data.get('city')
        checkin = data.get('checkin_date')
        checkout = data.get('checkout_date')
        
        if not city: return jsonify({'success': False, 'message': 'Kota wajib diisi.'})
        if not checkin or not checkout: return jsonify({'success': False, 'message': 'Tanggal wajib diisi.'})

        stars_str_list = data.get('hotel_star') 
        stars_num_list = [float(s) for s in stars_str_list] if stars_str_list else None
        
        # 1. Cari Hotel (Logic Lama)
        result = search_hotels(
            filepath="data_clustered/hotel_clustered_global.csv", 
            city=city,
            checkin_date=checkin,
            checkout_date=checkout,
            min_total_price=to_float(data.get('min_total_price')),
            max_total_price=to_float(data.get('max_total_price')),
            hotel_star=stars_num_list
        )
        
        # 2. Tambahkan Gambar Real (Logic Baru)
        if isinstance(result, pd.DataFrame) and not result.empty:
            # Panggil fungsi pencari gambar
            result = add_images_to_results(result)
            
            result_json = result.to_json(orient='records')
            return jsonify({'success': True, 'data': result_json})
        else:
            return jsonify({'success': False, 'message': str(result)})
            
    except Exception as e:
        print(f"Error Hotel: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/search-combo', methods=['POST'])
def api_search_combo():
    try:
        data = request.json
        origin = data.get('origin')
        destination = data.get('destination')
        checkin = data.get('checkin_date')
        
        if not origin or not destination: return jsonify({'success': False, 'message': 'Asal/Tujuan wajib.'})
        if not checkin: return jsonify({'success': False, 'message': 'Tanggal wajib.'})
        
        result = search_combo(
            filepath="data_clustered/flight_hotel_clustered.csv",
            origin=origin,
            destination=destination,
            checkin_date=checkin,
            min_total_price=to_float(data.get('min_total_price')),
            max_total_price=to_float(data.get('max_total_price')),
            hotel_name=data.get('hotel_name'),
            airline=data.get('airline'),
            cluster=data.get('cluster')
        )
        
        # Note: Untuk combo, kita tidak mencari gambar hotel agar tidak terlalu berat
        # karena datanya bisa sangat banyak. Bisa ditambahkan jika perlu.
        
        if isinstance(result, pd.DataFrame):
            result_json = result.to_json(orient='records')
            return jsonify({'success': True, 'data': result_json})
        else:
            return jsonify({'success': False, 'message': str(result)})
            
    except Exception as e:
        print(f"Error Combo: {e}", file=sys.stderr)
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)