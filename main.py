import logging
import os
import requests
import schedule
import time
from data_sources import fetch_company_snapshot  # Import from data_sources.py
from ipo_alerts import build_ipo_alert  # Import from ipo_alerts.py
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Parameters for Small Cap and price <= 50 USD
MAX_PRICE = 50  # Maximum stock price
MIN_MARKET_CAP = 5e8  # Minimum market cap of 500 million USD

# Selected sectors for filtering IPO companies
SECTORS = ["Technology", "Biotechnology", "AI", "GreenTech", "FinTech", "E-commerce", "HealthTech", "SpaceTech", "Autonomous Vehicles", "Cybersecurity", "Agritech", "EdTech", "RetailTech"]

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# List of investors (e.g., VC, Top companies, Billionaires)
VC_FUNDS = ['Vanguard Group Inc.', 'Sequoia Capital', 'Andreessen Horowitz', 'Benchmark', 'Greylock Partners', 'Insight Partners']
TOP_COMPANIES = ['Apple', 'Microsoft', 'Google', 'Amazon', 'Facebook', 'Berkshire Hathaway']
TOP_BILLIONAIRES = ['Elon Musk', 'Jeff Bezos', 'Bill Gates', 'Warren Buffett', 'Mark Zuckerberg']
ALL_INVESTORS = VC_FUNDS + TOP_COMPANIES + TOP_BILLIONAIRES

def send_telegram(message: str) -> bool:
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
        response = requests.post(url, json=payload, timeout=5)  # Timeout for 5 seconds
        logging.info(f"Response: {response.status_code} - {response.text}")  # Log the response
        if response.status_code == 200:
            logging.info(f"Message successfully sent: {message[:50]}...")  # Show first 50 characters of the message
            return True
        else:
            logging.error(f"Error sending message: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")
        return False

def fetch_ipo_data(ticker: str) -> Dict[str, Any]:
    """Fetch IPO data for a single ticker"""
    try:
        logging.info(f"Fetching data for {ticker}...")
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

def fetch_and_filter_ipo_data(tickers: List[str]) -> List[Dict[str, Any]]:
    """Fetch IPO data for multiple tickers using multithreading"""
    ipo_data = []
    with ThreadPoolExecutor(max_workers=10) as executor:  # Increased number of workers to 10
        futures = {executor.submit(fetch_ipo_data, ticker): ticker for ticker in tickers}
        for future in as_completed(futures):
            ipo = future.result()
            if ipo:
                ipo_data.append(ipo)

    logging.info(f"Total number of filtered IPOs: {len(ipo_data)}")
    return ipo_data

def send_alerts():
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    
    logging.info(f"Starting to monitor {len(tickers)} IPO companies...")

    # Fetching and filtering data for companies
    ipo_data = fetch_and_filter_ipo_data(tickers)

    # Sending alerts only for filtered IPOs
    for ipo in ipo_data:
        try:
            ipo_msg = build_ipo_alert(ipo)  # Corrected function call, now correctly with the ipo argument

            # Send message to Telegram
            success = send_telegram(ipo_msg)
            if success:
                logging.info(f"Alert for {ipo['ticker']} successfully sent.")
            else:
                logging.error(f"Error sending alert for {ipo['ticker']}")
        except Exception as e:
            logging.error(f"Error creating alert for {ipo['ticker']}: {e}")

    logging.info("Process completed.")

# Scheduling the alert sending function to run every 15 minutes
schedule.every(15).minutes.do(send_alerts)

# Running the scheduler
if __name__ == "__main__":
    logging.info("Script started.")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check for pending tasks every minute
