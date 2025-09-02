import logging
import os
import requests
import schedule
import time
from data_sources import fetch_company_snapshot  # Import z data_sources.py
from ipo_alerts import build_ipo_alert  # Import z ipo_alerts.py
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Parametre pre Small Cap a cena akcie ≤ 50 USD
MAX_PRICE = 50  # Zvýšená cena akcie
MIN_MARKET_CAP = 5e8  # Minimálna trhová kapitalizácia 500 miliónov USD

# Vybrané sektory pre filtrovanie IPO spoločností
SECTORS = ["Technológie", "Biotechnológia", "AI", "Zelené technológie", "FinTech", "E-commerce", "HealthTech", "SpaceTech", "Autonómne vozidlá", "Cybersecurity", "Agritech", "EdTech", "RetailTech"]

# Nastavenie logovania
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Zoznam investorov (napr. VC, Top spoločnosti, Billionaires)
VC_FUNDS = ['Vanguard Group Inc.', 'Sequoia Capital', 'Andreessen Horowitz', 'Benchmark', 'Greylock Partners', 'Insight Partners']
TOP_COMPANIES = ['Apple', 'Microsoft', 'Google', 'Amazon', 'Facebook', 'Berkshire Hathaway']
TOP_BILLIONAIRES = ['Elon Musk', 'Jeff Bezos', 'Bill Gates', 'Warren Buffett', 'Mark Zuckerberg']
ALL_INVESTORS = VC_FUNDS + TOP_COMPANIES + TOP_BILLIONAIRES

def send_telegram(message: str) -> bool:
    """Send message to Telegram"""
    token = os.getenv('TG_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    
    if not token or not chat_id:
        logging.error("Chýbajúce Telegram credentials!")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)  # Timeout na 5 sekúnd pre API volania
        if response.status_code == 200:
            logging.info(f"Správa úspešne odoslaná: {message[:50]}...")  # Zobraziť len prvých 50 znakov správy
            return True
        else:
            logging.error(f"Chyba pri odosielaní správy: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Chyba pri odosielaní Telegram správy: {e}")
        return False

def fetch_ipo_data(ticker: str) -> Dict[str, Any]:
    """Fetch IPO data for a single ticker"""
    try:
        logging.info(f"Získavam údaje pre {ticker}...")
        snap = fetch_company_snapshot(ticker)
        if snap:
            price = snap.get("price_usd")
            market_cap = snap.get("market_cap_usd")
            sector = snap.get("sector", "")
            if price is not None and market_cap is not None:
                if price <= MAX_PRICE and market_cap >= MIN_MARKET_CAP:
                    if any(sector in sector_name for sector_name in SECTORS):
                        return snap
                    else:
                        logging.warning(f"Ignorované IPO {ticker} – sektor mimo požiadaviek.")
                else:
                    logging.warning(f"Ignorované IPO {ticker} – cena alebo market cap je mimo kritérií. Cena: {price}, Market Cap: {market_cap}")
            else:
                logging.warning(f"Neúplné dáta pre {ticker}, ignorované.")
        else:
            logging.warning(f"Neboli získané dáta pre {ticker}")
    except Exception as e:
        logging.error(f"Chyba pri spracovaní {ticker}: {e}")
    return None

def fetch_and_filter_ipo_data(tickers: List[str]) -> List[Dict[str, Any]]:
    """Fetch IPO data for multiple tickers using multithreading"""
    ipo_data = []
    with ThreadPoolExecutor(max_workers=20) as executor:  # Zvýšený počet workerov na 20
        futures = {executor.submit(fetch_ipo_data, ticker): ticker for ticker in tickers}
        for future in as_completed(futures):
            ipo = future.result()
            if ipo:
                ipo_data.append(ipo)

    logging.info(f"Celkový počet filtrovaných IPO: {len(ipo_data)}")
    return ipo_data

def send_alerts():
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    
    logging.info(f"Začínam monitorovať {len(tickers)} IPO spoločností...")
    
    # Načítanie údajov o spoločnostiach a filtrovanie
    ipo_data = fetch_and_filter_ipo_data(tickers)
    
    # Poslanie alertov len pre filtrované IPO
    for ipo in ipo_data:
        try:
            ipo_msg = build_ipo_alert(ipo)  # Opravené volanie funkcie, teraz správne s argumentom ipo
            
            # Odoslanie správy na Telegram
            success = send_telegram(ipo_msg)
            if success:
                logging.info(f"Alert pre {ipo['ticker']} úspešne odoslaný.")
            else:
                logging.error(f"Chyba pri odosielaní alertu pre {ipo['ticker']}")
        except Exception as e:
            logging.error(f"Chyba pri vytváraní alertu pre {ipo['ticker']}: {e}")
    
    logging.info("Proces dokončený.")

# Nastavenie časovača na spúšťanie každých 15 minút
schedule.every(15).minutes.do(send_alerts)

# Spustenie plánovača
if __name__ == "__main__":
    logging.info("Skript sa spustil.")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Skontroluje úlohy každú minútu
