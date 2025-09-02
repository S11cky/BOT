def build_ipo_alert(ipo: dict) -> str:
    """Vytvorí formátovaný alert pre IPO spoločnosť v požadovanom formáte"""
    company_name = ipo.get("company_name", "N/A")
    ticker = ipo.get("ticker", "N/A")
    price = ipo.get("price_usd", "N/A")
    market_cap = ipo.get("market_cap_usd", "N/A")
    free_float_pct = ipo.get("free_float_pct", "N/A")
    insiders_pct = ipo.get("insiders_total_pct", "N/A")
    ipo_first_trade_date = ipo.get("ipo_first_trade_date", "N/A")
    days_to_lockup = ipo.get("days_to_lockup", "N/A")
    
    # Definovanie optimálnych pásiem (buy, exit) podľa ceny IPO
    buy_band_min = ipo.get("buy_band_min", "N/A")
    buy_band_max = ipo.get("buy_band_max", "N/A")
    exit_band_min = ipo.get("exit_band_min", "N/A")
    exit_band_max = ipo.get("exit_band_max", "N/A")
    
    # Formátovaná správa pre Telegram
    message = f"""
🚀 <b>IPO Alert - {company_name} ({ticker})</b>

🔹 <i>Cena akcie</i>: {price} USD
🔹 <i>Market Cap</i>: {market_cap} USD
🔹 <i>Free Float</i>: {free_float_pct}%
🔹 <i>Insider %</i>: {insiders_pct}%
🔹 <i>IPO Dátum</i>: {ipo_first_trade_date}
🔹 <i>Lock-up</i>: {days_to_lockup} dní

📈 <b>Optimálny vstup do pozície (Buy Band)</b>: {buy_band_min} - {buy_band_max} USD
🎯 <b>Optimálny výstup z pozície (Exit Band)</b>: {exit_band_min} - {exit_band_max} USD

💡 <b>Strategický pohľad</b>: 
🔑 <i>Silný Free Float</i>: Tento IPO má silný free float, čo môže naznačovať vyššiu likviditu a väčší záujem o akcie. Môže to byť vhodná príležitosť na nákup. ⚠️ <i>Nízký Insider Ownership</i>: Nižší podiel insiderov môže znamenať nižšiu dôveru zo strany zakladateľov a zamestnancov. 

🔮 <b>Krátkodobá stratégia</b>: <i>Krátkodobý cieľ</i>: Cena môže vzrásť o 10% až 20% v krátkom horizonte po IPO. Odhadovaný výstup medzi {exit_band_min} a {exit_band_max} USD.
🌱 <b>Dlhodobá stratégia</b>: <i>Dlhodobý cieľ</i>: Ak spoločnosť uspeje v raste, cena akcie môže dosiahnuť 25% až 50% zisk v priebehu nasledujúcich 12-18 mesiacov.
"""
    return message
