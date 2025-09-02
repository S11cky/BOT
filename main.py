import os
import requests
from datetime import datetime, timedelta
from data_sources import fetch_company_snapshot
from ipo_alerts import build_ipo_alert, filter_ipo_by_lockup_and_sectors, filter_ipo_by_investors
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

def get_ipo_tickers() -> List[str]:
    """Získa zoznam IPO tickerov z verejných zdrojov a filtrovanie podľa market cap"""
    ipo_tickers = []
    
    # Príklad načítania zoznamu IPO z externého API (napr. IPOs na Nasdaq)
    try:
        url = "https://api.nasdaq.com/api/ipo-calendar"
        response = requests.get(url)
        data = response.json()
        
        # Predpokladáme, že API poskytuje IPO tickery a trhovú kapitalizáciu
        if 'data' in data and 'ipoCalendar' in data['data']:
            for ipo in data['data']['ipoCalendar']:
                ticker = ipo.get("symbol")
                market_cap = ipo.get("marketCap")  # Predpokladáme, že API poskytuje market cap
                
                if ticker and market_cap and market_cap >= MIN_MARKET_CAP:
                    ipo_tickers.append(ticker)
                    
    except Exception as e:
        print(f"Chyba pri získavaní IPO tickerov: {e}")
    
    return ipo_tickers

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

def main():
    # Získanie zoznamu IPO tickerov z verejných zdrojov
    tickers = get_ipo_tickers()  # Dynamicky načítaný zoznam IPO tickerov
    print(f"Začínam monitorovať {len(tickers)} IPO spoločností...")
    
    # Načítanie údajov o spoločnostiach a filtrovanie
    ipo_data = fetch_and_filter_ipo_data(tickers)
    
    # Filtrovanie IPO podľa lock-upu ≤ 180 dní a sektorov: Technológie, Zbrojárstvo, Zdravotníctvo, FinTech, obnoviteľné zdroje, AI, Biotechnológia, EV
    print(f"Po filtrovaní zostáva {len(ipo_data)} IPO spoločností")
    filtered_ipo_data = filter_ipo_by_lockup_and_sectors(ipo_data, sectors=[
        "Technology", "Defense", "Healthcare", "FinTech", "Renewable Energy", 
        "Cloud", "AI", "Biotech", "EV", "E-commerce", "Blockchain"
    ])
    
    # Ak neexistujú žiadne IPO dáta, skonči
    if not filtered_ipo_data:
        print("Žiadne IPO vyhovujúce kritériám.")
        return

    # Poslanie alertov len pre filtrované IPO
    for ipo in filtered_ipo_data:
        try:
            # Realistické údaje pre alert
            ipo_msg = build_ipo_alert(
                investor="Vanguard Group Inc", 
                company=ipo["company_name"],
                ticker=ipo["ticker"],
                market_cap_usd=ipo["market_cap_usd"],
                free_float_pct=ipo["free_float_pct"],
                holder_pct=6.8,  # Predpokladaná hodnota
                price_usd=ipo["price_usd"],
                history=[("14.50 USD", "3. máj 2024", None)],
                avg_buy_price_usd=ipo["price_usd"] * 0.95 if ipo["price_usd"] else None,
                insiders_total_pct=ipo["insiders_total_pct"],
                insiders_breakdown=[("Founders", ipo["insiders_total_pct"] or 10.0)],
                strategic_total_pct=(ipo["insiders_total_pct"] or 10.0) + 6.8,
                buy_band=(
                    ipo["price_usd"] * 0.9 if ipo["price_usd"] else None, 
                    ipo["price_usd"] * 1.1 if ipo["price_usd"] else None
                ),
                exit_band=(
                    ipo["price_usd"] * 1.2 if ipo["price_usd"] else None, 
                    ipo["price_usd"] * 1.4 if ipo["price_usd"] else None
                ),
                optimal_exit=(
                    ipo["price_usd"] * 1.3 if ipo["price_usd"] else None, 
                    ipo["price_usd"] * 1.5 if ipo["price_usd"] else None
                ),
                days_to_lockup=ipo["days_to_lockup"],
                lockup_release_pct=ipo["insiders_total_pct"] or 15.0,
            )
            
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
