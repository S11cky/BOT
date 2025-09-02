import logging
import os
import requests
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from data_sources import fetch_company_snapshot  # Import from data_sources.py
from ipo_alerts import build_ipo_alert  # Import from ipo_alerts.py
from typing import List, Dict, Any

# Parametre pre Small Cap a cena akcie ≤ 50 USD
MAX_PRICE = 50  # Maximum stock price
MIN_MARKET_CAP = 5e8  # Minimum market cap of 500 million USD

# Vybrané sektory pre filtrovanie IPO spoločností
SECTORS = ["Technology", "Biotechnology", "AI", "GreenTech", "FinTech", "E-commerce", "HealthTech", "SpaceTech", "Autonomous Vehicles", "Cybersecurity", "Agritech", "EdTech", "RetailTech"]

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def send_telegram(message: str) -> bool:
    """Send message to Telegram"""
    token = os.getenv('TG_TOKEN')  # Telegram bot token
    chat_id = os.getenv('TG_CHAT_ID')  # Telegram chat ID
    
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
            async with session.post(url, json=payload, timeout=5) as response:
                if response.status == 200:
                    logging.info(f"Message successfully sent: {message[:50]}...")  # Show first 50 characters of the message
                    return True
                else:
                    logging.error(f"Error sending message: {response.status}")
                    return False
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")
        return False

async def fetch_ipo_data(ticker: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Fetch IPO data for a single ticker using async"""
    try:
        logging.info(f"Fetching data for {ticker}...")
        snap = await fetch_company_snapshot(ticker, session)
        if snap:
            price = snap.get("price_usd")
            market_cap = snap.get("market_cap_usd")
            sector = snap.get("sector", "")
            if price is not None and market_cap is not None:
                if price <= MAX_PRICE and market_cap >= MIN_MARKET_CAP:
                    if any(sector in sector_name for sector_name in SECTORS):
                        return snap
                    else:
                        logging.warning(f"Ignored IPO {ticker} – sector outside of required criteria.")
                else:
                    logging.warning(f"Ignored IPO {ticker} – price or market cap is outside of criteria.")
            else:
                logging.warning(f"Incomplete data for {ticker}, ignored.")
        else:
            logging.warning(f"Data not fetched for {ticker}")
    except Exception as e:
        logging.error(f"Error processing {ticker}: {e}")
    return None

async def fetch_and_filter_ipo_data(tickers: List[str]) -> List[Dict[str, Any]]:
    """Fetch IPO data for multiple tickers using asyncio"""
    ipo_data = []
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_ipo_data(ticker, session) for ticker in tickers]
        results = await asyncio.gather(*tasks)
        ipo_data = [ipo for ipo in results if ipo]
    
    logging.info(f"Total number of filtered IPOs: {len(ipo_data)}")
    return ipo_data

async def send_alerts():
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    
    logging.info(f"Starting to monitor {len(tickers)} IPO companies...")

    # Fetching and filtering data for companies
    ipo_data = await fetch_and_filter_ipo_data(tickers)

    # Sending alerts only for filtered IPOs
    for ipo in ipo_data:
        try:
            ipo_msg = build_ipo_alert(ipo)  # Corrected function call, now correctly with the ipo argument

            # Send message to Telegram
            success = await send_telegram(ipo_msg)
            if success:
                logging.info(f"Alert for {ipo['ticker']} successfully sent.")
            else:
                logging.error(f"Error sending alert for {ipo['ticker']}")
        except Exception as e:
            logging.error(f"Error creating alert for {ipo['ticker']}: {e}")

    logging.info("Process completed.")

if __name__ == "__main__":
    logging.info("Script started.")
    asyncio.run(send_alerts())  # Calling the async function to run the alert process
