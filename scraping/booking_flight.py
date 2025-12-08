import time
import re
import pandas as pd
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup

# --- Setup Driver ---
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")
# options.add_argument("--headless") # Aktifkan untuk run tanpa membuka browser
driver = webdriver.Chrome(options=options)

start_date = datetime(2025, 11, 14)
num_days = 10
dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]

routes = [
    ("JKT", "SIN"),
    ("SIN", "JKT"),
    ("SUB" , "DPS"),
    ("DPS", "SUB"),
    ("SUB", "SIN"),
    ("SIN", "SUB"),
    ("SUB", "SRG"),
    ("SRG", "SUB"),
    ("SUB", "JKT"),
    ("JKT", "SUB"),
]

seat_classes = [
    "ECONOMY",
    "BUSINESS"]

flights = []
print("✈️ Memulai proses scraping Booking.com...")

for date in dates:
    for origin, destination in routes:
        for sc in seat_classes:
            
            url = (
                f"https://flights.booking.com/flights/{origin}.CITY-{destination}.CITY?"
                f"type=ONEWAY&adults=1&cabinClass={sc}&from={origin}.CITY&to={destination}.CITY"
                f"&depart={date}&sort=BEST"
            )
            
            print(f"\n--- Mengambil data untuk: {origin} -> {destination} ({sc}) pada {date} ---")
            print(f"URL: {url}")
            
            try:
                driver.get(url)
                time.sleep(5) 

                try:
                    driver.find_element(By.XPATH, "//div[@data-testid='searchresults_no_results_found']")
                    print(f"🟡 TIDAK ADA PENERBANGAN: Rute {origin} -> {destination} kelas {sc} tanggal {date}. Melanjutkan...")
                    continue
                except NoSuchElementException:
                    pass 

                
                for i in range(2): 
                    driver.execute_script("window.scrollBy(0, 2000);")
                    print(f"   Scroll ke-{i+1}...")
                    time.sleep(3) 
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//div[@data-testid='searchresults_card']"))
                        )
                    except TimeoutException:
                        print("   Tidak ada kartu baru/selesai scroll.")
                        break 
                
                try:
                    card_elements = driver.find_elements(By.XPATH, "//div[@data-testid='searchresults_card']")
                    total_cards = len(card_elements)
                    if total_cards == 0:
                        print("   Tidak ada kartu ditemukan sama sekali.")
                        continue 
                        
                    print(f"   Menemukan {total_cards} total kartu penerbangan.")
                except Exception as e:
                    print(f"   Tidak ada kartu ditemukan setelah scroll. Error: {e}")
                    continue

                for idx in range(total_cards):
                    
                    airline = None
                    departure_time = None
                    arrival_time = None
                    duration = None
                    transit = None
                    price = None
                    origin_code = None
                    dest_code = None
                    seat_class = None
                    baggage = 0

                    try:
                        all_cards = driver.find_elements(By.XPATH, "//div[@data-testid='searchresults_card']")
                        
                        card = all_cards[idx]
                        
                        soup_card = BeautifulSoup(card.get_attribute("outerHTML"), "html.parser")
                        
                        # 1. Airline
                        airline_tag = soup_card.find("div", {"data-testid": "flight_card_carriers"})
                        airline = airline_tag.get_text(strip=True) if airline_tag else None

                        # 2. Departure Time & Arrival Time 
                        time_box = soup_card.find("div", {"data-testid": "flight_card_segment_departure_time_0"})
                        if time_box:
                            times = time_box.find("div", class_=re.compile("Text-module__root--variant-strong"))
                            departure_time = times.get_text(strip=True)

                        time_box1 = soup_card.find("div", {"data-testid": "flight_card_segment_destination_time_0"})
                        if time_box1:
                            times1 = time_box.find("div", class_=re.compile("Text-module__root--variant-strong"))
                            arrival_time = times.get_text(strip=True)

                        # 3. Duration
                        duration_tag = soup_card.find(attrs={"data-testid": "flight_card_segment_duration_0"})
                        
                        if duration_tag:
                            duration = duration_tag.get_text(strip=True)

                        # 4. Transit 
                        stops_anchor = soup_card.find("span", {"data-testid": "flight_card_segment_stops_0"})
                        if stops_anchor:
                            stops_raw = stops_anchor.get_text(strip=True)
                            if re.search(r"direct", stops_raw, re.IGNORECASE):
                                transit = "0"
                            else:
                                match = re.search(r"(\d+)", stops_raw)
                                transit = match.group(1) if match else stops_raw

                        # 5. Price 
                        price_tag = soup_card.find("div", {"data-testid": "upt_price"})
                        
                        if price_tag:
                            harga_text = price_tag.get_text(strip=True)
                            harga_num = int(re.sub(r'\D', '', harga_text))
                        else:
                            harga_num = None

    
                        # 6. Origin & Destination 
                        origin_tag = soup_card.find("span", {"data-testid": re.compile("flight_card_segment_departure_airport")})
                        dest_tag = soup_card.find("span", {"data-testid": re.compile("flight_card_segment_destination_airport")})
                        origin_code = origin_tag.get_text(strip=True) if origin_tag else None
                        dest_code = dest_tag.get_text(strip=True) if dest_tag else None

                        # 7. Seat Class
                        seat_class = sc.replace("_", " ").title()

                       # 8. Baggage (Selenium)
                        try:
                            details_btn = card.find_element(By.XPATH, ".//button[contains(., 'View details')]")
                            ActionChains(driver).move_to_element(details_btn).perform()
                            driver.execute_script("arguments[0].click();", details_btn)

                            modal_xpath = "//div[@role='dialog']"
                            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, modal_xpath)))

                            try:
                                WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.XPATH, f"{modal_xpath}//div[@data-testid='baggage_title']"))
                                )
                            except TimeoutException:
                                print(f"     ⚠ Konten bagasi di flight {idx+1} tidak terdeteksi (timeout).")
                            
                            soup_page = BeautifulSoup(driver.page_source, "html.parser")

                            all_baggage_titles = soup_page.find_all("div", {"data-testid": "baggage_title"})
                            
                            for title_tag in all_baggage_titles:
                                title_text = title_tag.get_text(strip=True).lower()
                                
                                if "checked" in title_text:
                                    
                                    description_tag = title_tag.find_next_sibling("div", {"data-testid": "baggage_description"})
                                    
                                    if description_tag:
                                        description_text = description_tag.get_text(strip=True)
                                        
                                        match_kg = re.search(r"(\d+)\s*kg", description_text, re.IGNORECASE)
                                        if match_kg:
                                            baggage = match_kg.group(1) 
                                            break 
                    
                            close_btn = driver.find_element(By.XPATH, f"{modal_xpath}//button[contains(@aria-label, 'Close') or contains(@aria-label, 'Tutup')]")
                            driver.execute_script("arguments[0].click();", close_btn)
                            time.sleep(1) 

                        except Exception as e:
                            print(f"     ⚠ Gagal ambil baggage di flight {idx+1}: {e}")

                            try:
                                close_btn = driver.find_element(By.XPATH, f"//div[@role='dialog']//button[contains(@aria-label, 'Close') or contains(@aria-label, 'Tutup')]")
                                driver.execute_script("arguments[0].click();", close_btn)
                            except:
                                pass # Modal tidak terbuka

                        except Exception as e:
                            print(f"     ⚠ Gagal ambil baggage di flight {idx+1}: {e}")
                            try:
                                close_btn = driver.find_element(By.XPATH, f"//div[@role='dialog']//button[contains(@aria-label, 'Close') or contains(@aria-label, 'Tutup')]")
                                driver.execute_script("arguments[0].click();", close_btn)
                            except:
                                pass 

                        if airline:
                            flights.append({
                                "date": date,
                                "airline": airline,
                                "departure_time": departure_time,
                                "arrival_time": arrival_time,
                                "duration": duration,
                                "transit": transit,
                                "price": harga_num,
                                "origin": origin_code,
                                "destination": dest_code,
                                "seat_class": seat_class,
                                "baggage": baggage,
                                "url": url
                            })
                            print(f"   ✅ [{len(flights)}] {airline} ({origin_code}-{dest_code}) | {departure_time}-{arrival_time} | {duration} | {transit} | Rp {harga_num} | Bag: {baggage}")
                        else:
                            print(f"   ℹ️ Melewati card {idx+1} (kemungkinan bukan penerbangan).")

                    except (StaleElementReferenceException, IndexError) as e:
                        print(f"   ⚠ Error Stale/Index di card {idx+1}: {e}. Kartu mungkin hilang. Melanjutkan...")
                        continue 
                    except Exception as e:
                        print(f"   ⚠ Error scrape umum di card {idx+1}: {e}")
              
            except Exception as e:
                print(f"❌ ERROR besar saat memproses {origin}->{destination} {date} {sc}: {e}")
                print(f"   URL Gagal: {url}")

