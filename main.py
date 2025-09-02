import os
import requests
from data_sources import fetch_company_snapshot
from typing import List, Dict, Any

# Parametre pre Small Cap a cena akcie ≤ 20 USD
MAX_PRICE = 20
MIN_MARKET_CAP = 1e9  # Minimálna trhová kapitalizácia pre IPO spoločnosti (1 miliarda USD)

# Zoznam investorov (napr. VC, Top spoločnosti, Billionaires)
VC_FUNDS = ['Sequoia Capital', 'Andreessen Horowitz', 'Benchmark', 'Greylock', 'Insight Partners']
TOP_COMPANIES = ['Apple', 'Microsoft', 'Google', 'Amazon', 'Facebook', 'Berkshire Hathaway']
TOP_BILLIONAIRES = ['Elon Musk', 'Jeff Bezos', 'Bill Gates', 'Warren Buffett', 'Mark Zuckerberg']
ALL_INVESTORS = VC_FUNDS + TOP_COMPANIES + TOP_BILLIONAIRES

def send_telegram(message: str) -> bool:
    """Send message to Telegram"""
    token = os.getenv('TG_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    
    if not token or not chat_id:
        print("Chýbajúce Telegram credentials!")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Chyba pri odosielaní Telegram správy: {e}")
        return False

def fetch_and_filter_ipo_data(tickers: List[str]) -> List[Dict[str, Any]]:
    """Fetch IPO data and filter by price and market cap"""
    ipo_data = []
    for ticker in tickers:
        try:
            print(f"Získavam údaje pre {ticker}...")
            snap = fetch_company_snapshot(ticker)
            if snap:
                price = snap.get("price_usd")
                market_cap = snap.get("market_cap_usd")
                
                # Filtrovanie podľa ceny a trhovej kapitalizácie
                if price is not None and market_cap is not None:
                    if price <= MAX_PRICE and market_cap >= MIN_MARKET_CAP:
                        ipo_data.append(snap)
                        print(f"Údaje pre {ticker} úspešne načítané")
                    else:
                        print(f"Ignorované IPO {ticker} – cena alebo market cap je mimo kritérií.")
                else:
                    print(f"Neúplné dáta pre {ticker}, ignorované.")
            else:
                print(f"Neboli získané dáta pre {ticker}")
        except Exception as e:
            print(f"Chyba pri spracovaní {ticker}: {e}")
    
    return ipo_data

def build_ipo_alert(ipo: Dict[str, Any]) -> str:
    """Build the IPO alert message for Telegram"""
    company = ipo["company_name"]
    ticker = ipo["ticker"]
    price = ipo["price_usd"]
    market_cap = ipo["market_cap_usd"]
    free_float = ipo["free_float_pct"]
    insiders_total_pct = ipo["insiders_total_pct"]
    ipo_date = ipo["ipo_first_trade_date"]
    days_to_lockup = ipo["days_to_lockup"]
    
    # Calculate potential short-term and long-term profits
    short_term_profit = f"Ak cena akcie vzrastie na 23.40 - 27.30 USD, môžete dosiahnuť zisk z 10% do 40%."
    long_term_profit = f"Optimálny exit pri 25.35 - 29.25 USD môže priniesť 30% - 50% zisk."
    
    # Generate the alert message
    message = f"""
🌍 **Investor**: Vanguard Group Inc

🚀 **IPO Alert - {company} ({ticker})**

🔹 **Aktuálna cena akcie**: {price} USD  
🔹 **Trhová kapitalizácia**: {market_cap} miliárd USD  
🔹 **Free Float**: {free_float}%  
🔹 **Insider %**: {insiders_total_pct}%  
🔹 **IPO Dátum**: {ipo_date}  
🔹 **Lock-up**: {days_to_lockup} dní (Zostáva {days_to_lockup} dní)

**Investičné hodnotenie**:  
💡 **Buy Band**: 17.55 - 21.45 USD  
🎯 **Exit Band**: 23.40 - 27.30 USD  
📈 **Optimálny Exit**: 25.35 - 29.25 USD

🔒 **Status lock-upu**: Po lock-upe

**Potenciálny zisk**:  
- **Krátkodobý zisk**: {short_term_profit}  
- **Dlhodobý zisk**: {long_term_profit}
"""
    return message

def main():
    # Získanie zoznamu IPO tickerov z verejných zdrojov
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    
    print(f"Začínam monitorovať {len(tickers)} IPO spoločností...")
    
    # Načítanie údajov o spoločnostiach a filtrovanie
    ipo_data = fetch_and_filter_ipo_data(tickers)
    
    # Poslanie alertov len pre filtrované IPO
    for ipo in ipo_data:
        try:
            ipo_msg = build_ipo_alert(ipo)
            
            # Odoslanie správy na Telegram
            success = send_telegram(ipo_msg)
            if success:
                print(f"Správa pre {ipo['ticker']} úspešne odoslaná")
            else:
                print(f"Chyba pri odosielaní správy pre {ipo['ticker']}")
                
        except Exception as e:
            print(f"Chyba pri vytváraní alertu pre {ipo['ticker']}: {e}")
    
    print("Proces dokončený.")

if __name__ == "__main__":
    main()
