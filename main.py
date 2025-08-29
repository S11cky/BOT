from data_sources import fetch_company_snapshot
from ipo_alerts import build_ipo_alert, filter_ipo_by_lockup

def main():
    # Zoznam tickerov
    tickers = ["GTLB", "ABNB", "PLTR"]  # Nahradiť dynamicky podľa potreby

    # Filtrovanie IPO podľa lock-upu ≤ 180 dní
    ipo_data = []
    for ticker in tickers:
        snap = fetch_company_snapshot(ticker)
        ipo_data.append(snap)

    # Filtrovanie len IPO ≤ 180 dní
    filtered_ipo_data = filter_ipo_by_lockup(ipo_data)

    # Poslanie alertov len pre filtrované IPO
    for ipo in filtered_ipo_data:
        ipo_msg = build_ipo_alert(
            investor="BlackRock", 
            company=ipo["company_name"],
            ticker=ipo["ticker"],
            market_cap_usd=ipo["market_cap_usd"],
            free_float_pct=ipo["free_float_pct"],
            holder_pct=6.8,  # Predpokladaná hodnota
            price_usd=ipo["price_usd"],
            history=[("14.50 USD", "3. máj 2024", None)],
            avg_buy_price_usd=15.0,
            insiders_total_pct=ipo["insiders_total_pct"],
            insiders_breakdown=[("Founders", 6.0)],
            strategic_total_pct=10.0,
            buy_band=(14.40, 14.80),
            exit_band=(16.0, 18.0),
            optimal_exit=(17.0, 20.0),
            days_to_lockup=ipo["days_to_lockup"],
            lockup_release_pct=5.0,
        )
        send_telegram(ipo_msg)

    return 0