driver.quit()
print("\n🎉 Proses scraping selesai.")

if flights: 
    
    df_baru = pd.DataFrame(flights) 
    output_filename = "NEW_booking_flight_data.xlsx"
    
    try:

        if os.path.exists(output_filename):
            print(f"ℹ️ File '{output_filename}' sudah ada. Membaca data lama...")
            df_lama = pd.read_excel(output_filename, engine="openpyxl")
            print("   Menggabungkan data lama dan baru...")
            df_gabungan = pd.concat([df_lama, df_baru], ignore_index=True) 
            df_gabungan.to_excel(output_filename, index=False, engine="openpyxl")
            print(f"✅ Data berhasil ditambahkan ke {output_filename}")
            print(f"   (Total {len(df_lama)} baris lama + {len(df_baru)} baris baru = {len(df_gabungan)} total baris)")
        
        else:
            print(f"ℹ️ File '{output_filename}' tidak ditemukan. Membuat file baru...")
            df_baru.to_excel(output_filename, index=False, engine="openpyxl")
            print(f"✅ Data baru berhasil disimpan ke {output_filename} ({len(df_baru)} baris)")

    except Exception as e:
        print(f"❌ ERROR saat menyimpan ke Excel: {e}")
        print("   Mungkin file sedang terbuka? Menyimpan sebagai file backup...")
        backup_filename = f"BACKUP_booking_data_{int(time.time())}.xlsx"
        df_baru.to_excel(backup_filename, index=False, engine="openpyxl")
        print(f"   Data scrape SAAT INI disimpan ke {backup_filename}")
        
else:
    print("❌ Tidak ada data penerbangan baru yang berhasil di-scrape. File Excel tidak diubah.")