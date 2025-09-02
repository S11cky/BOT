from data_sources import fetch_company_snapshot
import logging

# Parametre pre filtrovanie IPO
MAX_PRICE = 50  # Zvýšená cena akcie
MIN_MARKET_CAP = 5e8  # Minimálna trhová kapitalizácia 500 miliónov USD
SECTORS = ["Technológie", "Biotechnológia", "AI", "Zelené technológie", "FinTech", "E-commerce", "HealthTech", "SpaceTech", "Autonómne vozidlá", "Cybersecurity", "Agritech", "EdTech", "RetailTech"]

def fetch_ipo_data(ticker: str):
    """Načítanie dát o IPO pre jednotlivé tickery"""
    try:
        ipo = fetch_company_snapshot(ticker)
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
                        logging.warning(f"Ignorované IPO {ticker} – sektor mimo požiadaviek.")
                else:
                    logging.warning(f"Ignorované IPO {ticker} – cena alebo market cap je mimo kritérií.")
            else:
                logging.warning(f"Neúplné dáta pre {ticker}, ignorované.")
        else:
            logging.warning(f"Neboli získané dáta pre {ticker}")
    except Exception as e:
        logging.error(f"Chyba pri spracovaní {ticker}: {e}")
    return None

def fetch_and_filter_ipo_data(tickers: list):
    """Načítanie a filtrovanie IPO dát pre viacero tickerov"""
    ipo_data = []
    for ticker in tickers:
        ipo = fetch_ipo_data(ticker)
        if ipo:
            ipo_data.append(ipo)
    
    logging.info(f"Celkový počet filtrovaných IPO: {len(ipo_data)}")
    return ipo_data
