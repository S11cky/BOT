import requests
from bs4 import BeautifulSoup
import yfinance as yf
import aiohttp

# Parametre pre filtrovanie IPO
MAX_PRICE = 50  # Zvýšená cena akcie
MIN_MARKET_CAP = 5e8  # Minimálna trhová kapitalizácia 500 miliónov USD
SECTORS = ["Technológie", "Biotechnológia", "AI", "Zelené technológie", "FinTech", "E-commerce", "HealthTech", "SpaceTech", "Autonómne vozidlá", "Cybersecurity", "Agritech", "EdTech", "RetailTech"]

def fetch_ipo_data_yahoo(ticker: str):
    """Načítanie IPO dát z Yahoo Finance"""
    try:
        company = yf.Ticker(ticker)
        ipo_data = company.info
        snapshot = {
            "company_name": ipo_data.get("shortName", "N/A"),
            "ticker": ticker,
            "price_usd": ipo_data.get("regularMarketPrice", 0),
            "market_cap_usd": ipo_data.get("marketCap", 0),
            "sector": ipo_data.get("sector", ""),
            "free_float_pct": ipo_data.get("floatShares", 0) / ipo_data.get("sharesOutstanding", 1) * 100,
            "insiders_total_pct": ipo_data.get("insiderOwnership", 0),
            "ipo_first_trade_date": ipo_data.get("ipoStartDate", "N/A"),
            "days_to_lockup": ipo_data.get("daysToLockup", "N/A")
        }
        return snapshot
    except Exception as e:
        print(f"Chyba pri získavaní dát z Yahoo pre {ticker}: {e}")
        return None

async def fetch_ipo_data_from_nasdaq(ticker: str, session: aiohttp.ClientSession):
    """Načítanie IPO dát z NASDAQ"""
    url = f"https://www.nasdaq.com/market-activity/ipos/{ticker}"
    async with session.get(url) as response:
        if response.status == 200:
            page_content = await response.text()
            soup = BeautifulSoup(page_content, 'html.parser')
            ipo_data = {
                "company_name": soup.find("h1", class_="company-name").text.strip(),
                "price_usd": soup.find("span", class_="ipo-price").text.strip(),
                "market_cap_usd": soup.find("span", class_="market-cap").text.strip(),
                # Pridaj ďalšie relevantné informácie z NASDAQ
            }
            return ipo_data
        else:
            print(f"Chyba pri získavaní dát z NASDAQ pre {ticker}")
            return None

async def fetch_ipo_data_from_benzinga(ticker: str, session: aiohttp.ClientSession):
    """Načítanie IPO dát z Benzinga"""
    url = f"https://www.benzinga.com/ipo-calendar/{ticker}"
    async with session.get(url) as response:
        if response.status == 200:
            page_content = await response.text()
            soup = BeautifulSoup(page_content, 'html.parser')
            ipo_data = {
                "company_name": soup.find("h1", class_="company-name").text.strip(),
                "price_usd": soup.find("span", class_="ipo-price").text.strip(),
                "market_cap_usd": soup.find("span", class_="market-cap").text.strip(),
                # Pridaj ďalšie relevantné informácie z Benzinga
            }
            return ipo_data
        else:
            print(f"Chyba pri získavaní dát z Benzinga pre {ticker}")
            return None

async def fetch_and_filter_ipo_data(tickers: list):
    """Načítanie a filtrovanie IPO dát pre viacero tickerov asynchrónne"""
    ipo_data = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for ticker in tickers:
            tasks.append(fetch_ipo_data_yahoo(ticker))  # Pridáme ďalšie zdroje
            tasks.append(fetch_ipo_data_from_nasdaq(ticker, session))
            tasks.append(fetch_ipo_data_from_benzinga(ticker, session))
        
        results = await asyncio.gather(*tasks)
        ipo_data = [ipo for ipo in results if ipo]  # Filtrujeme None hodnoty
    logging.info(f"Celkový počet filtrovaných IPO: {len(ipo_data)}")
    return ipo_data

# Príklad spustenia
async def send_alerts():
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    
    logging.info(f"Začínam monitorovať {len(tickers)} IPO spoločností...")
    
    # Načítanie údajov o spoločnostiach a filtrovanie asynchrónne
    ipo_data = await fetch_and_filter_ipo_data(tickers)
    
    # Poslanie alertov len pre filtrované IPO asynchrónne
    tasks = []
    for ipo in ipo_data:
        ipo_msg = build_ipo_alert(ipo)  # Vytvorí správy pre alerty
        tasks.append(send_telegram(ipo_msg))  # Vytvoríme úlohu pre každý alert

    results = await asyncio.gather(*tasks)  # Spustíme všetky úlohy súčasne
    logging.info(f"Alerty odoslané: {sum(results)}")

if __name__ == "__main__":
    asyncio.run(send_alerts())
