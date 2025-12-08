import os, time, pickle, re, datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

COOKIE_FILE = "agoda_cookies.pkl"
OUTPUT_FILE = "agoda_flights_multiroute.xlsx"

def save_cookies(driver):
    pickle.dump(driver.get_cookies(), open(COOKIE_FILE, "wb"))
    print("✅ Cookies saved!")

def load_cookies(driver):
    cookies = pickle.load(open(COOKIE_FILE, "rb"))
    for cookie in cookies:
        if isinstance(cookie.get("expiry"), float):
            cookie["expiry"] = int(cookie["expiry"])
        driver.add_cookie(cookie)
    print("✅ Cookies loaded!")

def scroll_to_load_flights(driver, pause_time=2, max_scroll=3):
    """Scroll down to load all flight results."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(max_scroll):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


ROUTES = [
    ("JKT", "SIN"),   
    ("SIN", "JKT"),   
    ("SUB", "DPS"),    
    ("DPS", "SUB"),    
    ("SUB", "SIN"),
    ("SIN", "SUB"),
    ("SUB", "SRG"),
    ("SRG", "SUB"),
    ("SUB", "JKT"),
    ("JKT", "SUB"),
]
START_DATE = "2025-11-15"
END_DATE = "2025-11-15"
SEAT_TYPES = ["Business"]
MAX_FLIGHTS_PER_PAGE = 15

print("🚀 Launching browser...")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()
driver.get("https://www.agoda.com/")

if os.path.exists(COOKIE_FILE):
    print("🔁 Loading cookies...")
    driver.delete_all_cookies()
    load_cookies(driver)
    driver.refresh()
else:
    print("🕐 Please log in manually (if needed)...")
    time.sleep(60)
    save_cookies(driver)
    print("ℹ Restart the script next time to skip login.")

start = datetime.datetime.strptime(START_DATE, "%Y-%m-%d")
end = datetime.datetime.strptime(END_DATE, "%Y-%m-%d")
date_list = [(start + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end - start).days + 1)]


for origin, dest in ROUTES:
    for seat_type in SEAT_TYPES:
        for depart_date in date_list:

            print(f"\n🌍 Scraping {origin} → {dest} on {depart_date} ({seat_type})")

            url = (
                "https://www.agoda.com/flights/results"
                f"?departureFrom={origin}"
                f"&departureFromType=1"
                f"&arrivalTo={dest}"
                f"&arrivalToType=0"
                f"&departDate={depart_date}"
                "&searchType=1"
                f"&cabinType={seat_type}"
                "&adults=1"
                "&sort=8"
            )

            driver.get(url)
            time.sleep(6)
            scroll_to_load_flights(driver)

            try:
                cards = WebDriverWait(driver, 25).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div[data-testid='flightCard-flight-detail']")
                    )
                )
                print(f"✅ Found {len(cards)} flight cards.")
            except Exception as e:
                print(f"❌ Could not find flight cards for {origin}→{dest} on {depart_date}: {e}")
                continue

            cards = cards[:MAX_FLIGHTS_PER_PAGE]
            print(f"ℹ Limiting to {len(cards)} flights per page.")

            flights_data = []

            for idx, card in enumerate(cards, start=1):
                try:
                    airline = card.find_element(
                        By.CSS_SELECTOR,
                        "p.sc-dmqHEX.Typographystyled__TypographyStyled-sc-1uoovui-0.czWcZb.iYbjBz"
                    ).text.strip()

                    times = card.find_elements(
                        By.CSS_SELECTOR,
                        "h3.sc-dmqHEX.Typographystyled__TypographyStyled-sc-1uoovui-0.czWcZb.clvaSu"
                    )
                    dep_time = times[0].text.strip() if len(times) > 0 else None
                    arr_time = times[1].text.strip() if len(times) > 1 else None

                    origin_txt = card.find_element(By.CSS_SELECTOR, "p[data-testid='origin']").text.strip() if card.find_elements(By.CSS_SELECTOR, "p[data-testid='origin']") else ""
                    dep_term = card.find_element(By.CSS_SELECTOR, "p[data-testid='departure-terminal']").text.strip() if card.find_elements(By.CSS_SELECTOR, "p[data-testid='departure-terminal']") else ""
                    dest_txt = card.find_element(By.CSS_SELECTOR, "p[data-testid='destination']").text.strip() if card.find_elements(By.CSS_SELECTOR, "p[data-testid='destination']") else ""
                    arr_term = card.find_element(By.CSS_SELECTOR, "p[data-testid='arrival-terminal']").text.strip() if card.find_elements(By.CSS_SELECTOR, "p[data-testid='arrival-terminal']") else ""

                    origin_full = f"{origin_txt} {dep_term}".strip()
                    dest_full = f"{dest_txt} {arr_term}".strip()

                    duration = card.find_element(By.CSS_SELECTOR, "span[data-testid='duration']").text.strip() if card.find_elements(By.CSS_SELECTOR, "span[data-testid='duration']") else ""
                    transit = len(card.find_elements(By.CSS_SELECTOR, "span[data-testid='layover']"))

                    try:
                        price_txt = card.find_element(
                            By.CSS_SELECTOR,
                            "span.sc-dmqHEX.Typographystyled__TypographyStyled-sc-1uoovui-0.czWcZb.gPcWqz"
                        ).text.strip()
                        price = int(re.sub(r"[^\d]", "", price_txt))
                    except:
                        price = None

                    flights_data.append({
                        "date": depart_date,
                        "route": f"{origin} → {dest}",
                        "airline": airline,
                        "departure_time": dep_time,
                        "arrival_time": arr_time,
                        "duration": duration,
                        "transit": transit,
                        "price": price,
                        "origin": origin_full,
                        "destination": dest_full,
                        "seat_class": seat_type,
                    })

                    print(f"✈ {depart_date} | {seat_type} | {airline} | {origin_full} → {dest_full} | "
                          f"{dep_time} → {arr_time} | {duration} | Transit: {transit} | Price: {price}")

                except Exception as e:
                    print(f"⚠ Error parsing flight {idx}: {e}")

            if flights_data:
                df_new = pd.DataFrame(flights_data)

                if os.path.exists(OUTPUT_FILE):
                    existing = pd.read_excel(OUTPUT_FILE)
                    combined = pd.concat([existing, df_new], ignore_index=True)
                    combined.to_excel(OUTPUT_FILE, index=False)
                else:
                    df_new.to_excel(OUTPUT_FILE, index=False)

                print(f"💾 Saved {len(df_new)} new flights to {OUTPUT_FILE}")

driver.quit()
print("👋 Done.")
