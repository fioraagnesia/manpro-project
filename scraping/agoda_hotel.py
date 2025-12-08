from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time, random
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd 
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
import os
def main():
    start = time.time()   
    
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)

    city_codes = {
        "Jakarta": "8691",
        "Bali": "17193",
        "Surabaya": "10779",
        "Bandung": "18943",
        "Yogyakarta": "14018",
        "Semarang" : "19359",
        "Malang" : "5414",

        "Singapura": "4064",
        "Kuala Lumpur": "14524",
        "Bangkok": "9395",
    }

    url_to_country = {
        "Jakarta": "Indonesia",
        "Bali": "Indonesia",
        "Surabaya": "Indonesia",
        "Bandung": "Indonesia",
        "Yogyakarta": "Indonesia",
        "Semarang" : "Indonesia",
        "Malang" : "Indonesia",

        "Singapura": "Singapura",
        "Kuala Lumpur": "Malaysia",
        "Bangkok": "Thailand",
    }

    collected = []
    today = datetime(2025,11,14)

    for day in range(10): 
        checkin = (today + timedelta(days=day)).strftime("%m-%d-%Y")
        checkout = (today + timedelta(days=day+1)).strftime("%m-%d-%Y")
        print(f"\n📅 Scraping tanggal {checkin} → {checkout} hari ke {day + 1}")

        for city, code in city_codes.items():
            base = "https://www.agoda.com/search?"  
            search_page_url = f"{base}city={code}&checkIn={checkin}&checkOut={checkout}&rooms=1&adults=2&children=0&priceCur=IDR&los=1&textToSearch={city}"            
            print(f"🌐 Sedang scrape: {city} ({search_page_url})")

            try:
                driver.get(search_page_url)
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[class="hotel-list-container"]'))
                )
            except Exception as e:
                print(f"Error saat load halaman: {e}")
                continue
            print("Memuat semua data hotel dengan scrolling...")
            time.sleep(random.uniform(2, 4)) 

            print("Memuat data hotel (Smart Scroll v2)...")
        
            
            for i in range(5):
                # 1. Cek jumlah hotel
                hotels = driver.find_elements(By.CSS_SELECTOR, 'li[class="PropertyCard PropertyCardItem"]')
                current_count = len(hotels)
                
                
                last_count = current_count
                driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(random.uniform(2, 3))
            
            print("Mengambil source halaman setelah semua data dimuat...")
            soup = BeautifulSoup(driver.page_source, "html.parser")

            hotel_cards = soup.select('li[class="PropertyCard PropertyCardItem"]')            
            hotel_cards = hotel_cards[:15]
            
            print(f"Menemukan {len(hotel_cards)} hotel untuk diproses (Maks 15).")

            seen_per_day = set()
            for card in hotel_cards:
                try:
                    # Ambil Nama
                    name_element = card.select_one('h3[data-selenium="hotel-name"]')
                    if name_element:
                        hotel_name = name_element.get_text(strip=True)

                    # Ambil Harga
                    price_element = card.select_one('[data-selenium="display-price"]')
                    if price_element:
                        hotel_price_raw = price_element.get_text(strip=True)
                        if hotel_price_raw:
                            hotel_price = int(re.sub(r"[^\d]", "", hotel_price_raw))

                    # Ambil Rating Bintang
                    stars_div = card.select_one('[data-testid="rating-container"]')

                    if stars_div:
                        span_element = stars_div.select_one('span[class*="ScreenReaderOnly"]')
                        
                        if span_element:
                            raw_text = span_element.get_text(strip=True) 
                            match = re.search(r"(\d+)\s*stars", raw_text, re.IGNORECASE)
                            
                            if match:
                                star_count = int(match.group(1))

                    guest_rating = 0.0 

                    rating_block = card.select_one('[data-element-name="property-card-review"]')
                    if rating_block:
                        span_element = rating_block.select_one('span[class*="ScreenReaderOnly"]')
                        if span_element:
                            raw_text = span_element.get_text(strip=True).replace(",", ".")
                            match = re.search(r"(\d+(?:[.]\d+)?)\s*out of\s*10", raw_text, re.IGNORECASE)
                            
                            if match:
                                guest_rating = float(match.group(1))

                    link_tag = card.select_one('a[class="PropertyCard__Link"]')
                    if link_tag and 'href' in link_tag.attrs:
                        relative_url = link_tag['href']
                        if relative_url.startswith('/'):
                            hotel_source_url = "https://www.agoda.com" + relative_url
                        else:
                            hotel_source_url = relative_url

                    scraped_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    key = (hotel_name, checkin, checkout)
                    if key in seen_per_day:
                                continue
                    seen_per_day.add(key) 
                    record = (
                        hotel_name, 
                        hotel_price, 
                        city, 
                        url_to_country.get(city, "Unknown"), 
                        star_count, 
                        guest_rating, 
                        scraped_timestamp, 
                        checkin,
                        checkout,
                        hotel_source_url 
                    )
                    
                    collected.append(record)
                    print(f"   -> {hotel_name} | {hotel_price} | {star_count}* | Rating {guest_rating}")

                except Exception as e:
                    print(f"Error saat memproses kartu: {e}")
                
            print(f"📌 Hotel terkumpul dari {city}: {len(seen_per_day)}")
            print(f"Total hotel terkumpul: {len(collected)}")

            time.sleep(random.uniform(3, 4)) 
    df_new = pd.DataFrame(collected, columns=[
        "hotel_name", "price", "city", "country", "hotel_star",
        "guest_rating", "Scraped Timestamp", "checkin_date", "checkout_date", "source_url"
    ])


    filename = f"hotel_agoda.xlsx"

    if os.path.exists(filename):
        print(f"📁 File '{filename}' sudah ada. Menambahkan data baru...")
        try:
            df_existing = pd.read_excel(filename)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            
            print(f"Data lama: {len(df_existing)} baris, Data baru: {len(df_new)} baris. Total: {len(df_combined)} baris.")

        except Exception as e:
            print(f"❌ Gagal membaca file lama: {e}. Menimpa file...")
            df_combined = df_new

    else:
        print(f"📁 File '{filename}' tidak ditemukan. Membuat file baru...")
        df_combined = df_new

    if 'Hotel_ID' in df_combined.columns:
        df_combined = df_combined.drop(columns=['Hotel_ID'])
        
    df_combined.insert(0, "Hotel_ID", range(1, len(df_combined) + 1))
    try:
        df_combined.to_excel(filename, index=False, engine="openpyxl")
        print(f"✅ Data berhasil disimpan/di-update ke {filename}")
    except Exception as e:
        print(f"❌ GAGAL menyimpan ke Excel: {e}")
        print("Pastikan file tersebut tidak sedang dibuka di komputer Anda.")
    driver.quit() 
    
    end = time.time()    
    print(f"\nWaktu eksekusi: {end - start:.4f} detik")
    
if __name__ == "__main__":
    main()