"""Sample seed data for local development and demo purposes."""
import random
from datetime import date, timedelta

from sqlmodel import Session, select

from app.auth.security import hash_password
from app.models.expense import Expense
from app.models.investment import Investment
from app.models.milk import MilkDelivery
from app.models.newspaper import NewspaperDelivery
from app.models.servant import Servant
from app.models.user import User

CATEGORIES = [
    "groceries", "utilities", "transport", "entertainment",
    "health", "medical", "education", "household", "dining", "shopping",
]

SERVANTS = [
    ("Lakshmi", "home cleaning", 3000.0),
    ("Ravi", "utensil cleaning", 1500.0),
    ("Arjun", "car cleaning", 800.0),
    ("Meena", "cook", 5000.0),
]

NEWSPAPERS = [
    ("The Times of India", 250.0),
    ("The Hindu", 300.0),
]

MILK_SUPPLIERS = ["Aavin Dairy", "Heritage Fresh", "Amul Parishad"]


def seed_users(session: Session) -> None:
    existing = session.exec(select(User)).first()
    if existing:
        return
    admin = User(
        username="admin",
        password_hash=hash_password("admin123"),
        role="admin",
    )
    demo = User(
        username="demo",
        password_hash=hash_password("demo123"),
        role="user",
    )
    session.add(admin)
    session.add(demo)


def seed_expenses(session: Session, months_back: int = 3) -> None:
    existing = session.exec(select(Expense)).first()
    if existing:
        return
    today = date.today()
    rng = random.Random(42)
    for back in range(months_back, -1, -1):
        month_start = today.replace(day=1) - timedelta(days=back * 31)
        # Generate between 8 and 14 expenses for that month
        num = rng.randint(8, 14)
        for _ in range(num):
            day = rng.randint(1, 28)
            cat = rng.choice(CATEGORIES)
            amount = round(rng.uniform(20, 800), 2)
            payment = rng.choice(["cash", "card", "upi"])
            session.add(
                Expense(
                    category=cat,
                    amount=amount,
                    date=month_start.replace(day=day),
                    notes=f"Sample {cat} expense",
                    payment_mode=payment,
                    tags=cat,
                )
            )
    # Guarantee a grocery-heavy current month for interesting insights
    current = today.replace(day=1)
    for _ in range(6):
        session.add(
            Expense(
                category="groceries",
                amount=round(rng.uniform(150, 500), 2),
                date=current + timedelta(days=rng.randint(0, today.day - 1)),
                notes="Weekly grocery run",
                payment_mode="upi",
                tags="groceries,weekly",
            )
        )
    # Guarantee a few medical expenses this month so the category is visible
    for day, amount, note, tag in [
        (2, 240.0, "Doctor consultation", "medical,doctor"),
        (9, 680.0, "Pharmacy - medicines", "medical,pharmacy"),
        (14, 1200.0, "Diagnostic lab tests", "medical,lab"),
    ]:
        session.add(
            Expense(
                category="medical",
                amount=amount,
                date=current.replace(day=min(day, today.day)),
                notes=note,
                payment_mode="card",
                tags=tag,
            )
        )


def seed_servants(session: Session) -> None:
    existing = session.exec(select(Servant)).first()
    if existing:
        return
    for name, role, salary in SERVANTS:
        session.add(
            Servant(
                name=name,
                role=role,
                monthly_salary=salary,
                payment_status="pending" if name != "Lakshmi" else "paid",
                attendance_count=26,
            )
        )


def seed_milk(session: Session) -> None:
    existing = session.exec(select(MilkDelivery)).first()
    if existing:
        return
    today = date.today()
    current_month = today.strftime("%Y-%m")
    missed_days = {2, 5, 11}
    for day in range(1, today.day + 1, 2):
        supplier = MILK_SUPPLIERS[day % len(MILK_SUPPLIERS)]
        session.add(
            MilkDelivery(
                supplier=supplier,
                quantity=1.5,
                rate=28.0,
                date=date(today.year, today.month, min(day, today.day)),
                month=current_month,
                is_delivered=day not in missed_days,
                payment_status="pending",
            )
        )


def seed_newspapers(session: Session) -> None:
    existing = session.exec(select(NewspaperDelivery)).first()
    if existing:
        return
    today = date.today()
    current_month = today.strftime("%Y-%m")
    last_day = 28
    missed_days = {2, 9, 17, 25}
    for name, cost in NEWSPAPERS:
        for day in range(1, last_day + 1):
            session.add(
                NewspaperDelivery(
                    name=name,
                    monthly_cost=cost,
                    date=date(today.year, today.month, min(day, last_day)),
                    month=current_month,
                    delivery_status=day not in missed_days,
                    payment_status="pending",
                )
            )


def seed_investments(session: Session) -> None:
    existing = session.exec(select(Investment)).first()
    if existing:
        return
    today = date.today()
    current_month = today.strftime("%Y-%m")
    sample = [
        ("HDFC Flexi Cap Fund - Direct", "equity_mf", 10000.0, 14, 12.0, "Monthly SIP - Direct growth plan"),
        ("SBI Bluechip Fund - Direct", "equity_mf", 5000.0, 7, 12.0, "SIP top-up"),
        ("PPF Account - Post Office", "ppf", 15000.0, 5, 7.1, "Annual contribution towards 80C"),
        ("NPS Tier 1 - HDFC Pension", "nps", 8000.0, 20, 9.0, "Monthly contribution (NPS 50)"),
        ("Nifty 50 Index Fund - UTI", "index_fund", 3000.0, 2, 11.0, "Index investing"),
        ("Axis Long Term Equity (ELSS)", "elss", 2000.0, 3, 12.0, "Tax saver ELSS"),
        ("Sukanya Samriddhi - Post Office", "ssy", 6000.0, 9, 8.2, "For daughter's future education"),
        ("Bank FD - SBI 444 days", "fd", 50000.0, 28, 6.7, "Emergency buffer FD"),
        ("SBI Magnum Gilt Fund", "debt_mf", 4000.0, 15, 7.0, "Gilt fund for stability"),
        ("HDFC Balanced Advantage", "hybrid_mf", 3500.0, 11, 9.0, "Hybrid fund"),
    ]
    for name, cat, amount, day, ret, notes in sample:
        session.add(
            Investment(
                scheme_name=name,
                category=cat,
                amount=amount,
                date=date(today.year, today.month, min(day, today.day)),
                month=current_month,
                expected_return=ret,
                notes=notes,
            )
        )


def run_seed(session: Session) -> None:
    seed_users(session)
    seed_expenses(session)
    seed_servants(session)
    seed_milk(session)
    seed_newspapers(session)
    seed_investments(session)
    session.commit()
