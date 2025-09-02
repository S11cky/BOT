import yfinance as yf

def fetch_company_snapshot(ticker: str):
    """Získa údaje o spoločnosti podľa tickeru pomocou yfinance."""
    try:
        # Získanie údajov o akcii zo zdroja Yahoo Finance
        company = yf.Ticker(ticker)
        ipo_data = company.info

        # Extrahovanie potrebných údajov
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
        print(f"Chyba pri získavaní dát o spoločnosti {ticker}: {e}")
        return None
