import logging
import os
import requests
import schedule
import time
import aiohttp
from data_sources import fetch_company_snapshot  # Import z data_sources.py
from ipo_alerts import build_ipo_alert  # Import z ipo_alerts.py
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Parametre pre Small Cap a cena akcie ≤ 50 USD
MAX_PRICE = 50  # Zvýšená cena akcie
MIN_MARKET_CAP = 5e8  # Minimálna trhová kapitalizácia 500 miliónov USD

# Vybrané sektory pre filtrovanie IPO spoločností
SECTORS = ["Technológie", "Biotechnológia", "AI", "Zelené technológie", "FinTech", "E-commerce", "HealthTech", "SpaceTech", "Autonómne vozidlá", "Cybersecurity", "Agritech", "EdTech", "RetailTech"]

# Uchovávanie histórie poslaných alertov
alert_history = {}

# Nastavenie logovania
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def send_telegram(message: str) -> bool:
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
        async with aiohttp.ClientSession() as session:
            response = await session.post(url, json=payload, timeout=5)
            if response.status == 200:
                logging.info(f"Správa úspešne odoslaná: {message[:50]}...")  # Zobraziť len prvých 50 znakov správy
                return True
            else:
                logging.error(f"Chyba pri odosielaní správy: {response.status}")
                return False
    except Exception as e:
        logging.error(f"Chyba pri odosielaní Telegram správy: {e}")
        return False

async def fetch_ipo_data(ticker: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Fetch IPO data for a single ticker"""
    try:
        logging.info(f"Získavam údaje pre {ticker}...")
        snap = await fetch_company_snapshot(ticker, session)  # Passing session to the API function
        if snap:
            price = snap.get("price_usd")
            market_cap = snap.get("market_cap_usd")
            sector = snap.get("sector", "")
            logging.info(f"IPO {ticker} získané: Cena = {price}, Market Cap = {market_cap}, Sektor = {sector}")
            if price is not None and market_cap is not None:
                if price <= MAX_PRICE and market_cap >= MIN_MARKET_CAP:
                    if any(sector in sector_name for sector_name in SECTORS):
                        logging.info(f"IPO {ticker} spĺňa kritériá.")
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

async def fetch_and_filter_ipo_data(tickers: List[str]) -> List[Dict[str, Any]]:
    """Fetch IPO data for multiple tickers using multithreading"""
    ipo_data = []
    async with aiohttp.ClientSession() as session:  # Creating a session to be used in all fetch calls
        for ticker in tickers:
            ipo = await fetch_ipo_data(ticker, session)
            if ipo:
                ipo_data.append(ipo)
    logging.info(f"Celkový počet filtrovaných IPO: {len(ipo_data)}")
    return ipo_data

async def send_alerts():
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    
    logging.info(f"Začínam monitorovať {len(tickers)} IPO spoločností...")
    
    # Načítanie údajov o spoločnostiach a filtrovanie
    ipo_data = await fetch_and_filter_ipo_data(tickers)
    
    logging.info(f"Po filtrovaní: {len(ipo_data)} IPO splnilo kritériá.")
    
    # Poslanie alertov len pre filtrované IPO
    for ipo in ipo_data:
        try:
            logging.info(f"Spracovávam IPO: {ipo['ticker']} - Cena: {ipo['price_usd']}, Market Cap: {ipo['market_cap_usd']}")
            
            # Prvý alert - Ak IPO ešte nebolo odoslané a splní podmienky
            if ipo['ticker'] not in alert_history:
                ipo_msg = build_ipo_alert(ipo)
                await send_telegram(ipo_msg)
                alert_history[ipo['ticker']] = {"first_alert_sent": True, "price": ipo.get("price_usd")}
                logging.info(f"Prvý alert pre {ipo['ticker']} úspešne odoslaný.")
            
            # Druhý alert - Ak cena akcie vstúpi do optimálneho nákupného pásma (Buy Band)
            if ipo['ticker'] in alert_history:
                buy_band_min = ipo.get("buy_band_min")
                buy_band_max = ipo.get("buy_band_max")
                current_price = ipo.get("price_usd")
                if buy_band_min <= current_price <= buy_band_max:
                    ipo_msg = build_ipo_alert(ipo)  # Tento alert je rovnaký ako prvý, ale môžeš pridať špecifickú správu
                    await send_telegram(ipo_msg)
                    logging.info(f"Druhý alert pre {ipo['ticker']} úspešne odoslaný.")
        except Exception as e:
            logging.error(f"Chyba pri vytváraní alertu pre {ipo['ticker']}: {e}")
    
    logging.info("Proces dokončený.")

# Spustenie skriptu
if __name__ == "__main__":
    logging.info("Skript sa spustil.")
    import asyncio
    asyncio.run(send_alerts())
