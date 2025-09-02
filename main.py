import logging
import os
import requests
import schedule
import time
import aiohttp
from data_sources import fetch_company_snapshot  # Import from data_sources.py
from ipo_alerts import build_ipo_alert  # Import from ipo_alerts.py
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Parameters for Small Cap and stock price ≤ 50 USD
MAX_PRICE = 50  # Maximum stock price
MIN_MARKET_CAP = 5e8  # Minimum market capitalization 500 million USD

# Selected sectors for filtering IPO companies (translated to English)
SECTORS = ["Technology", "Biotechnology", "AI", "Green Technologies", "FinTech", "E-commerce", "HealthTech", "SpaceTech", "Autonomous Vehicles", "Cybersecurity", "Agritech", "EdTech", "RetailTech"]

# Storing history of sent alerts
alert_history = {}

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def send_telegram(message: str) -> bool:
    """Send message to Telegram"""
    token = os.getenv('TG_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    
    if not token or not chat_id:
        logging.error("Missing Telegram credentials!")
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
                logging.info(f"Message successfully sent: {message[:50]}...")  # Show only first 50 characters
                return True
            else:
                logging.error(f"Error sending message: {response.status}")
                return False
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")
        return False

async def fetch_ipo_data(ticker: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Fetch IPO data for a single ticker"""
    try:
        logging.info(f"Fetching data for {ticker}...")
        snap = await fetch_company_snapshot(ticker, session)  # Passing session to the API function
        if snap:
            price = snap.get("price_usd")
            market_cap = snap.get("market_cap_usd")
            sector = snap.get("sector", "")
            logging.info(f"IPO {ticker} fetched: Price = {price}, Market Cap = {market_cap}, Sector = {sector}")
            if price is not None and market_cap is not None:
                if price <= MAX_PRICE and market_cap >= MIN_MARKET_CAP:
                    if any(sector in sector_name for sector_name in SECTORS):
                        logging.info(f"IPO {ticker} meets criteria.")
                        return snap
                    else:
                        logging.warning(f"Ignored IPO {ticker} – sector not in required list.")
                else:
                    logging.warning(f"Ignored IPO {ticker} – price or market cap out of criteria. Price: {price}, Market Cap: {market_cap}")
            else:
                logging.warning(f"Incomplete data for {ticker}, ignored.")
        else:
            logging.warning(f"No data retrieved for {ticker}")
    except Exception as e:
        logging.error(f"Error processing {ticker}: {e}")
    return None

async def fetch_and_filter_ipo_data(tickers: List[str]) -> List[Dict[str, Any]]:
    """Fetch IPO data for multiple tickers using multithreading"""
    ipo_data = []
    async with aiohttp.ClientSession() as session:  # Creating a session to be used in all fetch calls
        for ticker in tickers:
            ipo = await fetch_ipo_data(ticker, session)
            if ipo:
                ipo_data.append(ipo)
    logging.info(f"Total number of filtered IPOs: {len(ipo_data)}")
    return ipo_data

async def send_alerts():
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    
    logging.info(f"Starting to monitor {len(tickers)} IPO companies...")
    
    # Fetching data for companies and filtering
    ipo_data = await fetch_and_filter_ipo_data(tickers)
    
    logging.info(f"After filtering: {len(ipo_data)} IPOs met the criteria.")
    
    # Sending alerts only for filtered IPOs
    for ipo in ipo_data:
        try:
            logging.info(f"Processing IPO: {ipo['ticker']} - Price: {ipo['price_usd']}, Market Cap: {ipo['market_cap_usd']}")
            
            # First alert - If IPO hasn't been sent before and meets criteria
            if ipo['ticker'] not in alert_history:
                ipo_msg = build_ipo_alert(ipo)
                await send_telegram(ipo_msg)
                alert_history[ipo['ticker']] = {"first_alert_sent": True, "price": ipo.get("price_usd")}
                logging.info(f"First alert for {ipo['ticker']} successfully sent.")
            
            # Second alert - If stock price enters the optimal buy band
            if ipo['ticker'] in alert_history:
                buy_band_min = ipo.get("buy_band_min")
                buy_band_max = ipo.get("buy_band_max")
                current_price = ipo.get("price_usd")
                if buy_band_min <= current_price <= buy_band_max:
                    ipo_msg = build_ipo_alert(ipo)  # This alert is the same as the first, but can be modified with specific messages
                    await send_telegram(ipo_msg)
                    logging.info(f"Second alert for {ipo['ticker']} successfully sent.")
        except Exception as e:
            logging.error(f"Error creating alert for {ipo['ticker']}: {e}")
    
    logging.info("Process completed.")

# Run the script
if __name__ == "__main__":
    logging.info("Script started.")
    import asyncio
    asyncio.run(send_alerts())
