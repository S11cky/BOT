import logging
import requests

# Definovanie funkcie pre získavanie údajov z API
def fetch_data_from_api(api_function, ticker):
    try:
        data = api_function(ticker)
        price = data.get('price', 'N/A')
        market_cap = data.get('market_cap', 'N/A')
        free_float = data.get('free_float', 'N/A')
        insider_percentage = data.get('insider_percentage', 'N/A')
        ipo_date = data.get('ipo_date', 'N/A')
        lock_up = data.get('lock_up', 'N/A')
        buy_band_lower = data.get('buy_band_lower', 'N/A')
        buy_band_upper = data.get('buy_band_upper', 'N/A')
        exit_band_lower = data.get('exit_band_lower', 'N/A')
        exit_band_upper = data.get('exit_band_upper', 'N/A')
        return price, market_cap, free_float, insider_percentage, ipo_date, lock_up, buy_band_lower, buy_band_upper, exit_band_lower, exit_band_upper
    except Exception as e:
        logging.error(f"Error fetching data for {ticker}: {e}")
        return 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'

# Funkcia pre generovanie a odoslanie alertu
def send_alert(ticker, price, market_cap, free_float, insider_percentage, ipo_date, lock_up, buy_band_lower, buy_band_upper, exit_band_lower, exit_band_upper):
    try:
        # Vytvorenie alertu vo formáte požiadaviek
        alert_message = f"🚀 <b>IPO Alert - {ticker}</b>\n"
        alert_message += f"🔹 Cena akcie: {price} USD\n"
        alert_message += f"🔹 Market Cap: {market_cap} USD\n"
        alert_message += f"🔹 Free Float: {free_float}%\n"
        alert_message += f"🔹 Insider %: {insider_percentage}%\n"
        alert_message += f"🔹 IPO Dátum: {ipo_date}\n"
        alert_message += f"🔹 Lock-up: {lock_up} dní\n\n"

        # Optimálne vstupy a výstupy (Buy Band, Exit Band)
        alert_message += f"📈 Optimálny vstup do pozície (Buy Band): {buy_band_lower} - {buy_band_upper} USD\n"
        alert_message += f"🎯 Optimálny výstup z pozície (Exit Band): {exit_band_lower} - {exit_band_upper} USD\n\n"

        # Stratégie
        alert_message += f"💡 Strategický pohľad: \n"
        alert_message += f"🔑 Silný Free Float: Tento IPO má silný free float, čo môže naznačovať vyššiu likviditu a väčší záujem o akcie. Môže to byť vhodná príležitosť na nákup. \n"
        alert_message += f"⚠️ Nízký Insider Ownership: Nižší podiel insiderov môže znamenať nižšiu dôveru zo strany zakladateľov a zamestnancov. \n\n"
        alert_message += f"🔮 Krátkodobá stratégia: Cena môže vzrásť o 10% až 20% v krátkom horizonte po IPO. \n"
        alert_message += f"🌱 Dlhodobá stratégia: Ak spoločnosť uspeje v raste, cena akcie môže dosiahnuť 25% až 50% zisk v priebehu nasledujúcich 12-18 mesiacov. \n"

        # Odoslanie správy na Telegram
        send_telegram(alert_message)

        logging.info(f"Alert for {ticker} successfully sent.")

    except Exception as e:
        logging.error(f"Error sending alert for {ticker}: {e}")

# Funkcia pre odosielanie Telegram správ
def send_telegram(alert_message):
    telegram_api_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        response = requests.post(telegram_api_url, data={
            "chat_id": TG_CHAT_ID,
            "text": alert_message,
            "parse_mode": "HTML"
        })
        if response.status_code == 200:
            logging.info(f"Message successfully sent.")
        else:
            logging.error(f"Failed to send message. Status Code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending message: {e}")

# Hlavná funkcia pre monitoring IPOs
async def monitor_ipo(tickers):
    for ticker in tickers:
        # Získanie dát cez funkciu pre API
        price, market_cap, free_float, insider_percentage, ipo_date, lock_up, buy_band_lower, buy_band_upper, exit_band_lower, exit_band_upper = fetch_data_from_api(yfinance.get_stock_data, ticker)

        # Odoslanie alertu
        send_alert(ticker, price, market_cap, free_float, insider_percentage, ipo_date, lock_up, buy_band_lower, buy_band_upper, exit_band_lower, exit_band_upper)

# Spustenie monitorovania IPO spoločností
if __name__ == "__main__":
    tickers = ["GTLB", "ABNB", "PLTR", "SNOW", "DDOG", "U", "NET", "ASAN", "PATH"]
    asyncio.run(monitor_ipo(tickers))
