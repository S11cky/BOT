import logging
import os
import requests
from data_sources import fetch_company_snapshot  # Import funkcie zo súboru data_sources.py
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import yfinance as yf
import numpy as np

# Parametre pre filtrovanie IPO
MAX_PRICE = 50  # Maximálna cena akcie
MIN_MARKET_CAP = 5e8  # Minimálna trhová kapitalizácia (500 miliónov USD)
SECTORS = ["Technology", "Biotechnology", "AI", "Green Technologies", "FinTech", "E-commerce", "HealthTech", "SpaceTech", "Autonomous Vehicles", "Cybersecurity", "Agritech", "EdTech", "RetailTech"]

# Logovanie
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Funkcia na získanie historických údajov a výpočet volatility
def get_historical_data(ticker: str):
    try:
        # Získame historické údaje za posledné 3 mesiace
        data = yf.download(ticker, period="3mo", interval="1d")
        return data
    except Exception as e:
        logging.error(f"Chyba pri získavaní historických dát pre {ticker}: {e}")
        return None

# Funkcia na výpočet volatility na základe historických dát
def calculate_volatility(data):
    if data is None or len(data) < 30:  # Min. 30 dní pre volatilitu
        return None
    
    # Výpočet denného percentuálneho zisku
    data['Returns'] = data['Adj Close'].pct_change()
    
    # Výpočet volatility (štandardná odchýlka denných ziskov)
    volatility = np.std(data['Returns']) * np.sqrt(252)  # Annualizovaná volatilita
    return volatility

# Funkcia na dynamické nastavenie Buy Band
def dynamic_buy_band(price: float, volatility: float):
    if volatility is None:
        return None, None
    
    # Dynamické pásmo na základe volatility
    spread = price * volatility  # Spread na základe volatility
    buy_band_lower = price - spread
    buy_band_upper = price + spread
    
    return buy_band_lower, buy_band_upper

# Funkcia na filtrovanie IPO dát a generovanie alertov
def fetch_ipo_data(ticker: str):
    try:
        # Získame IPO dáta (predpokladáme, že fetch_company_snapshot už je implementovaná)
        ipo = fetch_company_snapshot(ticker)
        if ipo:
            price = ipo.get("price_usd")
            market_cap = ipo.get("market_cap_usd")
            sector = ipo.get("sector", "")

            # Filtrujeme IPO podľa ceny, trhovej kapitalizácie a sektora
            if price is not None and market_cap is not None:
                if price <= MAX_PRICE and market_cap >= MIN_MARKET_CAP:
                    if any(sector in sector_name for sector_name in SECTORS):
                        # Získame historické dáta
                        historical_data = get_historical_data(ticker)
                        volatility = calculate_volatility(historical_data)
                        
                        # Dynamicky vypočítať Buy band
                        buy_band_lower, buy_band_upper = dynamic_buy_band(price, volatility)
                        
                        return ipo, buy_band_lower, buy_band_upper
                    else:
                        logging.warning(f"Ignorované IPO {ticker} – sektor mimo požiadaviek.")
                else:
                    logging.warning(f"Ignorované IPO {ticker} – cena alebo market cap je mimo kritérií.")
            else:
                logging.warning(f"Neúplné dáta pre {ticker}, ignorované.")
        else:
            logging.warning(f"Neboli získané dáta pre {ticker}")
    except Exception as e:
        logging.error(f"Chyba pri spracovaní {ticker}: {e}")
    return None, None, None

# Funkcia na poslanie alertu
def send_alert(ticker, price, buy_band_lower, buy_band_upper):
    if buy_band_lower is None or buy_band_upper is None:
        return
    
    # Vytvoríme správu
    alert_message = f"🚀 IPO Alert - {ticker}\n"
    alert_message += f"🔹 **Cena akcie**: {price} USD\n"
    alert_message += f"📈 **Optimálny vstup do pozície (Buy Band)**: {buy_band_lower:.2f} - {buy_band_upper:.2f} USD\n"
    
    # Pošleme alert (predpokladáme, že send_telegram je už implementovaná)
    send_telegram(alert_message)

# Hlavná funkcia na monitorovanie IPO
def monitor_ipo(tickers):
    for ticker in tickers:
        ipo, buy_band_lower, buy_band_upper = fetch_ipo_data(ticker)
        if ipo:
            price = ipo["price_usd"]
            send_alert(ticker, price, buy_band_lower, buy_band_upper)

# Spustenie monitorovania IPO spoločností
if __name__ == "__main__":
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    monitor_ipo(tickers)
