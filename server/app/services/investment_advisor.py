"""Investment advisor: curated catalog of Indian investment options and
a simple risk-based allocation strategy.

This is informational/educational guidance, not registered financial advice.
Rates are indicative (subject to change by the issuing institutions).
"""

from __future__ import annotations

from sqlmodel import Session, select

from app.models.investment import Investment
from app.utils.helpers import format_money

# Risk levels
LOW = "low"
MEDIUM = "medium"
HIGH = "high"

# Asset classes / buckets
GOVT = "government"
EQUITY = "equity"
DEBT = "debt"
GOLD = "gold"
BANK = "bank"


def investment_catalog() -> list[dict]:
    """Curated list of Indian investment options (government + market)."""
    return [
        {
            "key": "ppf",
            "name": "Public Provident Fund (PPF)",
            "category": "Government",
            "asset_class": GOVT,
            "risk": LOW,
            "expected_return": 7.1,
            "lock_in": "15 years (partial withdrawal from year 7)",
            "tax_benefit": "EEE — Section 80C up to ₹1.5L/year, tax-free interest & maturity",
            "description": "Safest long-term retirement savings backed by the Government of India.",
        },
        {
            "key": "nps",
            "name": "National Pension System (NPS)",
            "category": "Government",
            "asset_class": GOVT,
            "risk": MEDIUM,
            "expected_return": 9.0,
            "lock_in": "Until retirement (60), partial withdrawal allowed",
            "tax_benefit": "80CCD(1) ₹1.5L + 80CCD(1B) ₹50k extra",
            "description": "Market-linked pension scheme with a mix of equity, corporate and govt bonds.",
        },
        {
            "key": "ssy",
            "name": "Sukanya Samriddhi Yojana (SSY)",
            "category": "Government",
            "asset_class": GOVT,
            "risk": LOW,
            "expected_return": 8.2,
            "lock_in": "21 years / until the girl turns 18",
            "tax_benefit": "EEE — 80C up to ₹1.5L/year, tax-free",
            "description": "Scheme for a girl child under 10; among the highest tax-free govt returns.",
        },
        {
            "key": "scss",
            "name": "Senior Citizens Savings Scheme (SCSS)",
            "category": "Government",
            "asset_class": GOVT,
            "risk": LOW,
            "expected_return": 8.2,
            "lock_in": "5 years (extendable), for age 60+",
            "tax_benefit": "80C up to ₹1.5L/year; interest taxable",
            "description": "Quarterly interest income for senior citizens.",
        },
        {
            "key": "nsc",
            "name": "National Savings Certificate (NSC)",
            "category": "Government",
            "asset_class": GOVT,
            "risk": LOW,
            "expected_return": 7.7,
            "lock_in": "5 years",
            "tax_benefit": "80C eligible; interest taxable",
            "description": "Fixed-rate government savings certificate.",
        },
        {
            "key": "fd",
            "name": "Bank Fixed Deposit (FD)",
            "category": "Bank",
            "asset_class": BANK,
            "risk": LOW,
            "expected_return": 6.5,
            "lock_in": "Flexible (7 days to 10 years)",
            "tax_benefit": "No 80C benefit; interest taxable",
            "description": "Capital-protected deposit from banks/Post Office.",
        },
        {
            "key": "rd",
            "name": "Recurring Deposit (RD)",
            "category": "Bank",
            "asset_class": BANK,
            "risk": LOW,
            "expected_return": 6.5,
            "lock_in": "Typically 1-10 years",
            "tax_benefit": "No 80C benefit; interest taxable",
            "description": "Save a fixed amount every month; good habit builder.",
        },
        {
            "key": "sgb",
            "name": "Sovereign Gold Bond (SGB)",
            "category": "Government",
            "asset_class": GOLD,
            "risk": MEDIUM,
            "expected_return": 2.5,
            "lock_in": "8 years (redemption from 5th year)",
            "tax_benefit": "Capital gains at maturity are tax-free",
            "description": "Gold in paper form with an additional fixed interest of ~2.5%.",
        },
        {
            "key": "elss",
            "name": "ELSS Mutual Funds (tax saver)",
            "category": "Mutual Fund",
            "asset_class": EQUITY,
            "risk": HIGH,
            "expected_return": 12.0,
            "lock_in": "3 years (shortest among 80C options)",
            "tax_benefit": "80C up to ₹1.5L/year",
            "description": "Equity mutual funds with a 3-year lock-in and tax deduction.",
        },
        {
            "key": "equity_mf",
            "name": "Equity Mutual Funds",
            "category": "Mutual Fund",
            "asset_class": EQUITY,
            "risk": HIGH,
            "expected_return": 12.0,
            "lock_in": "None (SIP/lumpsum, exit load applies)",
            "tax_benefit": "LTCG over ₹1L taxed at 10%",
            "description": "Actively managed funds investing in company shares.",
        },
        {
            "key": "index_fund",
            "name": "Index Funds / ETFs (Nifty, Sensex)",
            "category": "Mutual Fund",
            "asset_class": EQUITY,
            "risk": HIGH,
            "expected_return": 11.0,
            "lock_in": "None",
            "tax_benefit": "LTCG over ₹1L taxed at 10%",
            "description": "Low-cost funds that track the Nifty 50 or Sensex.",
        },
        {
            "key": "debt_mf",
            "name": "Debt Mutual Funds",
            "category": "Mutual Fund",
            "asset_class": DEBT,
            "risk": MEDIUM,
            "expected_return": 7.0,
            "lock_in": "None (exit load applies)",
            "tax_benefit": "Gains taxed as per slab (indexation for 3+ years)",
            "description": "Bonds and money-market instruments; lower volatility than equity.",
        },
        {
            "key": "hybrid_mf",
            "name": "Hybrid / Balanced Mutual Funds",
            "category": "Mutual Fund",
            "asset_class": DEBT,
            "risk": MEDIUM,
            "expected_return": 9.0,
            "lock_in": "None",
            "tax_benefit": "Mixed taxation",
            "description": "A balanced mix of equity and debt managed by the fund house.",
        },
    ]


