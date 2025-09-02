import logging
import sqlite3
from data_sources import fetch_company_snapshot  # Import z data_sources.py
from ipo_alerts import build_ipo_alert  # Import z ipo_alerts.py
from typing import Dict, Any
import requests

# Nastavenie logovania
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Inicializácia databázy pre odoslané alerty
def mark_alert_sent(ticker: str):
    """Uloží, že alert bol odoslaný pre daný ticker"""
    conn = sqlite3.connect('mna_watch.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO sent_alerts (ticker) VALUES (?);', (ticker,))
    conn.commit()
    conn.close()

def is_alert_sent(ticker: str) -> bool:
    """Skontroluje, či bol alert už odoslaný pre daný ticker"""
    conn = sqlite3.connect('mna_watch.db')
    c = conn.cursor()
    c.execute('SELECT 1 FROM sent_alerts WHERE ticker = ?;', (ticker,))
    result = c.fetchone()
    conn.close()
    return result is not None

def monitor_buy_band(ipo: dict) -> bool:
    """Skontroluje, či cena akcie klesla do optimálneho nákupného pásma."""
    price = ipo.get("price_usd")
    if price is None:
        return False
    
    # Určte optimálne nákupné pásmo
    buy_band_lower = round(price * 0.85, 2)  # 15% pod aktuálnou cenou
    buy_band_upper = round(price * 0.90, 2)  # 10% pod aktuálnou cenou
    
    # Skontroluj, či cena akcie spadla do tohto pásma
    if price >= buy_band_lower and price <= buy_band_upper:
        return True
    return False

def send_telegram(message: str) -> bool:
    """Odosiela správu na Telegram"""
    token = 'YOUR_TELEGRAM_TOKEN'
    chat_id = 'YOUR_CHAT_ID'
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            logging.info(f"Správa úspešne odoslaná: {message[:50]}...")
            return True
        else:
            logging.error(f"Chyba pri odosielaní správy: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Chyba pri odosielaní Telegram správy: {e}")
        return False

def check_and_send_alert(ipo: dict):
    ticker = ipo.get("ticker")
    if not ticker:
        return

    if is_alert_sent(ticker):  # Skontrolujeme databázu
        logging.info(f"Alert už bol odoslaný pre {ticker}, preskakuje sa.")
        return

    if monitor_buy_band(ipo):
        ipo_msg = build_ipo_alert(ipo)
        ipo_msg += "\n🎯 **Poznámka**: Cena akcie spadla do optimálneho nákupného pásma, čo môže predstavovať príležitosť na nákup."
        
        success = send_telegram(ipo_msg)
        if success:
            logging.info(f"Alert pre {ticker} úspešne odoslaný.")
            mark_alert_sent(ticker)  # Uložíme do databázy, že alert bol odoslaný
        else:
            logging.error(f"Chyba pri odosielaní alertu pre {ticker}")

# Hlavná funkcia na spustenie procesu
def send_alerts():
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    
    logging.info(f"Začínam monitorovať {len(tickers)} IPO spoločností...")
    
    # Načítanie údajov o spoločnostiach a filtrovanie
    ipo_data = fetch_and_filter_ipo_data(tickers)  # Implementujte túto funkciu na načítanie IPO dát
    
    # Poslanie alertov len pre filtrované IPO
    for ipo in ipo_data:
        try:
            check_and_send_alert(ipo)  # Skontroluje, či bol alert odoslaný a ak cena spadla do nákupného pásma
        except Exception as e:
            logging.error(f"Chyba pri vytváraní alertu pre {ipo['ticker']}: {e}")
    
    logging.info("Proces dokončený.")

# Spustenie procesu (napríklad každých 15 minút)
if __name__ == "__main__":
    send_alerts()
