import os
import requests
import schedule
import time
from data_sources import fetch_company_snapshot  # Import z data_sources.py
from ipo_alerts import build_ipo_alert  # Import z ipo_alerts.py
from typing import List, Dict, Any

# Parametre pre Small Cap a cena akcie ≤ 20 USD
MAX_PRICE = 20
MIN_MARKET_CAP = 1e9  # Minimálna trhová kapitalizácia pre IPO spoločnosti (1 miliarda USD)

# Zoznam investorov (napr. VC, Top spoločnosti, Billionaires)
VC_FUNDS = ['Vanguard Group Inc.', 'Sequoia Capital', 'Andreessen Horowitz', 'Benchmark', 'Greylock Partners', 'Insight Partners']
TOP_COMPANIES = ['Apple', 'Microsoft', 'Google', 'Amazon', 'Facebook', 'Berkshire Hathaway']
TOP_BILLIONAIRES = ['Elon Musk', 'Jeff Bezos', 'Bill Gates', 'Warren Buffett', 'Mark Zuckerberg']
ALL_INVESTORS = VC_FUNDS + TOP_COMPANIES + TOP_BILLIONAIRES

# Načítanie zoznamu tickerov z iného zdroja alebo súboru
def load_companies_from_yaml(yaml_file: str) -> List[str]:
    try:
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)
            return data.get('companies', [])
    except Exception as e:
        print(f"Chyba pri načítaní YAML súboru: {e}")
        return []

def send_telegram(message: str) -> bool:
    """Send message to Telegram"""
    token = os.getenv('TG_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    
    if not token or not chat_id:
        print("Chýbajúce Telegram credentials!")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Chyba pri odosielaní Telegram správy: {e}")
        return False

def fetch_and_filter_ipo_data(tickers: List[str]) -> List[Dict[str, Any]]:
    """Fetch IPO data and filter by price and market cap"""
    ipo_data = []
    for ticker in tickers:
        try:
            print(f"Získavam údaje pre {ticker}...")
            snap = fetch_company_snapshot(ticker)  # Volanie funkcie z data_sources.py
            if snap:
                price = snap.get("price_usd")
                market_cap = snap.get("market_cap_usd")
                
                # Filtrovanie podľa ceny a trhovej kapitalizácie
                if price is not None and market_cap is not None:
                    if price <= MAX_PRICE and market_cap >= MIN_MARKET_CAP:
                        ipo_data.append(snap)
                        print(f"Údaje pre {ticker} úspešne načítané")
                    else:
                        print(f"Ignorované IPO {ticker} – cena alebo market cap je mimo kritérií.")
                else:
                    print(f"Neúplné dáta pre {ticker}, ignorované.")
            else:
                print(f"Neboli získané dáta pre {ticker}")
        except Exception as e:
            print(f"Chyba pri spracovaní {ticker}: {e}")
    
    return ipo_data

def send_alerts():
    # Zoznam tickerov firiem, ktorý môže byť načítaný zo súboru YAML alebo iného zdroja
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    
    print(f"Začínam monitorovať {len(tickers)} IPO spoločností...")
    
    # Načítanie údajov o spoločnostiach a filtrovanie
    ipo_data = fetch_and_filter_ipo_data(tickers)
    
    # Poslanie alertov len pre filtrované IPO
    for ipo in ipo_data:
        try:
            ipo_msg = build_ipo_alert(ipo)  # Vytvorenie alertu pomocou ipo_alerts.py
            
            # Odoslanie správy na Telegram
            success = send_telegram(ipo_msg)
            if success:
                print(f"Správa pre {ipo['ticker']} úspešne odoslaná")
            else:
                print(f"Chyba pri odosielaní správy pre {ipo['ticker']}")
                
        except Exception as e:
            print(f"Chyba pri vytváraní alertu pre {ipo['ticker']}: {e}")
    
    print("Proces dokončený.")

# Naplánovanie vykonania úlohy každých 15 minút
schedule.every(15).minutes.do(send_alerts)

# Spustenie plánovača
while True:
    schedule.run_pending()
    time.sleep(60)
