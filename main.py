from data_sources import fetch_company_snapshot
import logging
import requests

# Parametre pre filtrovanie IPO
MAX_PRICE = 50  # Zvýšená cena akcie
MIN_MARKET_CAP = 5e8  # Minimálna trhová kapitalizácia 500 miliónov USD
SECTORS = ["Technológie", "Biotechnológia", "AI", "Zelené technológie", "FinTech", "E-commerce", "HealthTech", "SpaceTech", "Autonómne vozidlá", "Cybersecurity", "Agritech", "EdTech", "RetailTech"]

# Telegram API nastavenia
TELEGRAM_TOKEN = 'YOUR_TELEGRAM_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'

def send_telegram(message: str) -> bool:
    """Odosiela správu na Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            logging.info(f"Správa úspešne odoslaná: {message[:50]}...")  # Prvých 50 znakov správy
            return True
        else:
            logging.error(f"Chyba pri odosielaní správy: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Chyba pri odosielaní Telegram správy: {e}")
        return False

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

def build_ipo_alert(ipo: dict) -> str:
    """Vytvorenie textu alertu pre Telegram na základe IPO dát"""
    
    # Získanie dát z IPO dictu
    company = ipo["company_name"]
    ticker = ipo["ticker"]
    price = ipo["price_usd"]
    market_cap = ipo["market_cap_usd"]
    free_float = ipo.get("free_float_pct", 0)
    insiders_total_pct = ipo.get("insiders_total_pct", 0)
    ipo_date = ipo.get("ipo_first_trade_date", "Neznámy")
    days_to_lockup = ipo.get("days_to_lockup", "Neznámy")
    
    # Zaokrúhlenie hodnôt na rozumný počet desatinných miest
    price = round(price, 2)
    market_cap = round(market_cap / 1e9, 2)  # Trhová kapitalizácia v miliardách USD
    free_float = round(free_float, 2)
    insiders_total_pct = round(insiders_total_pct, 2)
    
    # Výpočty pre optimálny vstup a výstup (Buy band a Exit band)
    buy_band_lower = round(price * 0.85, 2)  # 15% pod aktuálnou cenou
    buy_band_upper = round(price * 0.90, 2)  # 10% pod aktuálnou cenou
    exit_band_lower = round(price * 1.10, 2)  # 10% nad aktuálnou cenou
    exit_band_upper = round(price * 1.20, 2)  # 20% nad aktuálnou cenou
    
    # Definovanie stratégie (strategický pohľad)
    strategy = ""
    if free_float > 70:
        strategy += "🔑 **Silný Free Float**: Tento IPO má silný free float, čo môže naznačovať vyššiu likviditu a väčší záujem o akcie. Môže to byť vhodná príležitosť na nákup. "
    if insiders_total_pct < 10:
        strategy += "⚠️ **Nízký Insider Ownership**: Nižší podiel insiderov môže znamenať nižšiu dôveru zo strany zakladateľov a zamestnancov. "

    # Vytvorenie formátovaného textu pre alert
    message = f"""
🚀 IPO Alert - {company} ({ticker})

🔹 **Cena akcie**: {price} USD
🔹 **Market Cap**: {market_cap} miliárd USD
🔹 **Free Float**: {free_float}%
🔹 **Insider %**: {insiders_total_pct}%
🔹 **IPO Dátum**: {ipo_date}
🔹 **Lock-up**: {days_to_lockup} dní

📈 **Optimálny vstup do pozície (Buy Band)**: {buy_band_lower} - {buy_band_upper} USD
🎯 **Optimálny výstup z pozície (Exit Band)**: {exit_band_lower} - {exit_band_upper} USD

💡 **Strategický pohľad**: 
{strategy}
"""
    return message

def fetch_and_filter_ipo_data(tickers: list):
    """Načítanie a filtrovanie IPO dát pre viacero tickerov"""
    ipo_data = []
    for ticker in tickers:
        ipo = fetch_ipo_data(ticker)
        if ipo:
            ipo_data.append(ipo)
    
    logging.info(f"Celkový počet filtrovaných IPO: {len(ipo_data)}")
    return ipo_data

def send_alerts():
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    
    logging.info(f"Začínam monitorovať {len(tickers)} IPO spoločností...")
    
    # Načítanie údajov o spoločnostiach a filtrovanie
    ipo_data = fetch_and_filter_ipo_data(tickers)
    
    # Poslanie alertov len pre filtrované IPO
    for ipo in ipo_data:
        try:
            ipo_msg = build_ipo_alert(ipo)  # Vytvorí správy pre alerty
            # Odoslanie správy na Telegram
            success = send_telegram(ipo_msg)
            if success:
                logging.info(f"Alert pre {ipo['ticker']} úspešne odoslaný.")
            else:
                logging.error(f"Chyba pri odosielaní alertu pre {ipo['ticker']}")
        except Exception as e:
            logging.error(f"Chyba pri vytváraní alertu pre {ipo['ticker']}: {e}")
    
    logging.info("Proces dokončený.")

# Spustenie skriptu na testovanie
if __name__ == "__main__":
    send_alerts()