# Risk-profile → allocation percentages over asset classes (must sum to 100)
ALLOCATIONS: dict[str, dict[str, float]] = {
    "conservative": {GOVT: 55.0, BANK: 20.0, DEBT: 15.0, GOLD: 5.0, EQUITY: 5.0},
    "moderate": {GOVT: 40.0, BANK: 15.0, DEBT: 10.0, GOLD: 5.0, EQUITY: 30.0},
    "aggressive": {GOVT: 25.0, BANK: 10.0, DEBT: 5.0, GOLD: 5.0, EQUITY: 55.0},
}

RISK_LABELS = {"low": "Low risk", "medium": "Medium risk", "high": "High risk"}

PROFILE_DESCRIPTIONS = {
    "conservative": "Prioritises capital safety. Suited to short horizons (< 5 years) or those who cannot afford market swings.",
    "moderate": "Balances growth and safety with a majority in fixed income. Suited to 5-10 year horizons.",
    "aggressive": "Maximises long-term growth via equity. Suited to horizons above 10 years with higher tolerance for volatility.",
}


def risk_profiles() -> list[dict]:
    return [
        {"key": "conservative", "label": "Conservative"},
        {"key": "moderate", "label": "Moderate"},
        {"key": "aggressive", "label": "Aggressive"},
    ]


def build_allocation(amount: float, profile: str) -> dict:
    """Return a suggested asset-class allocation for a lump sum amount."""
    profile = (profile or "moderate").strip().lower()
    if profile not in ALLOCATIONS:
        profile = "moderate"
    alloc = ALLOCATIONS[profile]
    items = []
    for asset_class, pct in alloc.items():
        if pct <= 0:
            continue
        items.append(
            {
                "asset_class": asset_class,
                "label": asset_class.title(),
                "percent": pct,
                "amount": round(amount * pct / 100.0, 2),
            }
        )
    return {
        "profile": profile,
        "description": PROFILE_DESCRIPTIONS[profile],
        "total": round(amount, 2),
        "items": items,
    }


def suggested_schemes(allocation: dict, limit: int = 5) -> list[dict]:
    """Pick representative schemes for each asset class from the catalog."""
    asset_rank = {item["asset_class"]: item["percent"] for item in allocation["items"]}
    picked: dict[str, dict] = {}
    for opt in investment_catalog():
        if opt["asset_class"] not in asset_rank:
            continue
        if opt["asset_class"] not in picked:
            picked[opt["asset_class"]] = opt
    order = sorted(picked.values(), key=lambda o: asset_rank[o["asset_class"]], reverse=True)
    return order[:limit]


def portfolio_summary(session: Session) -> str:
    """Human-readable summary of the user's recorded investments."""
    rows = session.exec(select(Investment)).all()
    if not rows:
        return "You have not recorded any investments yet."
    total = sum(r.amount for r in rows)
    by_cat: dict[str, float] = {}
    for r in rows:
        by_cat[r.category] = by_cat.get(r.category, 0.0) + r.amount
    top = ", ".join(f"{cat} ({format_money(v)})" for cat, v in sorted(by_cat.items(), key=lambda x: x[1], reverse=True)[:5])
    return (
        f"Total invested: {format_money(total)} across {len(rows)} records "
        f"(top holdings: {top})."
    )
