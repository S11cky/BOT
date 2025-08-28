# -*- coding: utf-8 -*-
"""
ipo_alerts.py – šablóny a pomocné funkcie pre IPO alerty do Telegramu.
Poskytuje:
  - build_ipo_alert(...)
  - build_pre_lockup_sell_alert(...)
  - lockup_stage(days_to_lockup)
"""

from typing import List, Tuple, Optional

# ---------- Pomocné formátovače ----------

def _fm_usd(x: float) -> str:
    x = float(x or 0)
    if x >= 1_000_000_000:
        return f"{x/1_000_000_000:.1f} mld. USD"
    if x >= 1_000_000:
        return f"{x/1_000_000:.1f} mil. USD"
    return f"{x:,.0f} USD".replace(",", " ")

def _pct(x: float, d: int = 1) -> str:
    return f"{float(x):.{d}f} %"

def _lockup_risk_icon(release_pct: float, insider_pct: float) -> str:
    # <10% & insider<20% → 🟢, inak 10–25% alebo insider≤40% → 🟠, inak 🔴
    if release_pct < 10 and insider_pct < 20:
        return "🟢 nízke riziko"
    if release_pct <= 25 or insider_pct <= 40:
        return "🟠 stredné riziko"
    return "🔴 vysoké riziko rug pull-u"

def lockup_stage(days_to_lockup: int) -> Tuple[str, str]:
    """Vracia (emoji, label) podľa dňa do lock-upu."""
    if days_to_lockup > 21:
        return "📣", "INFO"
    if days_to_lockup > 10:
        return "⚠️", "SELL"
    if days_to_lockup > 0:
        return "🚨", "URGENT"
    return "🔴", "LOCK-UP"

# ---------- IPO ALERT (vstupy/dokupy) ----------

def build_ipo_alert(
    *,
    investor: str,
    company: str,
    ticker: str,
    market_cap_usd: float,
    free_float_pct: float,
    holder_pct: float,              # celkový podiel investora v %
    price_usd: float,
    history: List[Tuple[str, Optional[str], Optional[str]]],  # [(cena, dátum, delta_text)]
    avg_buy_price_usd: Optional[float],
    insiders_total_pct: float,
    insiders_breakdown: List[Tuple[str, float]],  # [(meno, %)]
    strategic_total_pct: Optional[float] = None,  # insider + investor
    buy_band: Optional[Tuple[float, float]] = None,
    exit_band: Optional[Tuple[float, float]] = None,
    optimal_exit: Optional[Tuple[float, float]] = None,
    days_to_lockup: Optional[int] = None,
    lockup_release_pct: Optional[float] = None,   # % akcií, ktoré sa uvoľnia po lock-upe
) -> str:
    ff_usd = market_cap_usd * (free_float_pct/100.0)
    holder_usd = market_cap_usd * (holder_pct/100.0)
    insiders_total_usd = market_cap_usd * (insiders_total_pct/100.0)
    strategic_total_pct = strategic_total_pct if strategic_total_pct is not None else (insiders_total_pct + holder_pct)

    # História
    if history:
        lines = []
        for price, date, delta in history:
            s = f"   • {price}"
            if date:  s += f" – {date}"
            if delta: s += f" ({delta})"
            lines.append(s)
        history_block = "\n".join(lines)
    else:
        history_block = "   • (bez histórie)"

    # Priemer nákupov vs. aktuálna cena
    avg_line = ""
    if avg_buy_price_usd:
        diff_pct = (price_usd/avg_buy_price_usd - 1.0) * 100.0
        sign = "+" if diff_pct >= 0 else ""
        avg_line = f"\n📐 Priemer nákupov: {avg_buy_price_usd:.2f} USD | Aktuálna cena je {sign}{diff_pct:.1f} %"

    # Insider breakdown
    insiders_lines = []
    for name, pct in (insiders_breakdown or []):
        insiders_lines.append(f"   • {name} – {_pct(pct,1)}  (≈ {_fm_usd(market_cap_usd*(pct/100.0))})")
    insiders_block = "\n".join(insiders_lines) if insiders_lines else ""

    # Lock-up
    lock_line = ""
    if days_to_lockup is not None and lockup_release_pct is not None:
        release_usd = market_cap_usd * (lockup_release_pct/100.0)
        risk_txt = _lockup_risk_icon(lockup_release_pct, insiders_total_pct)
        lock_line = f"\n\n⏳ Lock-up: {days_to_lockup} dní (uvolní sa ~{_pct(lockup_release_pct,0)} = ≈ {_fm_usd(release_usd)}) {risk_txt}"

    # Pásma
    bands = []
    if buy_band: bands.append(f"📊 **NÁKUPNÉ PASMO: {buy_band[0]:.2f} – {buy_band[1]:.2f} USD**")
    if exit_band: bands.append(f"🎯 **EXIT PASMO: {exit_band[0]:.2f} – {exit_band[1]:.2f} USD**")
    if optimal_exit: bands.append(f"🚪 **OPTIMÁLNY EXIT: {optimal_exit[0]:.2f} – {optimal_exit[1]:.2f} USD**")
    bands_text = "\n".join(bands)

    msg = (
f"🔔 IPO Alert: {investor} dokúpil podiel v {company} ({ticker})\n\n"
f"🏢 Market cap: {_fm_usd(market_cap_usd)} | Free float: {_pct(free_float_pct,1)}  (≈ {_fm_usd(ff_usd)})\n"
f"🏦 Celkový podiel ({investor}): {_pct(holder_pct,2)}  (≈ {_fm_usd(holder_usd)})\n"
f"💲 Aktuálna cena: {price_usd:.2f} USD\n\n"
f"🔁 História dokúpení ({investor}):\n{history_block}"
f"{avg_line}\n\n"
f"👥 Insider ownership (spolu): {_pct(insiders_total_pct,0)}  (≈ {_fm_usd(insiders_total_usd)}) 🟢 optimálne pásmo\n"
f"{insiders_block}\n\n"
f"🤝 Strategickí držitelia (Insider + {investor}): {_pct(strategic_total_pct,1)}  (≈ {_fm_usd(market_cap_usd*(strategic_total_pct/100.0))})\n\n"
f"{bands_text}"
f"{lock_line}\n"
    )
    return msg.strip()

