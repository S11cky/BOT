import logging
import requests
import yfinance as yf
import aiohttp
import asyncio
from typing import Dict, Any

# Parametre pre filtrovanie IPO
MAX_PRICE = 50  # Maximálna cena akcie
MIN_MARKET_CAP = 5e8  # Minimálna trhová kapitalizácia (500 miliónov USD)
SECTORS = ["Technology", "Biotechnology", "AI", "Green Technologies", "FinTech", "E-commerce", "HealthTech", "SpaceTech", "Autonomous Vehicles", "Cybersecurity", "Agritech", "EdTech", "RetailTech"]

# Logovanie
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Alpha Vantage API - API kľúč
ALPHA_VANTAGE_API_KEY = "tvoj_alpha_vantage_api_kluc"

# IEX Cloud API - API kľúč
IEX_CLOUD_API_KEY = "tvoj_iex_cloud_api_kluc"

# Funkcia na získanie údajov cez Alpha Vantage API
def fetch_from_alpha_vantage(ticker: str) -> Dict[str, Any]:
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if "Time Series (Daily)" in data:
            last_close = list(data["Time Series (Daily)"].values())[0]["4. close"]
            market_cap = None  # Market cap nie je priamo dostupný z Alpha Vantage
            sector = None  # Sector je tiež dostupný cez iný endpoint

            return {
                "price_usd": float(last_close),
                "market_cap_usd": market_cap,
                "sector": sector
            }
        else:
            logging.warning(f"Chyba pri získavaní dát pre {ticker}: {data}")
            return None
    except Exception as e:
        logging.error(f"Chyba pri získavaní dát pre {ticker}: {e}")
        return None

# Funkcia na získanie údajov cez IEX Cloud API
def fetch_from_iex_cloud(ticker: str) -> Dict[str, Any]:
    try:
        url = f"https://cloud.iexapis.com/stable/stock/{ticker}/quote?token={IEX_CLOUD_API_KEY}"
        response = requests.get(url)
        data = response.json()

        price = data.get("latestPrice")
        market_cap = data.get("marketCap")
        sector = data.get("sector")

        return {
            "price_usd": price,
            "market_cap_usd": market_cap,
            "sector": sector
        }
    except Exception as e:
        logging.error(f"Chyba pri získavaní dát pre {ticker}: {e}")
        return None

# Asynchrónna funkcia na získanie IPO dát
async def fetch_company_snapshot(ticker: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
    try:
        # Skúsime najprv Alpha Vantage, potom IEX Cloud, ak Alpha Vantage nevráti dáta
        ipo = fetch_from_alpha_vantage(ticker)
        if ipo:
            return ipo
        
        ipo = fetch_from_iex_cloud(ticker)
        if ipo:
            return ipo
        
        # Ako zálohu použijeme yfinance (ak nič iné nefunguje)
        company = yf.Ticker(ticker)
        price = company.history(period="1d")['Close'].iloc[0]
        market_cap = company.info.get('marketCap', None)
        sector = company.info.get('sector', '')

        return {
            "price_usd": price,
            "market_cap_usd": market_cap,
            "sector": sector
        }
    except Exception as e:
        logging.error(f"Chyba pri získavaní dát pre {ticker}: {e}")
        return None

# Funkcia na odoslanie správy na Telegram
def send_telegram(message: str):
    """Send message to Telegram"""
    token = "tvoj_telegram_bot_token"  # Zadaj svoj token sem
    chat_id = "tvoj_chat_id"  # Zadaj svoje chat ID sem

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)  # Timeout na 5 sekúnd
        if response.status_code == 200:
            logging.info(f"Správa úspešne odoslaná: {message[:50]}...")  # Zobraziť len prvých 50 znakov správy
        else:
            logging.error(f"Chyba pri odosielaní správy: {response.status_code}")
    except Exception as e:
        logging.error(f"Chyba pri odosielaní Telegram správy: {e}")

# Asynchrónna funkcia na odoslanie alertu
async def send_alert(ticker, price, buy_band_lower, buy_band_upper):
    if buy_band_lower is None or buy_band_upper is None:
        return
    
    # Vytvoríme správu
    alert_message = f"🚀 IPO Alert - {ticker}\n"
    alert_message += f"🔹 **Cena akcie**: {price} USD\n"
    alert_message += f"📈 **Optimálny vstup do pozície (Buy Band)**: {buy_band_lower:.2f} - {buy_band_upper:.2f} USD\n"
    
    # Pošleme alert
    send_telegram(alert_message)

# Asynchrónna funkcia na monitorovanie IPO
async def monitor_ipo(tickers):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for ticker in tickers:
            tasks.append(fetch_company_snapshot(ticker, session))
        
        results = await asyncio.gather(*tasks)
        
        for ipo_data in results:
            if ipo_data:
                price = ipo_data.get("price_usd")
                sector = ipo_data.get("sector", "Unknown")
                market_cap = ipo_data.get("market_cap_usd")
                
                # Dynamicky vypočítať Buy band
                volatility = 0.05  # Volatilita (ako príklad, môžeš ju upraviť)
                buy_band_lower = price - (price * volatility)
                buy_band_upper = price + (price * volatility)

                await send_alert(sector, price, buy_band_lower, buy_band_upper)

# Spustenie asynchrónneho monitorovania IPO spoločností
if __name__ == "__main__":
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    asyncio.run(monitor_ipo(tickers))
