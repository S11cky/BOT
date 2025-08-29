# -*- coding: utf-8 -*-
"""
data_sources.py – reálne dostupné zdroje (Yahoo Finance)
- cena, market cap, free float, insider %
- IPO dátum ~ prvý obchodný deň (odhad)
- Lock-up rátame 180 dní od IPO, ak je už po lock-upe → None
"""

from datetime import date, timedelta
from typing import Dict, Any, Optional, Tuple
import math
import yfinance as yf
import pandas as pd

LOCKUP_DAYS_DEFAULT = 180

def _safe_float(v) -> Optional[float]:
    try:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        return float(v)
    except Exception:
        return None

def fetch_company_snapshot(ticker: str) -> Dict[str, Any]:
    t = yf.Ticker(ticker)
    info = t.get_info() or {}
    fast = getattr(t, "fast_info", {}) or {}

    company_name = info.get("shortName") or info.get("longName") or ticker.upper()
    market_cap = _safe_float(info.get("marketCap") or fast.get("market_cap"))
    price = _safe_float(info.get("currentPrice") or fast.get("last_price") or info.get("regularMarketPrice"))

    held_insiders = _safe_float(info.get("heldPercentInsiders"))
    insiders_total_pct = None
    if held_insiders is not None:
        insiders_total_pct = held_insiders * 100 if held_insiders <= 1 else held_insiders

    float_shares = _safe_float(info.get("floatShares"))
    shares_out = _safe_float(info.get("sharesOutstanding"))

    free_float_pct = None
    if float_shares and shares_out:
        free_float_pct = (float_shares / shares_out) * 100
    elif insiders_total_pct is not None:
        free_float_pct = max(0.0, 100.0 - insiders_total_pct)

    # IPO dátum = prvý deň s dátami
    try:
        hist = t.history(period="max")
        ipo_date = hist.index.min().date() if not hist.empty else None
    except Exception:
        ipo_date = None

    days_to_lockup = None
    if ipo_date:
        lockup_end = ipo_date + timedelta(days=LOCKUP_DAYS_DEFAULT)
        today = date.today()
        d = (lockup_end - today).days
        # ak už lock-up skončil → None
        if d >= 0 and (today - ipo_date).days <= LOCKUP_DAYS_DEFAULT:
            days_to_lockup = d

    return {
        "ticker": ticker.upper(),
        "company_name": company_name,
        "price_usd": price,
        "market_cap_usd": market_cap,
        "free_float_pct": free_float_pct,
        "insiders_total_pct": insiders_total_pct,
        "ipo_first_trade_date": ipo_date,
        "days_to_lockup": days_to_lockup,
    }
