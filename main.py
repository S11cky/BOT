import logging
import aiohttp  # Importovanie knižnice aiohttp
import asyncio  # Pridaný import pre asyncio
from data_sources import fetch_company_snapshot  # Import funkcie na získanie údajov o IPO

# Parametre pre filtrovanie IPO
MAX_PRICE = 50  # Zvýšená cena akcie
MIN_MARKET_CAP = 5e8  # Minimálna trhová kapitalizácia 500 miliónov USD
SECTORS = ["Technológie", "Biotechnológia", "AI", "Zelené technológie", "FinTech", "E-commerce", "HealthTech", "SpaceTech", "Autonómne vozidlá", "Cybersecurity", "Agritech", "EdTech", "RetailTech"]

# Telegram API nastavenia
TELEGRAM_TOKEN = 'YOUR_TELEGRAM_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'

# Asynchrónne odosielanie správ na Telegram
async def send_telegram(message: str) -> bool:
    """Odosiela správu na Telegram asynchrónne"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=5) as response:
                if response.status == 200:
                    logging.info(f"Správa úspešne odoslaná: {message[:50]}...")  # Prvých 50 znakov správy
                    return True
                else:
                    logging.error(f"Chyba pri odosielaní správy: {response.status}")
                    return False
        except Exception as e:
            logging.error(f"Chyba pri odosielaní Telegram správy: {e}")
            return False

# Asynchrónne získanie IPO dát
async def fetch_ipo_data(ticker: str, session: aiohttp.ClientSession):
    """Načítanie dát o IPO pre jednotlivé tickery asynchrónne"""
    try:
        ipo = await fetch_company_snapshot(ticker, session)  # Funkcia fetch_company_snapshot by mala byť asynchrónna
        if ipo:
            price = ipo.get("price_usd")
            market_cap = ipo.get("market_cap_usd")
            sector = ipo.get("sector", "")

            # Filtrujeme IPO podľa ceny, trhovej kapitalizácie a sektora
            if price is not None and market_cap is not None:
                if price <= MAX_PRICE and market_cap >= MIN_MARKET_CAP:
                    if any(sector in sector_name for sector_name in SECTORS):
                        return ipo
                    else:
                        logging.warning(f"Ignorované IPO {ticker} – sektor mimo požiadaviek. Sektor: {sector}")
                else:
                    logging.warning(f"Ignorované IPO {ticker} – cena alebo market cap je mimo kritérií. Cena: {price}, Market Cap: {market_cap}")
            else:
                logging.warning(f"Neúplné dáta pre {ticker}, ignorované.")
        else:
            logging.warning(f"Neboli získané dáta pre {ticker}")
    except Exception as e:
        logging.error(f"Chyba pri spracovaní {ticker}: {e}")
    return None

async def fetch_and_filter_ipo_data(tickers: list):
    """Načítanie a filtrovanie IPO dát pre viacero tickerov asynchrónne"""
    ipo_data = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for ticker in tickers:
            tasks.append(fetch_ipo_data(ticker, session))  # Pridáme ďalšie zdroje
        results = await asyncio.gather(*tasks)  # Čaká na všetky výsledky súčasne
        ipo_data = [ipo for ipo in results if ipo]  # Filtrujeme None hodnoty
    logging.info(f"Celkový počet filtrovaných IPO: {len(ipo_data)}")
    return ipo_data

# Funkcia na posielanie alertov pre každé IPO
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

# Spustenie skriptu na testovanie
if __name__ == "__main__":
    asyncio.run(send_alerts())
