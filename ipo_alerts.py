# ipo_alerts.py

def build_ipo_alert(ipo: dict) -> str:
    """Vytvoriť alert správu pre IPO v požadovanom formáte"""
    
    # Formátovanie správy pre IPO alert
    alert_msg = f"🚀 IPO Alert - {ipo['company_name']} ({ipo['ticker']})\n"
    alert_msg += f"\n"
    alert_msg += f"🔹 Cena akcie: {ipo['price']} USD\n"
    alert_msg += f"🔹 Market Cap: {ipo['market_cap']} USD\n"
    alert_msg += f"🔹 Free Float: {ipo['free_float']}%\n"
    alert_msg += f"🔹 Insider %: {ipo['insider_percent']}%\n"
    alert_msg += f"🔹 IPO Dátum: {ipo['ipo_date'] if ipo['ipo_date'] else 'N/A'}\n"
    alert_msg += f"🔹 Lock-up: {ipo['lock_up_period']} dní\n"
    alert_msg += f"\n"
    alert_msg += f"📈 Optimálny vstup do pozície (Buy Band): {ipo['buy_band_min']} - {ipo['buy_band_max']} USD\n"
    alert_msg += f"🎯 Optimálny výstup z pozície (Exit Band): {ipo['exit_band_min']} - {ipo['exit_band_max']} USD\n"
    alert_msg += f"\n"
    alert_msg += f"💡 Strategický pohľad: \n"
    alert_msg += f"🔑 {ipo['strategic_view']}\n"
    alert_msg += f"⚠️ {ipo['insider_alert']}\n"
    alert_msg += f"\n"
    alert_msg += f"🔮 Krátkodobá stratégia: Krátkodobý cieľ: {ipo['short_term_goal']} \n"
    alert_msg += f"🌱 Dlhodobá stratégia: Dlhodobý cieľ: {ipo['long_term_goal']} \n"

    return alert_msg
