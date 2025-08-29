# -*- coding: utf-8 -*-
"""
data_sources.py – reálne dostupné zdroje:
- Yahoo Finance (yfinance): cena, market cap, free float, insider %, inštitucionálni držitelia
- IPO dátum: odvodený z 1. obchodného dňa v historických dátach (priemyselný štandard, ak chýba metadata)
Pozn.: Lock-up rátame na 180 dní od 1. obchodného dňa (estimate).
"""

from datetime import date, datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple, List
import math

import pandas as pd
import yfinance as yf

LOCKUP_DAYS_DEFAULT = 180

BIG_HOLDER_WHITELIST = [
    "BlackRock", "Vanguard", "Fidelity", "State Street", "Capital Group",
    "Berkshire", "Morgan Stanley", "Goldman Sachs", "JP Morgan", "Wellington",
    "T. Rowe", "Dimensional", "Invesco", "Schwab", "Northern Trust",
]

def _safe_float(v) -> Optional[float]:
    try:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        return float(v)
    except Exception:
        return None

def _pick_primary_holder(df: pd.DataFrame) -> Tuple[Optional[str], Optional[float]]:
    """Vyber najrelevantnejšieho veľkého držiteľa z institutional_holders DF."""
    if df is None or df.empty:
        return None, None

    # normalizuj názvy stĺpcov
    cols = {c.lower(): c for c in df.columns}
    # percento môže byť v '% Out' alebo 'Pct Held' alebo 'Weight'
    pct_col = None
    for cand in ['% out', 'pct held', 'weight', 'pct_held', '%out']:
        if cand in cols:
            pct_col = cols[cand]
            break

    name_col = None
    for cand in ['holder', 'name']:
        if cand in cols:
            name_col = cols[cand]
            break
    if name_col is None:
        return None, None

    df2 = df.copy()
    if pct_col:
        # ak je v 0–1, premeň na %
        s = df2[pct_col].astype(float)
        if s.max() <= 1.0:
            df2['_pct'] = s * 100.0
        else:
            df2['_pct'] = s
    else:
        # ak percentá nemáme, odhad podľa Value
        val_col = None
        for cand in ['value', 'value ($)', 'value usd']:
            if cand in cols:
                val_col = cols[cand]
                break
        if val_col is None:
            # fallback: podľa počtu akcií
            shares_col = None
            for cand in ['shares', 'shares held']:
                if cand in cols:
                    shares_col = cols[cand]
                    break
            if shares_col is None:
                # zober prvý riadok
                row = df2.iloc[0]
                return str(row[name_col]), None
            df2['_score'] = df2[shares_col].astype(float)
        else:
            df2['_score'] = df2[val_col].astype(float)

    # preferuj whitelist
    def is_whitelisted(nm: str) -> bool:
        low = (nm or "").lower()
        return any(w.lower() in low for w in BIG_HOLDER_WHITELIST)

    if '_pct' in df2.columns:
        df2 = df2.sort_values('_pct', ascending=False)
    else:
        df2 = df2.sort_values('_score', ascending=False)

    for _, row in df2.iterrows():
        nm = str(row[name_col])
        if is_whitelisted(nm):
            pct = _safe_float(row.get('_pct'))
            return nm, pct
    # ak nič z whitelistu, vezmi top 1
    row = df2.iloc[0]
    return str(row[name_col]), _safe_float(row.get('_pct'))

def fetch_company_snapshot(ticker: str) -> Dict[str, Any]:
    """
    Vráti dict so základom pre alert:
      - company_name, price_usd, market_cap_usd
      - free_float_pct, insiders_total_pct
      - institutional_holders_df (pandas DF alebo None)
      - primary_holder_name, primary_holder_pct
      - ipo_first_trade_date, days_to_lockup (≈ 180 dní)
    """
    t = yf.Ticker(ticker)
    info = t.get_info()  # môže byť pomalšie, ale dá viac polí
    fast = getattr(t, "fast_info", {}) or {}

    company_name = info.get("shortName") or info.get("longName") or ticker.upper()
    market_cap = _safe_float(info.get("marketCap") or fast.get("market_cap"))
    price = _safe_float(info.get("currentPrice") or fast.get("last_price") or info.get("regularMarketPrice"))

    held_insiders = _safe_float(info.get("heldPercentInsiders"))
    if held_insiders is not None and held_insiders <= 1.0:
        insiders_total_pct = held_insiders * 100.0
    else:
        insiders_total_pct = held_insiders  # už v %

    float_shares = _safe_float(info.get("floatShares"))
    shares_out = _safe_float(info.get("sharesOutstanding"))

    if float_shares and shares_out:
        free_float_pct = (float_shares / shares_out) * 100.0
    else:
        # fallback: ak máme insider %
        free_float_pct = None
        if insiders_total_pct is not None:
            free_float_pct = max(0.0, 100.0 - insiders_total_pct)

    # institucionalni držitelia (môže None)
    try:
        inst_df = t.institutional_holders
    except Exception:
        inst_df = None

    primary_name, primary_pct = _pick_primary_holder(inst_df)

    # IPO dátum ~ prvý obchodný deň
    try:
        hist = t.history(period="max", auto_adjust=False)  # DataFrame s dátumovým indexom
        first_day = hist.index.min().date() if not hist.empty else None
    except Exception:
        first_day = None

    ipo_date = first_day  # ak nevieme, ostane None
    days_to_lockup = None
    if ipo_date:
        lockup_end = ipo_date + timedelta(days=LOCKUP_DAYS_DEFAULT)
        today = date.today()
        days_to_lockup = (lockup_end - today).days

    return {
        "ticker": ticker.upper(),
        "company_name": company_name,
        "price_usd": price,
        "market_cap_usd": market_cap,
        "free_float_pct": free_float_pct,
        "insiders_total_pct": insiders_total_pct,
        "institutional_holders_df": inst_df,
        "primary_holder_name": primary_name,
        "primary_holder_pct": primary_pct,  # v %
        "ipo_first_trade_date": ipo_date,
        "days_to_lockup": days_to_lockup,
    }
