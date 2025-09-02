def build_ipo_alert(ipo_data: Dict[str, Any]) -> str:
    try:
        ticker = ipo_data['ticker']
        price = ipo_data['price']
        market_cap = ipo_data['market_cap']
        sector = ipo_data['sector']
        free_float = ipo_data.get('free_float', 'N/A')
        insider_ownership = ipo_data.get('insider_ownership', 'N/A')
        ipo_date = ipo_data.get('ipo_date', 'N/A')
        lock_up = ipo_data.get('lock_up', 'N/A')
        buy_band_lower = ipo_data.get('buy_band_lower', 'N/A')
        buy_band_upper = ipo_data.get('buy_band_upper', 'N/A')
        exit_band_lower = ipo_data.get('exit_band_lower', 'N/A')
        exit_band_upper = ipo_data.get('exit_band_upper', 'N/A')

        alert_message = f"""🚀 <b>IPO Alert - {ticker}</b>
🔹 Cena akcie: {price} USD
🔹 Market Cap: {market_cap} USD
🔹 Sektor: {sector}

🔹 Free Float: {free_float}%
🔹 Insider %: {insider_ownership}%
🔹 IPO Dátum: {ipo_date}
🔹 Lock-up: {lock_up} dní

📈 **Optimálny vstup do pozície (Buy Band)**: {buy_band_lower} - {buy_band_upper} USD
🎯 **Optimálny výstup z pozície (Exit Band)**: {exit_band_lower} - {exit_band_upper} USD

💡 **Strategický pohľad**: 
🔑 **Silný Free Float**: Tento IPO má silný free float, čo môže naznačovať vyššiu likviditu a väčší záujem o akcie. Môže to byť vhodná príležitosť na nákup. ⚠️ **Nízký Insider Ownership**: Nižší podiel insiderov môže znamenať nižšiu dôveru zo strany zakladateľov a zamestnancov. 

🔮 **Krátkodobá stratégia**: **Krátkodobý cieľ**: Cena môže vzrásť o 10% až 20% v krátkom horizonte po IPO. Odhadovaný výstup medzi {exit_band_lower} a {exit_band_upper} USD.
🌱 **Dlhodobá stratégia**: **Dlhodobý cieľ**: Ak spoločnosť uspeje v raste, cena akcie môže dosiahnuť 25% až 50% zisk v priebehu nasledujúcich 12-18 mesiacov."""
        return alert_message
    except Exception as e:
        logging.error(f"Error creating IPO alert: {e}")
        return None