# ---------- PRE-LOCK-UP SELL ALERT (exity/ochrana) ----------

def build_pre_lockup_sell_alert(
    *,
    company: str,
    ticker: str,
    days_to_lockup: int,
    insider_pct: float,
    free_float_after_pct: float,
    market_cap_usd: float,
    signals: List[str],                    # každá veta v zozname bude vlastný odrážkový riadok
    release_pct: float,                    # % akcií uvoľnených pri lock-upe (alebo ekvivalent)
    exit_band: Tuple[float, float],
    avg_buy_price_usd: Optional[float] = None,
    hist_examples: Optional[List[str]] = None  # napr. ["Lyft (2019)…", "Robinhood (2021)…"]
) -> str:
    icon, stage = lockup_stage(days_to_lockup)
    exit_lo, exit_hi = exit_band

    # Nákup vs. Exit (oproti priemeru)
    diff_line = ""
    if avg_buy_price_usd:
        lo_diff = (exit_lo/avg_buy_price_usd - 1.0)*100.0
        hi_diff = (exit_hi/avg_buy_price_usd - 1.0)*100.0
        diff_line = f"\n📊 Nákup vs. Exit: {lo_diff:+.1f} % až {hi_diff:+.1f} % oproti priemeru ({avg_buy_price_usd:.2f} USD)"

    release_usd = market_cap_usd * (release_pct/100.0)
    signals_block = "\n".join([f"   • {s}" for s in (signals or [])]) or "   • (bez rizikových signálov)"
    hist_block = ""
    if hist_examples:
        hist_block = "\n" + "\n".join([f"   • {h}" for h in hist_examples])

    risk_txt = _lockup_risk_icon(release_pct, insider_pct)
    msg = (
f"{icon} PRE-LOCK-UP SELL ALERT: {company} ({ticker})\n\n"
f"⏳ Lock-up: {days_to_lockup} dní do expirácie\n"
f"👥 Insider ownership: {_pct(insider_pct,0)} (≈ {_fm_usd(market_cap_usd*(insider_pct/100.0))})\n"
f"🪙 Free float po expiracii: ~{_pct(free_float_after_pct,0)}  (≈ {_fm_usd(market_cap_usd*(free_float_after_pct/100.0))})\n\n"
f"📉 Rizikové signály:\n{signals_block}\n\n"
f"💰 Uvoľní sa ~{_pct(release_pct,0)} akcií = ≈ {_fm_usd(release_usd)}  → {risk_txt}\n"
f"{hist_block}\n\n"
f"💲 Exitná cena (odporúčanie): {exit_lo:.2f} – {exit_hi:.2f} USD"
f"{diff_line}\n\n"
f"👉 Odporúčanie: zvážiť exit alebo hedging pred lock-upom"
    )
    return msg.strip()
