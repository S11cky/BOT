import logging
import os
import aiohttp
import asyncio
import yfinance as yf
import requests
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

# Parametre pre Small Cap a cena akcie ≤ 50 USD
MAX_PRICE = 50  # Maximum stock price
MIN_MARKET_CAP = 5e8  # Minimum market cap of 500 million USD

# Vybrané sektory pre filtrovanie IPO spoločností
SECTORS = ["Technology", "Biotechnology", "AI", "GreenTech", "FinTech", "E-commerce", "HealthTech", "SpaceTech", "Autonomous Vehicles", "Cybersecurity", "Agritech", "EdTech", "RetailTech"]

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# List of API services for stock/ipo data
API_SERVICES = [
    "yfinance", "alphavantage", "finnhub", "iexcloud", "polygon", 
    "quandl", "twelvedata", "eodhistoricaldata", "financialmodelingprep"
]

# Function to send a message to Telegram
async def send_telegram(message: str) -> bool:
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

# Function to fetch IPO data from different APIs
async def fetch_ipo_data(ticker: str, api: str) -> Dict[str, Any]:
    try:
        logging.info(f"Fetching data for {ticker} from {api}...")
        
        if api == "yfinance":
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get("regularMarketPrice")
            market_cap = info.get("marketCap")
            sector = info.get("sector", "")
            
        elif api == "alphavantage":
            # Add Alpha Vantage API logic here
            pass
        
        elif api == "finnhub":
            # Add Finnhub API logic here
            pass
        
        # Add logic for other APIs here...

        if price is not None and market_cap is not None:
            if price <= MAX_PRICE and market_cap >= MIN_MARKET_CAP:
                if any(sector in sector_name for sector_name in SECTORS):
                    return {"ticker": ticker, "price": price, "market_cap": market_cap, "sector": sector}
                else:
                    logging.warning(f"Ignored IPO {ticker} – sector outside of required criteria.")
            else:
                logging.warning(f"Ignored IPO {ticker} – price or market cap is outside of criteria.")
        else:
            logging.warning(f"Incomplete data for {ticker}, ignored.")
    except Exception as e:
        logging.error(f"Error processing {ticker} from {api}: {e}")
    return None

# Function to fetch and filter IPO data for multiple tickers
async def fetch_and_filter_ipo_data(tickers: List[str]) -> List[Dict[str, Any]]:
    ipo_data = []
    tasks = []
    for api in API_SERVICES:
        for ticker in tickers:
            tasks.append(fetch_ipo_data(ticker, api))  # Now awaiting the result of fetch_ipo_data correctly
            
    ipo_data = await asyncio.gather(*tasks)  # Wait for all API calls to finish
    
    # Filter out None values
    ipo_data = [ipo for ipo in ipo_data if ipo is not None]
    
    logging.info(f"Total number of filtered IPOs: {len(ipo_data)}")
    return ipo_data

# Main function to send alerts for IPOs
async def send_alerts():
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    
    logging.info(f"Starting to monitor {len(tickers)} IPO companies...")

    # Fetching and filtering data for companies
    ipo_data = await fetch_and_filter_ipo_data(tickers)

    # Sending alerts only for filtered IPOs
    for ipo in ipo_data:
        try:
            ipo_msg = f"🚀 <b>IPO Alert - {ipo['ticker']}</b>\n"
            ipo_msg += f"🔹 <i>Price</i>: {ipo['price']} USD\n"
            ipo_msg += f"🔹 <i>Market Cap</i>: {ipo['market_cap']} USD\n"
            ipo_msg += f"🔹 <i>Sector</i>: {ipo['sector']}\n"
            
            # Send message to Telegram
            success = await send_telegram(ipo_msg)
            if success:
                logging.info(f"Alert for {ipo['ticker']} successfully sent.")
            else:
                logging.error(f"Error sending alert for {ipo['ticker']}")
        except Exception as e:
            logging.error(f"Error creating alert for {ipo['ticker']}: {e}")

# Main entry point for the script
if __name__ == "__main__":
    asyncio.run(send_alerts())
