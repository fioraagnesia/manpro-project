from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time, re, pandas as pd
from datetime import datetime, timedelta
import random

options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
# options.add_argument("--headless")
options.add_argument("--start-maximized")   
driver = webdriver.Chrome(options=options)

start_date = datetime(2025, 11, 14)
num_days = 10
dates = [(start_date + timedelta(days=i)).strftime("%d-%m-%Y") for i in range(num_days)]

routes = [
    ("JKTA", "SIN"),   
    ("SIN", "JKTA"),   
    ("SUB", "DPS"),    
    ("DPS", "SUB"),    
    ("SUB", "SIN"),
    ("SIN", "SUB"),
    ("SUB", "SRG"),
    ("SRG", "SUB"),
    ("SUB", "JKTA"),
    ("JKTA", "SUB"),
]

seat_classes = ["ECONOMY" , "BUSINESS"]

flights = []

for date in dates:
    for origin, destination in routes:
        for sc in seat_classes:
            url = f"https://www.traveloka.com/en-id/flight/fullsearch?ap={origin}.{destination}&dt={date}.NA&ps=1.0.0&sc={sc}"
            driver.get(url)
            time.sleep(4)
            try:
                driver.find_element(By.XPATH, "//h3[contains(text(), 'No flights match your preference')]")
                print(f"🟡 TIDAK ADA PENERBANGAN: Rute {origin} -> {destination} kelas {sc} tanggal {date}. Melanjutkan...")
                continue
            except:
                pass

            last_index = 0
            flight_count = 0 
            MAX_FLIGHTS = 15  # Batas maksimal per halaman

            for _ in range(15):
                if flight_count >= MAX_FLIGHTS:
                    print(f"⏹ Batas 15 penerbangan tercapai untuk {origin}-{destination} tanggal {date}, berhenti scroll.")
                    break

                scroll_distance = random.randint(600, 1000) 
                driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
                time.sleep(3)
                
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class,'css-1dbjc4n r-1x4r79x')]"))
                    )
                except:
                    continue

                cards = driver.find_elements(By.XPATH, "//div[contains(@class,'css-1dbjc4n r-1x4r79x')]")
                for idx in range(last_index, len(cards)):
                    if flight_count >= MAX_FLIGHTS:
                        break

                    card = cards[idx]
                    try:
                        soup_card = BeautifulSoup(card.get_attribute("outerHTML"), "html.parser")

                        airline_div = soup_card.find("div", class_="css-901oao css-cens5h r-uh8wd5 r-majxgm r-fdjqy7")
                        airline = airline_div.get_text(strip=True) if airline_div else None

                        time_divs = soup_card.find_all("div", string=re.compile(r"\d{1,2}:\d{2}"))
                        if len(time_divs) >= 2:
                            departure_time = time_divs[0].get_text(strip=True)
                            arrival_time = time_divs[1].get_text(strip=True)
                        else:
                            departure_time, arrival_time = None, None

                        duration_transit_divs = soup_card.find_all(
                            "div", class_="css-901oao r-uh8wd5 r-majxgm r-1p4rafz r-fdjqy7"
                        )
                        duration = duration_transit_divs[0].get_text(strip=True) if len(duration_transit_divs) > 0 else None
                        transit_raw = duration_transit_divs[1].get_text(strip=True) if len(duration_transit_divs) > 1 else None

                        if transit_raw:
                            if transit_raw.lower() == "direct":
                                transit = "0"
                            else:
                                match = re.search(r"(\d+)\s*stop[s]?", transit_raw, re.IGNORECASE)
                                transit = match.group(1) if match else transit_raw
                        else:
                            transit = None

                        price_div = soup_card.find("h3", class_="css-4rbku5 css-901oao r-uh8wd5 r-b88u0q r-rjixqe r-fdjqy7")
                        if price_div:
                            price_text = price_div.get_text(strip=True).replace("/pax", "").strip()
                            price_cleaned = price_text.replace("Rp", "").replace(".", "").replace(",", ".").strip()
                            try:
                                price = int(float(price_cleaned))
                            except:
                                price = None
                        else:
                            price = None

                        airport_divs = soup_card.find_all(
                            "div",
                            class_="css-901oao r-uh8wd5 r-majxgm r-fdjqy7",
                            string=re.compile(r"[A-Z]{3}")
                        )
                        origin = airport_divs[0].get_text(strip=True) if len(airport_divs) > 0 else None
                        destination = airport_divs[1].get_text(strip=True) if len(airport_divs) > 1 else None

                        baggage = None
                        try:
                            details_btn = card.find_element(By.XPATH, ".//div[contains(text(),'Flight Details')]")
                            ActionChains(driver).move_to_element(details_btn).perform()
                            driver.execute_script("arguments[0].click();", details_btn)
                            time.sleep(2)

                            soup_page = BeautifulSoup(driver.page_source, "html.parser")
                            baggage_div = soup_page.find("div", string=re.compile(r"Baggage \d+ kg", re.IGNORECASE))
                            if baggage_div:
                                baggage_text = baggage_div.get_text(strip=True)
                                match = re.search(r"Baggage (\d+)\s*kg", baggage_text, re.IGNORECASE)
                                if match:
                                    baggage = match.group(1)
                                else:
                                    baggage = None

                            driver.execute_script("arguments[0].click();", details_btn)
                            time.sleep(1)

                        except Exception as e:
                            print(f"⚠ Gagal ambil baggage di flight {idx+1}: {e}")

                        if airline and departure_time and arrival_time:
                            flights.append({
                                "date": date,
                                "airline": airline,
                                "departure_time": departure_time,
                                "arrival_time": arrival_time,
                                "duration": duration,
                                "transit": transit,
                                "price": price,
                                "origin": origin,
                                "destination": destination,
                                "seat_class": sc.replace("_", " ").title(),
                                "baggage": baggage,
                                "url": url
                            })
                            flight_count += 1
                            print(f"✅ [{len(flights)}] Berhasil scrape: {airline} rute {origin}-{destination} tanggal {date}")

                    except Exception as e:
                        print(f"⚠ Error di card {idx+1}: {e}")

                last_index = len(cards)

driver.quit()
excel_filename = "flights_traveloka.xlsx"
df_new = pd.DataFrame(flights)

if not df_new.empty:
    try:

        df_existing = pd.read_excel(excel_filename, engine="openpyxl")
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        
        print(f"\nINFO: Menggabungkan {len(df_new)} data baru dengan {len(df_existing)} data lama.")

    except FileNotFoundError:
        print(f"\nINFO: File {excel_filename} tidak ditemukan. Membuat file baru...")
        df_combined = df_new
    except Exception as e:
        print(f"\nWARNING: Gagal membaca {excel_filename} (mungkin rusak?): {e}")
        print("INFO: Menimpa file dengan data baru saja.")
        df_combined = df_new
    try:
        df_combined.to_excel(excel_filename, index=False, engine="openpyxl")
        print(f"✅ Data berhasil disimpan ke {excel_filename}. Total baris sekarang: {len(df_combined)}")
    except Exception as e:
        print(f"❌ GAGAL MENYIMPAN FILE: {e}")
        print("Mencoba menyimpan ke file backup...")
        df_combined.to_excel("flights_traveloka_BACKUP.xlsx", index=False, engine="openpyxl")
        print(f"✅ Data disimpan ke flights_traveloka_BACKUP.xlsx")

else:
    print("\nINFO: Tidak ada data penerbangan baru yang di-scrape. File Excel tidak diubah.")