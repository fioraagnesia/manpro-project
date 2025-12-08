# -- coding: utf-8 --

# Import modul yang diperlukan
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, random
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import re

# --- PERUBAHAN 1: Import selenium-stealth ---
from selenium_stealth import stealth

def save_to_excel(collected, filename="hotel_traveloka.xlsx"):
    """
    Fungsi untuk menyimpan data hotel ke file Excel.
    Jika file sudah ada, data akan di-append.
    """
    # Membuat DataFrame dari data yang dikumpulkan
    df = pd.DataFrame(collected, columns=[
        "hotel_name", "price", "city", "country", "hotel_star", "guest_rating", 
        "Scraped Timestamp", "checkin_date", "checkout_date", "source_url"
    ])

    # Cek apakah file sudah ada
    try:
        # Jika file ada, load data dan append
        existing_df = pd.read_excel(filename)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        # Jika file tidak ada, buat file baru
        combined_df = df

    # Simpan ke Excel (gunakan engine 'openpyxl')
    combined_df.to_excel(filename, index=False, engine="openpyxl")
    print(f"Data berhasil disimpan ke {filename}")

def main():
    """
    Fungsi utama untuk menjalankan proses web scraping data hotel dari Traveloka,
    dioptimalkan untuk menghindari deteksi bot.
    """
    start = time.time()
    
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36")
    # Opsi untuk menghindari error/pesan tidak penting di console
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    stealth(driver,
            languages=["id-ID", "id"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    city_codes = {
        "Jakarta": "102813",
        "Bali": "102746",
        "Surabaya": "103570",
        "Bandung": "103859",
        "Yogyakarta": "107442", 
        "Semarang" : "106587", 
        "Malang" : "103760",
        "Singapura": "107493", 
        "Kuala Lumpur": "107979",
        "Bangkok": " 10000045",
    }

    url_to_country = {
        "Medan" : "Indonesia", "Jakarta": "Indonesia", "Bali": "Indonesia", "Surabaya": "Indonesia",
        "Bandung": "Indonesia", "Yogyakarta": "Indonesia", "Semarang" : "Indonesia", "Malang" : "Indonesia",
        "Singapura": "Singapura", "Kuala Lumpur": "Malaysia", "Bangkok": "Thailand",
    }


    collected = []
    today = datetime(2025,11,14)
    seen_records = set() 
    
    for day in range(10): 
        checkin = (today + timedelta(days=day)).strftime("%d-%m-%Y")
        checkout = (today + timedelta(days=day+1)).strftime("%d-%m-%Y")
        print(f"\n📅 Scraping tanggal {checkin} → {checkout} (Hari ke-{day + 1})")

        for city, code in city_codes.items():
            search_url = f"https://www.traveloka.com/id-id/hotel/search?spec={checkin}.{checkout}.1.1.HOTEL_GEO.{code}.{city}.1" 
            print(f"🌐 Memproses kota: {city}")

            try:
                driver.get(search_url)
                time.sleep(10)
            except Exception as e:
                print(f"❌ Gagal membuka URL untuk {city}. Error: {e}")
                continue

            try:
                hotel_card_selector = "div.css-1dbjc4n.r-1d2f490.r-u8s1d.r-ipm5af.r-13qz1uu"
                processed_hotel_names = set()
                consecutive_scrolls_with_no_new_hotels = 0
                main_tab = driver.current_window_handle
                scraped_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                MAX_HOTELS_PER_CITY = 16
                print(f"   (Batas scraping diatur ke {MAX_HOTELS_PER_CITY} hotel)")

                while len(processed_hotel_names) < MAX_HOTELS_PER_CITY and consecutive_scrolls_with_no_new_hotels < 3:
                    
                    visible_cards = driver.find_elements(By.CSS_SELECTOR, hotel_card_selector)
                    new_hotels_found_this_scroll = False

                    for card in visible_cards:
                        if len(processed_hotel_names) >= MAX_HOTELS_PER_CITY: break
                        try:
                            hotel_name_element = card.find_element(By.CSS_SELECTOR, "h3.css-4rbku5")
                            hotel_name = hotel_name_element.text.strip()

                            if hotel_name and hotel_name not in processed_hotel_names:
                                new_hotels_found_this_scroll = True
                                print(f"   -> Memproses hotel baru ({len(processed_hotel_names)+1}/{MAX_HOTELS_PER_CITY}): {hotel_name}")
                                processed_hotel_names.add(hotel_name)
                                card_html = card.get_attribute('innerHTML')
                                soup = BeautifulSoup(card_html, "html.parser")
                                price_element = soup.find("div", class_="css-901oao r-uh8wd5 r-b88u0q r-1ff274t")
                                raw_price = price_element.text.strip() if price_element else ""
                                hotel_price = int(re.sub(r"[^\d]", "", raw_price)) if raw_price else None
                                rating_element = soup.find("div", class_="css-901oao r-b88u0q r-fdjqy7")
                                guest_rating = rating_element.text.strip().split("(")[0].strip() if rating_element and "(" in rating_element.text else 0                                
                                stars_container = soup.find("div", class_="css-1dbjc4n r-18u37iz r-9aw3ui")
                                star_count = len(stars_container.find_all("svg")) if stars_container else 0

                                card.click()
                                wait.until(EC.number_of_windows_to_be(2))
                                all_tabs = driver.window_handles
                                driver.switch_to.window(all_tabs[-1])
                                wait.until(EC.url_contains("hotel/"))
                                detail_url = driver.current_url
                                driver.close()
                                driver.switch_to.window(main_tab)

                                record = (hotel_name, hotel_price, city, url_to_country.get(city, "Unknown"), star_count, guest_rating, scraped_timestamp, checkin, checkout, detail_url)
                                if record not in seen_records:
                                    collected.append(record)
                                    seen_records.add(record)

                        except Exception:
                            continue
                    
                    if len(processed_hotel_names) >= MAX_HOTELS_PER_CITY:
                        print(f"   (Batas {MAX_HOTELS_PER_CITY} hotel telah tercapai, menghentikan scroll.)")
                        break

                    scroll_distance = random.randint(600, 1000)
                    driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
                    time.sleep(random.uniform(2, 4))

                    if not new_hotels_found_this_scroll:
                        consecutive_scrolls_with_no_new_hotels += 1
                        print(f"   (Scroll ke-{consecutive_scrolls_with_no_new_hotels}, tidak ada hotel baru ditemukan...)")
                    else:
                        consecutive_scrolls_with_no_new_hotels = 0
                
                print(f"👍 Selesai memproses {city}. Total hotel terkumpul sekarang: {len(collected)}")

            except Exception as e:
                print(f"⚠ Gagal melakukan scraping data untuk {city}. Error: {e}")
                continue

    save_to_excel(collected)

    driver.quit()
    end = time.time()
    print(f"\nTotal waktu eksekusi: {(end - start) / 60:.2f} menit")


if __name__ == "__main__":
    main()