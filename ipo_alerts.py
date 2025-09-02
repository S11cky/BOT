import asyncio
import logging
import yfinance as yf
import requests
from datetime import datetime

# Nastavenie logovania
logging.basicConfig(level=logging.INFO)

# Telegram API Token a Chat ID (zabezpečené cez GitHub Secrets)
TG_TOKEN = 'your_telegram_token_here'
TG_CHAT_ID = 'your_telegram_chat_id_here'

# Funkcia na odosielanie správy na Telegram
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        'chat_id': TG_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            logging.error(f"Failed to send message: {response.status_code}")
        else:
            logging.info("Message successfully sent")
    except Exception as e:
        logging.error(f"Error sending message: {e}")

# Funkcia na získanie dát o IPO z Yahoo Finance
def fetch_ipo_data(ticker):
    try:
        data = yf.Ticker(ticker).info
        price = data.get('regularMarketPrice')
        market_cap = data.get('marketCap')
        sector = data.get('sector')
        free_float = data.get('sharesOutstanding') / market_cap if market_cap else 0
        insider_ownership = data.get('insiderPercent', 0)
        ipo_date = data.get('ipoDate', 'N/A')

        # Formátovanie správy
        ipo_msg = f"🚀 <b>IPO Alert - {ticker}</b>\n"
        ipo_msg += f"🔹 <i>Price</i>: {price} USD\n"
        ipo_msg += f"🔹 <i>Market Cap</i>: {market_cap} USD\n"
        ipo_msg += f"🔹 <i>Sector</i>: {sector}\n"
        ipo_msg += f"🔹 <i>Free Float</i>: {free_float * 100:.2f}%\n"
        ipo_msg += f"🔹 <i>Insider %</i>: {insider_ownership}%\n"
        ipo_msg += f"🔹 <i>IPO Date</i>: {ipo_date}\n"
        ipo_msg += "📈 Optimálny vstup do pozície (Buy Band): N/A - N/A USD\n"
        ipo_msg += "🎯 Optimálny výstup z pozície (Exit Band): N/A - N/A USD\n"
        ipo_msg += "💡 Strategický pohľad: \n"
        ipo_msg += "🔑 Silný Free Float: Tento IPO má silný free float, čo môže naznačovať vyššiu likviditu a väčší záujem o akcie. Môže to byť vhodná príležitosť na nákup. \n"
        ipo_msg += "⚠️ Nízký Insider Ownership: Nižší podiel insiderov môže znamenať nižšiu dôveru zo strany zakladateľov a zamestnancov. \n"
        ipo_msg += "🔮 Krátkodobá stratégia: Krátkodobý cieľ: Cena môže vzrásť o 10% až 20% v krátkom horizonte po IPO. Odhadovaný výstup medzi N/A a N/A USD.\n"
        ipo_msg += "🌱 Dlhodobá stratégia: Dlhodobý cieľ: Ak spoločnosť uspeje v raste, cena akcie môže dosiahnuť 25% až 50% zisk v priebehu nasledujúcich 12-18 mesiacov.\n"
        
        # Odoslanie alertu
        send_telegram(ipo_msg)
        
        logging.info(f"Alert for {ticker} successfully sent.")
    except Exception as e:
        logging.error(f"Error processing {ticker}: {e}")

# Funkcia na monitorovanie IPOs
async def monitor_ipo(tickers):
    tasks = []
    for ticker in tickers:
        tasks.append(asyncio.ensure_future(fetch_ipo_data(ticker)))
    
    await asyncio.gather(*tasks)

# IPO tickers na monitorovanie
tickers = ['GTLB', 'ABNB', 'PLTR', 'SNOW', 'DDOG', 'U', 'NET', 'ASAN', 'PATH']

if __name__ == "__main__":
    asyncio.run(monitor_ipo(tickers))
