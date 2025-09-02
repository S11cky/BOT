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
    days_to_lockup = ipo.get("days_to_lockup", 0)
    
    # Vytvorenie formátovaného textu pre alert
    message = f"""
🚀 IPO Alert - {company} ({ticker})

🔹 Cena akcie: {price} USD
🔹 Market Cap: {market_cap} USD
🔹 Free Float: {free_float}%
🔹 Insider %: {insiders_total_pct}%
🔹 IPO Dátum: {ipo_date}
🔹 Lock-up: {days_to_lockup} dní
"""
    return message
