import aiohttp

async def fetch_company_snapshot(ticker: str, session: aiohttp.ClientSession):
    """Asynchrónne načítanie údajov o akcii cez aiohttp"""
    try:
        url = f"https://api.example.com/stocks/{ticker}"  # Tu použiješ správnu URL API na získanie údajov
        async with session.get(url) as response:
            data = await response.json()

        # Predpokladajme, že API vráti údaje v tomto formáte
        price = data.get("price_usd")
        market_cap = data.get("market_cap_usd")
        sector = data.get("sector", "")

        return {
            "price_usd": price,
            "market_cap_usd": market_cap,
            "sector": sector
        }
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None
