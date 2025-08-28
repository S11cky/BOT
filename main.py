# -*- coding: utf-8 -*-
"""
mapin.py – spúšťač IPO alertov a Pre-Lock-up SELL alertov do Telegramu.

Závislosti:
  - ipo_alerts.py (build_ipo_alert, build_pre_lockup_sell_alert, lockup_stage)
  - requests, python-dotenv (voliteľne, ak používaš .env)

Env premenné:
  TG_TOKEN      – Telegram bot token (od @BotFather)
  TG_CHAT_ID    – chat/skupina, kam sa majú posielať správy
  ALERT_ENABLE_IPO        – "1" / "0" (default 1)
  ALERT_ENABLE_PRELOCKUP  – "1" / "0" (default 1)
  LOCKUP_PING_DAYS        – CSV dni pred expir., default "30,14,7,0"

Použitie lokálne:
  python mapin.py
"""

import os
import sys
import requests
from typing import List, Tuple, Optional

try:
    from dotenv import load_dotenv  # ak nemáš, nevadí
    load_dotenv()
except Exception:
    pass

from ipo_alerts import (
    build_ipo_alert,
    build_pre_lockup_sell_alert,
    lockup_stage,
)

# ------------- Telegram odosielanie -------------

TG_TOKEN = os.getenv("TG_TOKEN", "").strip()
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "").strip()

def send_telegram(text: str) -> Optional[dict]:
    if not TG_TOKEN or not TG_CHAT_ID:
        print("[WARN] TG_TOKEN alebo TG_CHAT_ID chýba – neodosielam. Náhľad správy:")
        print("-" * 60)
        print(text)
        print("-" * 60)
        return None
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT_ID, "text": text, "disable_web_page_preview": True},
            timeout=20,
        )
        try:
            return r.json()
        except Exception:
            return {"status_code": r.status_code, "text": r.text[:200]}
    except Exception as e:
        print("[ERROR] Telegram send failed:", e)
        return None

# ------------- Demo/placeholder data -------------
# Tu si napojíš reálne dáta (IPO feedy, insider/lock-up zdroje…).
# Kým nemáš zdroje, nechávam dva ukážkové bloky, aby si overil doručovanie.

def demo_build_ipo_alert() -> str:
    """Postaví ukážkový IPO alert (optimistický)."""
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
    """Postaví ukážkový Pre-Lock-up SELL alert pre rôzne fázy (30/14/7/0)."""
    # tieto čísla sú ilustračné; adaptuj na reálne dáta:
    insider_pct = 48.0
    market_cap = 1_200_000_000
    release_pct = 22.0
    free_float_after_pct = 70.0

    # signály podľa fázy (iba príklad)
    signals = []
    if days_to_lockup <= 14:
        signals.append("Early VC Investors znížili podiel z 12 % → 8 % (–48M USD)")
        signals.append("Sekundárny predaj oznámený: ~60M USD akcií")
    else:
        signals.append("Monitoruj insider zmeny a secondary offering")

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

# ------------- Orchestrácia -------------

def main():
    enable_ipo = os.getenv("ALERT_ENABLE_IPO", "1") == "1"
    enable_pre = os.getenv("ALERT_ENABLE_PRELOCKUP", "1") == "1"

    # 1) IPO alert (napr. keď zistíš dokup veľkého hráča)
    if enable_ipo:
        ipo_msg = demo_build_ipo_alert()
        send_telegram(ipo_msg)

    # 2) Pre-lock-up alert – spúšťaj podľa dní do lock-upu
    #    nastav si v env LOCKUP_PING_DAYS="30,14,7,0" alebo inak
    ping_days_raw = os.getenv("LOCKUP_PING_DAYS", "30,14,7,0").strip()
    try:
        ping_days = [int(x) for x in ping_days_raw.split(",") if x.strip() != ""]
    except Exception:
        ping_days = [30, 14, 7, 0]

    # Tu iba DEMO: pošleme všetky 4 verzie naraz, aby si videl formát.
    # V produkcii pošli iba tú, ktorá práve zodpovedá skutočnému dňu.
    if enable_pre:
        for d in ping_days:
            pre_msg = demo_build_prelock_alert(d)
            send_telegram(pre_msg)

if __name__ == "__main__":
    sys.exit(main())
