"""Live mutual fund NAV data from the public mfapi.in API.

Fetches current NAV (net asset value) and recent NAV history for a curated set
of well-known Indian mutual funds, computes 1M/3M/6M/1Y returns, and ranks the
funds by their most recent 1-year performance so the app can suggest funds
based on the current market value.

This is educational information, not SEBI-registered financial advice.

Data source: https://api.mfapi.in (public, no API key required).
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta

import httpx

API_BASE = "https://api.mfapi.in/mf"
CACHE_TTL_SECONDS = 6 * 60 * 60  # refresh at most every 6 hours
DISCLAIMER = (
    "Based on live NAV data from mfapi.in. This is educational information, "
    "not SEBI-registered financial advice. Past performance does not guarantee "
    "future returns."
)

# Curated well-known Indian mutual funds (AMFI scheme codes verified via mfapi.in).
MUTUAL_FUNDS: list[dict] = [
    {"code": "120716", "name": "UTI Nifty 50 Index Fund - Direct - Growth", "category": "Large Cap"},
    {"code": "119063", "name": "HDFC Nifty 50 Index Fund - Direct Plan", "category": "Large Cap"},
    {"code": "119598", "name": "SBI Large Cap Fund (erstwhile Bluechip) - Direct - Growth", "category": "Large Cap"},
    {"code": "143341", "name": "UTI Nifty Next 50 Index Fund - Direct - Growth", "category": "Large & Mid Cap"},
    {"code": "118834", "name": "Mirae Asset Large & Midcap Fund - Direct - Growth", "category": "Large & Mid Cap"},
    {"code": "118955", "name": "HDFC Flexi Cap Fund - Direct - Growth", "category": "Flexi Cap"},
    {"code": "122639", "name": "Parag Parikh Flexi Cap Fund - Direct - Growth", "category": "Flexi Cap"},
    {"code": "120166", "name": "Kotak Flexicap Fund - Direct - Growth", "category": "Flexi Cap"},
    {"code": "118778", "name": "Nippon India Small Cap Fund - Direct - Growth", "category": "Small Cap"},
    {"code": "125497", "name": "SBI Small Cap Fund - Direct - Growth", "category": "Small Cap"},
    {"code": "119242", "name": "DSP ELSS Tax Saver Fund - Direct - Growth", "category": "ELSS"},
    {"code": "120592", "name": "ICICI Prudential ELSS Tax Saver Fund - Direct - Growth", "category": "ELSS"},
    {"code": "120377", "name": "ICICI Prudential Balanced Advantage Fund - Direct - Growth", "category": "Hybrid"},
    {"code": "118987", "name": "HDFC Corporate Bond Fund - Direct - Growth", "category": "Debt"},
]

# In-memory cache guarded by a lock.
_cache: dict[str, object] = {}
_cache_lock = threading.Lock()

PERIOD_DAYS = {
    "1m": 30.44,
    "3m": 91.32,
    "6m": 182.62,
    "1y": 365.25,
}


def _nav_history(code: str) -> tuple[list[dict], dict]:
    """Fetch {date, nav} history (newest-first) for a scheme code."""
    resp = httpx.get(f"{API_BASE}/{code}", timeout=15.0)
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("data", []), payload.get("meta", {})


def _nav_on_or_before(history: list[dict], target: datetime) -> float | None:
    for row in history:
        dt = datetime.strptime(row["date"], "%d-%m-%Y")
        if dt <= target:
            try:
                return float(row["nav"])
            except (TypeError, ValueError):
                return None
    return None


def fund_returns(code: str) -> dict | None:
    """Compute current NAV and 1M/3M/6M/1Y returns for one scheme."""
    try:
        history, meta = _nav_history(code)
    except Exception:
        return None
    if not history:
        return None
    try:
        latest_dt = datetime.strptime(history[0]["date"], "%d-%m-%Y")
        latest_nav = float(history[0]["nav"])
    except (TypeError, ValueError, KeyError):
        return None
    returns: dict[str, float | None] = {}
    for key, days in PERIOD_DAYS.items():
        old = _nav_on_or_before(history, latest_dt - timedelta(days=days))
        returns[key] = round((latest_nav / old - 1) * 100, 2) if old else None
    return {
        "name": meta.get("scheme_name", ""),
        "code": code,
        "nav": latest_nav,
        "nav_date": latest_dt.date().isoformat(),
        "returns": returns,
    }


def _rank_funds(funds: list[dict]) -> list[dict]:
    """Rank by 1y return (best available window), newest NAV first on ties."""
    def sort_key(f: dict):
        r = f.get("returns") or {}
        return (r.get("1y") if r.get("1y") is not None else -1e9), f.get("nav_date", "")
    return sorted(funds, key=sort_key, reverse=True)


def suggest_funds(limit: int = 6, category: str | None = None) -> dict:
    """Return top mutual funds by recent live performance for the current market.

    Uses a cached snapshot (refreshed at most every ``CACHE_TTL_SECONDS``). If the
    market data cannot be fetched, raises ``MarketDataUnavailable``.
    """
    now = time.time()
    with _cache_lock:
        cached = _cache.get("snapshot")
        if cached and now - cached["fetched_at"] < CACHE_TTL_SECONDS:
            snapshot = cached["snapshot"]
        else:
            funds: list[dict] = []
            for meta in MUTUAL_FUNDS:
                data = fund_returns(meta["code"])
                if data is None:
                    continue
                data["category"] = meta["category"]
                funds.append(data)
            if not funds:
                raise MarketDataUnavailable("Could not fetch live NAV data from mfapi.in.")
            snapshot = {
                "as_of": max(f["nav_date"] for f in funds),
                "funds": funds,
            }
            _cache["snapshot"] = {"snapshot": snapshot, "fetched_at": now}

    funds = snapshot["funds"]
    if category:
        category = category.strip().lower()
        funds = [f for f in funds if f["category"].lower() == category]
    ranked = _rank_funds(funds)[:limit]
    return {
        "source": "mfapi.in",
        "as_of": snapshot["as_of"],
        "funds": ranked,
        "disclaimer": DISCLAIMER,
    }


def market_text_summary(limit: int = 6) -> str:
    """Human-readable summary of the top funds for the AI chat."""
    try:
        data = suggest_funds(limit=limit)
    except MarketDataUnavailable:
        return "I could not fetch live market data right now. Please try again later."
    lines = [
        f"Based on the current market value (live NAV as of {data['as_of']} from mfapi.in), "
        f"here are {len(data['funds'])} mutual funds with the strongest recent performance:",
        "",
    ]
    for f in data["funds"]:
        ret = f["returns"]
        parts = []
        for label, key in (("1M", "1m"), ("3M", "3m"), ("6M", "6m"), ("1Y", "1y")):
            val = ret.get(key)
            parts.append(f"{label}: {val:+.2f}%" if val is not None else f"{label}: n/a")
        lines.append(
            f"- {f['name']} ({f['category']}) — NAV {f['nav']:.4f} on {f['nav_date']}: "
            + ", ".join(parts)
        )
    lines.append("")
    lines.append("Reasoning:")
    lines.append("- I fetched the live NAV and NAV history for each fund from mfapi.in.")
    lines.append("- Returns = (current NAV / NAV at the start of each window - 1) x 100.")
    lines.append("- Funds are ranked by their 1-year return, using the latest market value.")
    lines.append("")
    lines.append(data["disclaimer"])
    return "\n".join(lines)


class MarketDataUnavailable(Exception):
    """Raised when live market data cannot be fetched."""
