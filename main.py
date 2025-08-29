# -*- coding: utf-8 -*-
"""
main.py – spúšťač IPO alertov + pre-lockup alertov (D-18) do Telegramu
- pravidelné IPO alerty (demo dáta, neskôr nahradíš reálnymi)
- pre-lockup SELL alert iba v deň, keď ostáva presne 18 dní
- throttle + dedupe, aby nechodili duplicity a spam

ENV:
  TG_TOKEN, TG_CHAT_ID
  ALERT_ENABLE_IPO="1|0"              (default 1)
  ALERT_ENABLE_PRELOCKUP="1|0"        (default 1)
  LOCKUP_PING_DAYS="18"               (default 18; môžeš dať CSV, napr. "18,7")
  ALERT_FREQ_MIN="10"                 (min. rozostup odosielania v minútach)
"""

import os
import sys
import json
import time
import pathlib
import hashlib
import requests
from typing import List, Tuple, Optional

# .env je voliteľný (lokálny test)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from ipo_alerts import (
    build_ipo_alert,
    build_pre_lockup_sell_alert,
)

# ------------------- Telegram -------------------

TG_TOKEN = os.getenv("TG_TOKEN", "").strip()
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "").strip()

def send_telegram(text: str):
    """Odošli text do Telegramu (alebo vypíš náhľad, ak chýba token/chat)."""
    if not TG_TOKEN or not TG_CHAT_ID:
        print("[WARN] TG_TOKEN alebo TG_CHAT_ID chýba – neodosielam. Náhľad:")
        print("=" * 60)
        print(text)
        print("=" * 60)
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

# ------------------- throttle + dedupe -------------------

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

ALERT_FREQ_MIN = int(os.getenv("ALERT_FREQ_MIN", "10"))

def send_unique(text: str):
    """Pošli správu iba ak neporušujeme throttle a nie je to duplicita."""
    st = _state_load()
    now = int(time.time())

    # throttle
    if now - st.get("last_sent_ts", 0) < ALERT_FREQ_MIN * 60:
        print("[SKIP] throttle – neposielam ešte (ALERT_FREQ_MIN).")
        return

    h = _msg_hash(text)
    if h in st.get("hashes", [])[-200:]:
        print("[SKIP] duplicate – rovnaký obsah už nedávno poslaný.")
        return

    send_telegram(text)
    st["last_sent_ts"] = now
    st.setdefault("hashes", []).append(h)
    st["hashes"] = st["hashes"][-500:]
    _state_save(st)

# ------------------- DEMO buildre (nahraď reálnymi dátami) -------------------

def demo_build_ipo_alert() -> str:
    """Ukážkový IPO alert – kým nemáš reálne dáta, overíš si doručenie."""
    return build_ipo_alert(
        investor="BlackRock",
        company="GreenFuture Energy",
        ticker="GFE",
        market_cap_usd=1_500_000_000,
        free_float_pct=82.0,
        holder_pct=6.8,
        price_usd=15.20,
        history=[
            ("14.50 USD", "3. máj 2024", None),
            ("14.90 USD", "15. jún 2024", "+2.8 %"),
            ("15.20 USD", "12. aug 2024", "+2.0 %"),
        ],
        avg_buy_price_usd=14.90,
        insiders_total_pct=12.0,
        insiders_breakdown=[
            ("Founders & Mgmt", 6.0),
            ("Early VC", 4.0),
            ("Board", 2.0),
        ],
        strategic_total_pct=18.8,
        buy_band=(15.0, 15.3),
        exit_band=(19.0, 21.0),
        optimal_exit=(20.0, 22.0),
        days_to_lockup=120,
        lockup_release_pct=6.0,
    )

def demo_build_prelock_alert(days_to_lockup: int) -> str:
    """Ukážkový pre-lockup SELL alert – bude poslaný iba v deň D-18."""
    insider_pct = 48.0
    market_cap = 1_200_000_000
    release_pct = 22.0
    free_float_after_pct = 70.0

    signals = [
        "Early VC Investors znížili podiel z 12 % → 8 % (–48M USD)",
        "Sekundárny predaj oznámený: ~60M USD akcií",
    ]
    hist_examples = [
        "Lyft (2019) – insiders 48 %, free float 42 % → –23 % po lock-upe",
        "Robinhood (2021) – insiders 52 %, free float 40 % → –18 % po lock-upe",
    ]

    return build_pre_lockup_sell_alert(
        company="GreenTech Energy",
        ticker="GTE",
        days_to_lockup=days_to_lockup,
        insider_pct=insider_pct,
        free_float_after_pct=free_float_after_pct,
        market_cap_usd=market_cap,
        signals=signals,
        release_pct=release_pct,
        exit_band=(12.50, 12.70),
        avg_buy_price_usd=12.35,
        hist_examples=hist_examples,
    )

# ------------------- Orchestrácia -------------------

def main():
    enable_ipo = os.getenv("ALERT_ENABLE_IPO", "1") == "1"
    enable_pre = os.getenv("ALERT_ENABLE_PRELOCKUP", "1") == "1"

    # 1) Pravidelný IPO alert (demo) – po nasadení nahradíš reálnym triggerom
    if enable_ipo:
        ipo_msg = demo_build_ipo_alert()
        send_unique(ipo_msg)

    # 2) Pre-lockup alert – iba keď ostáva presne 18 dní (default z LOCKUP_PING_DAYS)
    ping_days_raw = os.getenv("LOCKUP_PING_DAYS", "18").strip()
    try:
        ping_days = {int(x) for x in ping_days_raw.split(",") if x.strip() != ""}
    except Exception:
        ping_days = {18}

    if enable_pre:
        # keď nemáš reálne IPO dátumy, pošleme len DEMO pre D-18 ak je v sete
        if 18 in ping_days:
            pre_msg = demo_build_prelock_alert(18)
            send_unique(pre_msg)

    return 0

if __name__ == "__main__":
    sys.exit(main())
