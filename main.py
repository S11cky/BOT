# -*- coding: utf-8 -*-
"""
main.py – reálne zdroje (Yahoo Finance) + tvoje alert šablóny
- IPO alert: využíva skutočný market cap, cenu, free float, insider %
- Pre-lockup SELL alert: pošle sa IBA, ak days_to_lockup == 18 (default)
- throttle + dedupe, aby nespadol spam
"""

import os
import sys
import json
import time
import pathlib
import hashlib
from typing import Optional, List, Tuple

import requests
from dotenv import load_dotenv

from data_sources import fetch_company_snapshot
from ipo_alerts import build_ipo_alert, build_pre_lockup_sell_alert

load_dotenv()

# ------------ Telegram ------------
TG_TOKEN = os.getenv("TG_TOKEN", "").strip()
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "").strip()

def send_telegram(text: str):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("[WARN] TG_TOKEN/TG_CHAT_ID chýba – náhľad správy:\n", text)
        return None
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT_ID, "text": text, "disable_web_page_preview": True},
            timeout=20,
        )
        return r.json()
    except Exception as e:
        print("[ERROR] Telegram send failed:", e)
        return None

# ------------ throttle + dedupe ------------
STATE_PATH = pathlib.Path(".state/ipo_state.json")
STATE_PATH.parent.mkdir(exist_ok=True, parents=True)

def _state_load():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    return {"last_sent_ts": 0, "hashes": []}

def _state_save(s): STATE_PATH.write_text(json.dumps(s))
def _msg_hash(s: str) -> str: return hashlib.sha256(s.encode("utf-8")).hexdigest()

ALERT_FREQ_MIN = int(os.getenv("ALERT_FREQ_MIN", "10"))  # min. rozostup medzi správami (min)

def send_unique(text: str):
    st = _state_load()
    now = int(time.time())
    if now - st.get("last_sent_ts", 0) < ALERT_FREQ_MIN * 60:
        print("[SKIP] throttle – čakám na ďalšie okno.")
        return
    h = _msg_hash(text)
    if h in st.get("hashes", [])[-200:]:
        print("[SKIP] duplicate – rovnaký obsah už poslaný.")
        return
    send_telegram(text)
    st["last_sent_ts"] = now
    st.setdefault("hashes", []).append(h)
    st["hashes"] = st["hashes"][-500:]
    _state_save(st)

# ------------ pomocné výpočty pásiem ------------

def compute_bands(price: Optional[float]) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
    """Jednoduché pásma: BUY ±(–2%..+1%), EXIT +(25..40)%, OPT +(35..50)%."""
    if not price:
        price = 10.0
    buy = (round(price*0.98, 2), round(price*1.01, 2))
    exitb = (round(price*1.25, 2), round(price*1.40, 2))
    opt = (round(price*1.35, 2), round(price*1.50, 2))
    return buy, exitb, opt

# ------------ hlavná logika ------------

def run_for_ticker(ticker: str, only_prelock_d18: bool = False):
    snap = fetch_company_snapshot(ticker)

    # základné metriky
    name = snap["company_name"]
    price = snap["price_usd"]
    mc = snap["market_cap_usd"]
    ff_pct = snap["free_float_pct"]
    insiders_pct = snap["insiders_total_pct"]
    days_to_lockup = snap["days_to_lockup"]  # môže byť None

    # držiteľ (skutočný z YF institutional_holders)
    investor = snap["primary_holder_name"] or "Top holder"
    holder_pct = snap["primary_holder_pct"]  # môže byť None

    # pásma
    buy_band, exit_band, opt_exit = compute_bands(price)

    # INSIDER breakdown – bez detailu (YF detail často chýba), nechajme prázdne:
    insiders_breakdown = []  # ak chceš, doplň sem heuristiku

    # IPO alert (ak nechceš – vypni cez env)
    if not only_prelock_d18:
        ipo_msg = build_ipo_alert(
            investor=investor,
            company=name,
            ticker=ticker.upper(),
            market_cap_usd=mc or 0.0,
            free_float_pct=ff_pct or max(0.0, 100.0 - (insiders_pct or 0.0)),
            holder_pct=holder_pct or 0.0,
            price_usd=price or 0.0,
            history=[],                     # reálne histórie dokupov nemáme vo free zdroji
            avg_buy_price_usd=None,         # nemáme priemer nákupov veľkého hráča
            insiders_total_pct=insiders_pct or 0.0,
            insiders_breakdown=insiders_breakdown,
            strategic_total_pct=(insiders_pct or 0.0) + (holder_pct or 0.0),
            buy_band=buy_band,
            exit_band=exit_band,
            optimal_exit=opt_exit,
            days_to_lockup=days_to_lockup if days_to_lockup is not None else 9999,
            lockup_release_pct=(insiders_pct or 0.0),   # hrubý odhad: insider % ~ potenciálne uvoľniteľné
        )
        send_unique(ipo_msg)

    # Pre-lockup SELL alert iba pri D-18
    ping_days_raw = os.getenv("LOCKUP_PING_DAYS", "18").strip()
    try:
        ping_days = {int(x) for x in ping_days_raw.split(",") if x.strip()}
    except Exception:
        ping_days = {18}

    if days_to_lockup is not None and days_to_lockup in ping_days:
        # odhad: free float po lock-upe ~ terajší free float + insider %
        ff_after = None
        if ff_pct is not None and insiders_pct is not None:
            ff_after = min(100.0, ff_pct + insiders_pct)
        else:
            ff_after = ff_pct or 0.0

        signals: List[str] = []
        if (insiders_pct or 0) >= 40:
            signals.append("Vysoký insider podiel ≥ 40 % (riziko predajného tlaku)")
        if holder_pct and holder_pct >= 5.0:
            signals.append(f"Veľký držiteľ {investor} drží ≈ {holder_pct:.1f} % – sleduj potenciálne pohyby")
        if not signals:
            signals.append("Blíži sa lock-up – sleduj objemy a insider zmeny")

        pre_msg = build_pre_lockup_sell_alert(
            company=name, ticker=ticker.upper(),
            days_to_lockup=days_to_lockup,
            insider_pct=insiders_pct or 0.0,
            free_float_after_pct=ff_after,
            market_cap_usd=mc or 0.0,
            signals=signals,
            release_pct=(insiders_pct or 0.0),         # hrubý odhad
            exit_band=(round((price or 0.0)*0.98, 2), round((price or 0.0)*1.02, 2)),
            avg_buy_price_usd=None,
            hist_examples=[
                "Lyft (2019) – insiders ~48 %, free float ~42 % → –23 % po lock-upe",
                "Robinhood (2021) – insiders ~52 %, free float ~40 % → –18 % po lock-upe",
            ],
        )
        send_unique(pre_msg)

def main():
    # Zoznam tickerov z env (CSV), napr.: WATCH_TICKERS="ABCD,EFGH"
    tickers_csv = os.getenv("WATCH_TICKERS", "GTLB,ABNB,PLTR").strip()
    tickers = [t.strip().upper() for t in tickers_csv.split(",") if t.strip()]

    enable_ipo = os.getenv("ALERT_ENABLE_IPO", "1") == "1"
    enable_pre = os.getenv("ALERT_ENABLE_PRELOCKUP", "1") == "1"

    only_prelock_d18 = (enable_ipo is False and enable_pre is True)

    for t in tickers:
        try:
            run_for_ticker(t, only_prelock_d18=only_prelock_d18)
        except Exception as e:
            print(f"[ERROR] {t} zlyhal: {e}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
