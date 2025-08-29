# -*- coding: utf-8 -*-
"""
ipo_alerts.py – šablóny pre IPO alerty
"""

from typing import List, Dict, Any, Tuple, Optional


def _fm_usd(x: float) -> str:
    if x is None:
        return "N/A USD"
    x = float(x)
    if x >= 1_000_000_000:
        return f"{x/1_000_000_000:.1f} mld. USD"
    if x >= 1_000_000:
        return f"{x/1_000_000:.1f} mil. USD"
    return f"{x:,.0f} USD".replace(",", " ")

def _pct(x: float, d: int = 1) -> str:
    if x is None:
        return "N/A %"
    return f"{float(x):.{d}f} %"

def _lockup_risk_icon(release_pct: float, insider_pct: float) -> str:
    if release_pct is None or insider_pct is None:
        return "⚪ neznáme riziko"
    if release_pct < 10 and insider_pct < 20:
        return "🟢 nízke riziko"
    if release_pct <= 25 or insider_pct <= 40:
        return "🟠 stredné riziko"
    return "🔴 vysoké riziko rug pull-u"

def filter_ipo_by_lockup(ipo_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter the IPO data to return only those companies with lock-up period ≤ 180 days.
    Includes companies where lock-up has already expired (None values).
    """
    filtered_data = [
        ipo for ipo in ipo_data 
        if ipo.get("days_to_lockup") is None or ipo.get("days_to_lockup", 0) <= 180
    ]
    print(f"Filtrácia IPO: {len(filtered_data)} IPO vyhovuje (vrátane expirovaných lock-upov)")
    return filtered_data

def build_ipo_alert(
    *,
    investor: str,
    company: str,
    ticker: str,
    market_cap_usd: float,
    free_float_pct: float,
    holder_pct: float,
    price_usd: float,
    history: List[Tuple[str, Optional[str], Optional[str]]],
    avg_buy_price_usd: Optional[float],
    insiders_total_pct: float,
    insiders_breakdown: List[Tuple[str, float]],
    strategic_total_pct: Optional[float] = None,
    buy_band: Optional[Tuple[float, float]] = None,
    exit_band: Optional[Tuple[float, float]] = None,
    optimal_exit: Optional[Tuple[float, float]] = None,
    days_to_lockup: Optional[int] = None,
    lockup_release_pct: Optional[float] = None,
) -> str:
    # Bezpečné výpočty pre None hodnoty
    ff_usd = market_cap_usd * (free_float_pct/100.0) if free_float_pct and market_cap_usd else None
    holder_usd = market_cap_usd * (holder_pct/100.0) if holder_pct and market_cap_usd else None
    insiders_total_usd = market_cap_usd * (insiders_total_pct/100.0) if insiders_total_pct and market_cap_usd else None
    
    strategic_total_pct = strategic_total_pct if strategic_total_pct is not None else (
        (insiders_total_pct + holder_pct) if insiders_total_pct and holder_pct else None
    )

    # história
    history_block = "   • (bez histórie)"
    if history:
        lines = []
        for price, date, delta in history:
            s = f"   • {price}"
            if date:  s += f" – {date}"
            if delta: s += f" ({delta})"
            lines.append(s)
        history_block = "\n".join(lines)

    # priemer
    avg_line = ""
    if avg_buy_price_usd and price_usd:
        diff_pct = (price_usd/avg_buy_price_usd - 1.0) * 100.0
        sign = "+" if diff_pct >= 0 else ""
        avg_line = f"\n📐 Priemer nákupov: {avg_buy_price_usd:.2f} USD | Aktuálna cena je {sign}{diff_pct:.1f} %"

    # insider breakdown
    insiders_block = ""
    if insiders_breakdown and market_cap_usd:
        insiders_block = "\n".join(
            f"   • {n} – {_pct(p,1)} (≈ {_fm_usd(market_cap_usd*(p/100.0))})"
            for n, p in insiders_breakdown
        )

    # lock-up
    lock_line = ""
    if days_to_lockup is not None and lockup_release_pct is not None and market_cap_usd:
        release_usd = market_cap_usd * (lockup_release_pct/100.0)
        risk_txt = _lockup_risk_icon(lockup_release_pct, insiders_total_pct)
        lock_status = f"{days_to_lockup} dní" if days_to_lockup >= 0 else "expiroval"
        lock_line = f"\n\n⏳ Lock-up: {lock_status} (uvolní sa ~{_pct(lockup_release_pct,0)} = ≈ {_fm_usd(release_usd)}) {risk_txt}"
    elif days_to_lockup is None:
        lock_line = f"\n\n⏳ Lock-up: expiroval ⚪"

    # pásma
    bands = []
    if buy_band: bands.append(f"📊 **NÁKUPNÉ PASMO: {buy_band[0]:.2f} – {buy_band[1]:.2f} USD**")
    if exit_band: bands.append(f"🎯 **EXIT PASMO: {exit_band[0]:.2f} – {exit_band[1]:.2f} USD**")
    if optimal_exit: bands.append(f"🚪 **OPTIMÁLNY EXIT: {optimal_exit[0]:.2f} – {optimal_exit[1]:.2f} USD**")
    bands_text = "\n".join(bands)

    return (
f"🔔 IPO Alert: {investor} dokúpil podiel v {company} ({ticker})\n\n"
f"🏢 Market cap: {_fm_usd(market_cap_usd)} | Free float: {_pct(free_float_pct,1)} (≈ {_fm_usd(ff_usd)})\n"
f"🏦 Celkový podiel ({investor}): {_pct(holder_pct,2)} (≈ {_fm_usd(holder_usd)})\n"
f"💲 Aktuálna cena: {price_usd:.2f} USD\n\n"
f"🔁 História dokúpení ({investor}):\n{history_block}"
f"{avg_line}\n\n"
f"👥 Insider ownership (spolu): {_pct(insiders_total_pct,0)} (≈ {_fm_usd(insiders_total_usd)}) 🟢 optimálne pásmo\n"
f"{insiders_block}\n\n"
f"🤝 Strategickí držitelia (Insider + {investor}): {_pct(strategic_total_pct,1)} (≈ {_fm_usd(market_cap_usd*(strategic_total_pct/100.0) if strategic_total_pct and market_cap_usd else None)})\n\n"
f"{bands_text}"
f"{lock_line}\n"
    ).strip()
