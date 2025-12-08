# scrape_booking.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time, random
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd 
import re
import os
import undetected_chromedriver as uc

def main():
    start = time.time()   
    
    # KADANG KADANG TERDETEKSI BOT, KADANG KADANG NGGA TERDETEKSI BOTE. KALAU TERDEKTEKSI BOT KELUARNYA NGGA ADA HARGANYA
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36")
    options.add_argument(r"C:\Users\marce\AppData\Local\Google\Chrome\User Data\Default")
    options.add_argument(r"profile-directory=Default")
    driver = uc.Chrome(options=options)

    city_to_country = {
        "Jakarta": "Indonesia",
        "Bali": "Indonesia",
        "Surabaya": "Indonesia",
        "Bandung": "Indonesia",
        "Yogyakarta": "Indonesia",
        "Semarang": "Indonesia",
        "Malang": "Indonesia",
        "Singapura": "Singapura",
        "Kuala Lumpur": "Malaysia",
        "Bangkok": "Thailand",
    }

    collected = []
    today = datetime(2025,11,13)

    for day in range(11): 
        checkin = (today + timedelta(days=day)).strftime("%Y-%m-%d")
        checkout = (today + timedelta(days=day+1)).strftime("%Y-%m-%d")
        print(f"\n📅 Scraping tanggal {checkin} → {checkout} (hari ke-{day+1})")

        for city, country in city_to_country.items():
            base = "https://www.booking.com/searchresults.html?"
            search_page_url = (
                f"{base}ss={city}"
                f"&checkin_year_month_monthday={checkin}"
                f"&checkout_year_month_monthday={checkout}"
                f"&group_adults=2&no_rooms=1"
            )
            print(f"🌐 Sedang scrape: {city} ({search_page_url})")

            try:
                driver.get(search_page_url)
                time.sleep(5)
            except Exception as e:
                print(f"❌ Gagal membuka {search_page_url}, error: {e}")          
                continue

            try:
                seen_per_day = set()
                stop_scrolling =   False
                for _ in range(10):  # scroll 
                    if stop_scrolling:
                        break
                    driver.execute_script("window.scrollBy(0, 800);")
                    time.sleep(random.uniform(1,2))

                    element = BeautifulSoup(driver.page_source, "html.parser")

                    names = element.find_all("div", {"data-testid": "title"})
                    prices = element.find_all("span", {"data-testid": "price-and-discounted-price"})
                    locations = element.find_all("span", {"data-testid": "address"})
                    ratings = element.find_all("div", {"data-testid": "review-score"})
                    stars = element.find_all("div", attrs={"aria-label": re.compile(r"\d+ out of \d+")})
                    hotel_links = element.find_all("a", {"data-testid": "title-link"})

                    scraped_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    n = min(len(names), len(prices), len(locations), len(ratings), len(hotel_links))

                    for i in range(n):
                        hotel_name = names[i].get_text(strip=True) if names[i] else None
                        hotel_price_raw = prices[i].get_text(strip=True) if prices[i] else None
                        hotel_price = int(re.sub(r"[^\d]", "", hotel_price_raw)) if hotel_price_raw else None
                        hotel_loc = locations[i].get_text(strip=True) if locations[i] else None
                        
                        guest_rating = None
                        if ratings and i < len(ratings):
                            rating_text = ratings[i].get_text(strip=True)
                            m = re.search(r"\d+(\.\d+)?", rating_text)
                            guest_rating = m.group(0) if m else 0
                        else:
                            guest_rating = 0

                        star_count = None
                        if stars and i < len(stars):
                            aria_text = stars[i].get("aria-label", "")
                            m = re.search(r"(\d+)", aria_text)
                            star_count = int(m.group(1)) if m else 0

                        hotel_source_url = "N/A"
                        if hotel_links[i] and 'href' in hotel_links[i].attrs:
                            relative_url = hotel_links[i]['href']
                            if relative_url.startswith('/'):
                                hotel_source_url = "https://www.booking.com" + relative_url
                            else:
                                hotel_source_url = relative_url

                        key = (hotel_name, checkin, checkout)
                        if key in seen_per_day:
                            continue


                        if len(seen_per_day) >= 15:
                            stop_scrolling = True   
                            break
                        seen_per_day.add(key) 

                        record = (
                            hotel_name, 
                            hotel_price, 
                            city, 
                            country, 
                            star_count, 
                            guest_rating, 
                            scraped_timestamp, 
                            checkin, 
                            checkout, 
                            hotel_source_url 
                        )
                        if record not in collected:
                            collected.append(record)

                print(f"📌 Hotel terkumpul sampai sekarang: {len(collected)}")

            except Exception as e:
                print(f"⚠️ Gagal scrape data dari {search_page_url}, error: {e}")
                continue

            time.sleep(random.uniform(5, 6)) 

    print("\n=== HASIL AKHIR ===")
    df_new = pd.DataFrame(collected, columns=[
        "hotel_name", "price", "city", "country", "hotel_star",
        "guest_rating", "Scraped Timestamp", "checkin_date", "checkout_date", "source_url"
    ])

    filename = "hotel_booking_data.xlsx"  

    if os.path.exists(filename):
        df_existing = pd.read_excel(filename)

        df_combined = pd.concat([df_existing, df_new], ignore_index=True)

        df_combined.drop_duplicates(subset=["hotel_name", "checkin_date", "checkout_date"], inplace=True)

        df_combined.to_excel(filename, index=False, engine="openpyxl")
        print(f"✅ Data ditambahkan ke file yang sudah ada: {filename}")
    else:
        df_new.insert(0, "Hotel_ID", range(1, len(df_new) + 1))
        df_new.to_excel(filename, index=False, engine="openpyxl")
        print(f"✅ File baru dibuat: {filename}")

    driver.quit()

    end = time.time()     
    print(f"\nWaktu eksekusi: {end - start:.4f} detik")

if __name__ == "__main__":
    main()
