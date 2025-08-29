import os
import requests
from data_sources import fetch_company_snapshot
from ipo_alerts import build_ipo_alert, filter_ipo_by_lockup

def send_telegram(message: str):
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

def main():
    # Zoznam tickerov IPO spoločností (bez ZI ktoré spôsobuje chybu)
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    
    print(f"Začínam monitorovať {len(tickers)} IPO spoločností...")
    
    # Načítanie údajov o spoločnostiach
    ipo_data = []
    for ticker in tickers:
        try:
            print(f"Získavam údaje pre {ticker}...")
            snap = fetch_company_snapshot(ticker)
            if snap and snap.get('price_usd'):
                ipo_data.append(snap)
                print(f"Údaje pre {ticker} úspešne načítané")
            else:
                print(f"Chyba pri načítaní údajov pre {ticker}")
        except Exception as e:
            print(f"Chyba pri spracovaní {ticker}: {e}")
    
    # Filtrovanie len IPO s lock-upom ≤ 180 dní
    filtered_ipo_data = filter_ipo_by_lockup(ipo_data)
    print(f"Po filtrovaní zostáva {len(filtered_ipo_data)} spoločností")
    
    if not filtered_ipo_data:
        print("Žiadne spoločnosti na odoslanie")
        return 0
    
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
            
            # Odoslanie správy
            success = send_telegram(ipo_msg)
            if success:
                print(f"Správa pre {ipo['ticker']} úspešne odoslaná")
            else:
                print(f"Chyba pri odosielaní správy pre {ipo['ticker']}")
                
        except Exception as e:
            print(f"Chyba pri vytváraní alertu pre {ipo['ticker']}: {e}")
    
    return 0

if __name__ == "__main__":
    main()
